#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recherche dans Noethys des familles de défauts révélées par Teamworks.

L'objectif n'est pas de copier les correctifs Teamworks, mais de transformer
chaque classe de défaut reproductible en signature AST réutilisable. Les
signatures de ce premier lot sont volontairement à forte confiance :

- compréhension exécutée dans un corps de classe qui lit un nom défini plus
  haut dans cette même classe depuis la portée interne de la compréhension ;
- accesseur wx/contrôle testé ou comparé comme objet méthode au lieu d'être
  appelé ;
- ancien appel ``Thread.isAlive()`` retiré du runtime Python moderne.

La lecture/parsing passe obligatoirement par ``SourceAuditSession`` : un fichier
qui échappe à l'analyse invalide la couverture et produit un code de sortie 2.
Les occurrences restent un inventaire tant qu'elles n'ont pas été qualifiées.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_source_coverage import SourceAuditSession, iter_python_files  # noqa: E402

NOETHYS = ROOT / "noethys"
EXCLUDED_PARTS = {"ObjectListView", "Outils"}
ACCESSOR_METHODS = {
    "GetValue",
    "GetSelection",
    "GetStringSelection",
    "GetLabel",
    "GetPath",
    "GetFilename",
}


def iter_application_files(root: Path = NOETHYS):
    root = Path(root)
    for path in iter_python_files(root):
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        yield path


def _target_names(target: ast.AST) -> set[str]:
    names = set()
    for node in ast.walk(target):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            names.add(node.id)
    return names


def _statement_definitions(statement: ast.stmt) -> set[str]:
    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {statement.name}
    if isinstance(statement, ast.Assign):
        result = set()
        for target in statement.targets:
            result.update(_target_names(target))
        return result
    if isinstance(statement, ast.AnnAssign):
        return _target_names(statement.target)
    if isinstance(statement, ast.AugAssign):
        return _target_names(statement.target)
    if isinstance(statement, (ast.Import, ast.ImportFrom)):
        return {alias.asname or alias.name.split(".")[0] for alias in statement.names}
    return set()


class _ComprehensionsInClassStatement(ast.NodeVisitor):
    """Visite les expressions d'un statement de classe sans entrer dans un scope imbriqué."""

    def __init__(self):
        self.nodes = []

    def visit_ListComp(self, node):
        self.nodes.append(node)
        self.generic_visit(node)

    def visit_SetComp(self, node):
        self.nodes.append(node)
        self.generic_visit(node)

    def visit_DictComp(self, node):
        self.nodes.append(node)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node):
        self.nodes.append(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        return

    def visit_AsyncFunctionDef(self, node):
        return

    def visit_Lambda(self, node):
        return

    def visit_ClassDef(self, node):
        return


def _loaded_names(node: ast.AST) -> set[str]:
    return {
        child.id
        for child in ast.walk(node)
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
    }


def _comprehension_inner_loads(node: ast.AST) -> set[str]:
    """Noms non liés lus dans la portée interne d'une compréhension Python 3.

    L'itérable du premier générateur est évalué dans la portée englobante. Une
    fois entré dans la portée implicite de la compréhension, chaque cible de
    générateur masque un éventuel nom homonyme défini dans le corps de classe.
    On respecte cet ordre de liaison pour éviter de prendre une variable locale
    de compréhension pour un accès impossible au namespace de classe.
    """
    generators = list(node.generators)
    bound = set()
    result = set()

    for index, generator in enumerate(generators):
        if index > 0:
            result.update(_loaded_names(generator.iter) - bound)

        bound.update(_target_names(generator.target))
        for condition in generator.ifs:
            result.update(_loaded_names(condition) - bound)

    if isinstance(node, ast.DictComp):
        payload = [node.key, node.value]
    else:
        payload = [node.elt]

    for part in payload:
        result.update(_loaded_names(part) - bound)
    return result


def _scan_class_comprehensions(tree: ast.AST, relpath: str) -> list[dict]:
    findings = []
    for class_node in (node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)):
        defined = set()
        for statement in class_node.body:
            visitor = _ComprehensionsInClassStatement()
            visitor.visit(statement)
            for comprehension in visitor.nodes:
                trapped = sorted(defined & _comprehension_inner_loads(comprehension))
                for name in trapped:
                    findings.append(
                        {
                            "kind": "class_comprehension_scope",
                            "priority": "high",
                            "file": relpath,
                            "line": comprehension.lineno,
                            "class": class_node.name,
                            "name": name,
                            "detail": "nom de classe lu depuis la portée interne d'une compréhension Python 3",
                        }
                    )
            defined.update(_statement_definitions(statement))
    return findings


def _accessor_attribute(expr: ast.AST):
    if isinstance(expr, ast.Attribute) and expr.attr in ACCESSOR_METHODS:
        return expr
    return None


def _iter_boolean_operands(expr: ast.AST):
    if isinstance(expr, ast.BoolOp):
        for value in expr.values:
            yield from _iter_boolean_operands(value)
    elif isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
        yield expr.operand
    else:
        yield expr


def _scan_uninvoked_accessors(tree: ast.AST, relpath: str) -> list[dict]:
    findings = []
    seen = set()

    def add(node: ast.Attribute, context: str):
        key = (node.lineno, node.col_offset, node.attr, context)
        if key in seen:
            return
        seen.add(key)
        findings.append(
            {
                "kind": "accessor_not_called",
                "priority": "high",
                "file": relpath,
                "line": node.lineno,
                "accessor": node.attr,
                "detail": context,
            }
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for operand in [node.left, *node.comparators]:
                accessor = _accessor_attribute(operand)
                if accessor is not None:
                    add(accessor, "accesseur comparé sans appel")
        elif isinstance(node, (ast.If, ast.While, ast.Assert)):
            for operand in _iter_boolean_operands(node.test):
                accessor = _accessor_attribute(operand)
                if accessor is not None:
                    add(accessor, "accesseur utilisé comme booléen sans appel")
        elif isinstance(node, ast.IfExp):
            for operand in _iter_boolean_operands(node.test):
                accessor = _accessor_attribute(operand)
                if accessor is not None:
                    add(accessor, "accesseur utilisé comme condition sans appel")

    return findings


def _scan_is_alive(tree: ast.AST, relpath: str) -> list[dict]:
    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "isAlive":
            continue
        findings.append(
            {
                "kind": "thread_isAlive",
                "priority": "high",
                "file": relpath,
                "line": node.lineno,
                "detail": "API Thread.isAlive() obsolète ; utiliser is_alive()",
            }
        )
    return findings


def scan_tree(tree: ast.AST, relpath: str = "<memory>") -> list[dict]:
    findings = []
    findings.extend(_scan_class_comprehensions(tree, relpath))
    findings.extend(_scan_uninvoked_accessors(tree, relpath))
    findings.extend(_scan_is_alive(tree, relpath))
    findings.sort(key=lambda item: (item["file"], item["line"], item["kind"]))
    return findings


def build_report(root: Path = NOETHYS) -> dict:
    root = Path(root)
    session = SourceAuditSession(iter_application_files(root))
    findings = []

    for path in session.paths:
        loaded = session.parse(path)
        if loaded is None:
            continue
        _source, tree = loaded
        relpath = path.relative_to(root).as_posix()
        findings.extend(scan_tree(tree, relpath))

    findings.sort(key=lambda item: (item["priority"] != "high", item["kind"], item["file"], item["line"]))
    return {
        "coverage": {
            "found": session.coverage.found,
            "read": session.coverage.read,
            "parsed": session.coverage.parsed,
            "complete": session.coverage.complete,
            "failures": [failure.format() for failure in session.coverage.failures],
        },
        "count": len(findings),
        "kinds": dict(Counter(item["kind"] for item in findings)),
        "priorities": dict(Counter(item["priority"] for item in findings)),
        "findings": findings,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=NOETHYS)
    parser.add_argument("--json", default="", metavar="FILE")
    parser.add_argument("--fail-on-high", action="store_true")
    args = parser.parse_args(argv)

    report = build_report(args.root)
    coverage = report["coverage"]
    print(
        "TEAMWORKS_SIGNATURES=%d — %s — couverture %d/%d/%d"
        % (
            report["count"],
            report["kinds"],
            coverage["found"],
            coverage["read"],
            coverage["parsed"],
        )
    )
    for item in report["findings"]:
        print("- {priority} {kind} {file}:{line} — {detail}".format(**item))
    for failure in coverage["failures"]:
        print("ERREUR AUDIT: %s" % failure)

    if args.json:
        output = Path(args.json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if not coverage["complete"]:
        return 2
    if args.fail_on_high and report["priorities"].get("high", 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
