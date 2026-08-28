#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Détecte les variables locales potentiellement non définies après un ``if``.

Le contrôle est volontairement conservateur : il ne signale qu'une affectation
présente dans une seule branche, sans définition antérieure visible, lorsque le
premier usage ultérieur de ce nom est une lecture. Les résultats restent des
candidats à qualifier humainement. La couverture des sources est bloquante.

La propagation des définitions suit les chemins qui peuvent réellement
continuer après un branchement. Une chaîne exhaustive ``if/elif/else`` qui
définit un nom dans toutes ses branches rend donc ce nom disponible ensuite,
y compris lorsque les ``elif`` sont représentés par des ``If`` imbriqués dans
``orelse`` par l'AST Python.
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path

try:
    from scripts.audit_source_coverage import SourceAuditSession
except ModuleNotFoundError:
    from audit_source_coverage import SourceAuditSession

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
EXCLUDED_PARTS = {"ObjectListView", "Outils"}


def iter_python_files(root=NOETHYS):
    for path in root.rglob("*.py"):
        relative = path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        yield path


class NameEvents(ast.NodeVisitor):
    def __init__(self, name):
        self.name = name
        self.events = []

    def visit_Name(self, node):
        if node.id == self.name:
            mode = "load" if isinstance(node.ctx, ast.Load) else "store"
            self.events.append((node.lineno, mode))

    def visit_FunctionDef(self, node):
        return

    def visit_AsyncFunctionDef(self, node):
        return

    def visit_Lambda(self, node):
        return

    def visit_ClassDef(self, node):
        return


def assigned_names(statements):
    names = set()

    class Stores(ast.NodeVisitor):
        def visit_Name(self, node):
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                names.add(node.id)

        def visit_FunctionDef(self, node):
            return

        def visit_AsyncFunctionDef(self, node):
            return

        def visit_Lambda(self, node):
            return

        def visit_ClassDef(self, node):
            return

    visitor = Stores()
    for statement in statements:
        visitor.visit(statement)
    return names


def target_names(target):
    names = set()
    for node in ast.walk(target):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
    return names


def direct_definitions(statement):
    if isinstance(statement, ast.Assign):
        result = set()
        for target in statement.targets:
            result.update(target_names(target))
        return result
    if isinstance(statement, ast.AnnAssign):
        return target_names(statement.target)
    if isinstance(statement, ast.AugAssign):
        return target_names(statement.target)
    if isinstance(statement, (ast.Import, ast.ImportFrom)):
        result = set()
        for alias in statement.names:
            result.add(alias.asname or alias.name.split(".")[0])
        return result
    return set()


def direct_definitions_in_sequence(statements):
    result = set()
    for statement in statements:
        result.update(direct_definitions(statement))
    return result


def block_terminates(statements):
    if not statements:
        return False
    last = statements[-1]
    if isinstance(last, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
        return True
    if isinstance(last, ast.If) and last.orelse:
        return block_terminates(last.body) and block_terminates(last.orelse)
    return False


def first_event(statements, name):
    visitor = NameEvents(name)
    for statement in statements:
        visitor.visit(statement)
    if not visitor.events:
        return None
    return min(visitor.events, key=lambda item: item[0])


def function_args(function):
    result = {arg.arg for arg in function.args.posonlyargs}
    result.update(arg.arg for arg in function.args.args)
    result.update(arg.arg for arg in function.args.kwonlyargs)
    if function.args.vararg:
        result.add(function.args.vararg.arg)
    if function.args.kwarg:
        result.add(function.args.kwarg.arg)
    return result


def guaranteed_definitions(statements, predefined):
    """Retourne les noms définis sur tous les chemins qui atteignent la suite.

    Cette fonction est volontairement prudente. Les boucles ne propagent pas
    leurs affectations car leur corps peut ne jamais s'exécuter. Pour un ``if``
    exhaustif, l'intersection des définitions des branches est en revanche
    garantie. Lorsqu'une branche termine le flot, seule la branche qui continue
    contribue aux définitions disponibles après le ``if``.
    """
    defined = set(predefined)
    for statement in statements:
        if isinstance(statement, ast.If):
            body_defined = guaranteed_definitions(statement.body, defined)
            body_terminates = block_terminates(statement.body)

            if statement.orelse:
                else_defined = guaranteed_definitions(statement.orelse, defined)
                else_terminates = block_terminates(statement.orelse)
                if body_terminates and not else_terminates:
                    defined = else_defined
                elif else_terminates and not body_terminates:
                    defined = body_defined
                elif not body_terminates and not else_terminates:
                    defined = body_defined & else_defined
                else:
                    # Aucun chemin ne poursuit normalement après ce branchement.
                    return defined

        elif isinstance(statement, ast.Try):
            body_defined = guaranteed_definitions(statement.body, defined)
            handler_states = [guaranteed_definitions(handler.body, defined) for handler in statement.handlers]
            handler_terminations = [block_terminates(handler.body) for handler in statement.handlers]

            continuing_states = []
            if not block_terminates(statement.body):
                if statement.orelse:
                    continuing_states.append(guaranteed_definitions(statement.orelse, body_defined))
                else:
                    continuing_states.append(body_defined)
            for state, terminates in zip(handler_states, handler_terminations):
                if not terminates:
                    continuing_states.append(state)

            if continuing_states:
                merged = set(continuing_states[0])
                for state in continuing_states[1:]:
                    merged.intersection_update(state)
                defined = merged

            if statement.finalbody:
                defined = guaranteed_definitions(statement.finalbody, defined)

        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            with_defined = set(defined)
            for item in statement.items:
                if item.optional_vars is not None:
                    with_defined.update(target_names(item.optional_vars))
            defined = guaranteed_definitions(statement.body, with_defined)

        elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
            # Le corps d'une boucle peut ne pas être parcouru. Ne rien propager.
            pass

        else:
            defined.update(direct_definitions(statement))

    return defined


def scan_sequence(statements, predefined, relpath, function_name, findings):
    defined = set(predefined)
    for index, statement in enumerate(statements):
        if isinstance(statement, ast.If):
            body_assigned = assigned_names(statement.body)
            else_assigned = assigned_names(statement.orelse)
            only_body = body_assigned - else_assigned
            only_else = else_assigned - body_assigned
            following = statements[index + 1 :]

            for name in sorted(only_body | only_else):
                if name in defined:
                    continue
                if name in only_body:
                    unassigned_path_terminates = block_terminates(statement.orelse) if statement.orelse else False
                    branch = "body_only"
                else:
                    unassigned_path_terminates = block_terminates(statement.body)
                    branch = "else_only"
                if unassigned_path_terminates:
                    continue
                event = first_event(following, name)
                if event and event[1] == "load":
                    findings.append({
                        "kind": "branch_assignment_gap",
                        "priority": "high",
                        "file": relpath,
                        "function": function_name,
                        "if_line": statement.lineno,
                        "line": event[0],
                        "name": name,
                        "detail": branch,
                    })

            scan_sequence(statement.body, defined, relpath, function_name, findings)
            scan_sequence(statement.orelse, defined, relpath, function_name, findings)

            body_defined = guaranteed_definitions(statement.body, defined)
            body_terminates = block_terminates(statement.body)
            if statement.orelse:
                else_defined = guaranteed_definitions(statement.orelse, defined)
                else_terminates = block_terminates(statement.orelse)
                if body_terminates and not else_terminates:
                    defined = else_defined
                elif else_terminates and not body_terminates:
                    defined = body_defined
                elif not body_terminates and not else_terminates:
                    defined = body_defined & else_defined
            # Sans ``else``, le corps peut ne pas s'exécuter : aucune nouvelle
            # définition n'est garantie après le branchement.

        elif isinstance(statement, (ast.For, ast.AsyncFor)):
            loop_defined = defined | target_names(statement.target)
            scan_sequence(statement.body, loop_defined, relpath, function_name, findings)
            scan_sequence(statement.orelse, defined, relpath, function_name, findings)

        elif isinstance(statement, ast.While):
            scan_sequence(statement.body, defined, relpath, function_name, findings)
            scan_sequence(statement.orelse, defined, relpath, function_name, findings)

        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            with_defined = set(defined)
            for item in statement.items:
                if item.optional_vars is not None:
                    with_defined.update(target_names(item.optional_vars))
            scan_sequence(statement.body, with_defined, relpath, function_name, findings)
            defined = guaranteed_definitions(statement.body, with_defined)

        elif isinstance(statement, ast.Try):
            scan_sequence(statement.body, defined, relpath, function_name, findings)
            for handler in statement.handlers:
                handler_defined = set(defined)
                if handler.name:
                    handler_defined.add(handler.name)
                scan_sequence(handler.body, handler_defined, relpath, function_name, findings)
            scan_sequence(statement.orelse, defined, relpath, function_name, findings)
            scan_sequence(statement.finalbody, defined, relpath, function_name, findings)

            defined = guaranteed_definitions([statement], defined)

        defined.update(direct_definitions(statement))


def _scan_loaded(tree, path, root=NOETHYS):
    relpath = str(path.relative_to(root)).replace("\\", "/")
    findings = []
    for function in (node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))):
        scan_sequence(function.body, function_args(function), relpath, function.name, findings)
    return findings


def scan_file(path, root=NOETHYS):
    session = SourceAuditSession([path])
    loaded = session.parse(path)
    session.require_complete()
    assert loaded is not None
    _source, tree = loaded
    return _scan_loaded(tree, path, root)


def build_report(root=NOETHYS):
    findings = []
    for path in iter_python_files(root):
        findings.extend(scan_file(path, root))
    unique = {}
    for item in findings:
        key = (item["file"], item["function"], item["if_line"], item["line"], item["name"])
        unique[key] = item
    findings = sorted(unique.values(), key=lambda item: (item["file"], item["line"], item["name"]))
    return {
        "count": len(findings),
        "kinds": dict(Counter(item["kind"] for item in findings)),
        "priorities": dict(Counter(item["priority"] for item in findings)),
        "findings": findings,
    }


def _coverage_session(root=NOETHYS):
    session = SourceAuditSession(iter_python_files(root))
    for path in session.paths:
        session.parse(path)
    return session


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default="", metavar="FILE")
    args = parser.parse_args(argv)

    coverage = _coverage_session()
    coverage.report(prefix="Couverture audit affectations conditionnelles")
    coverage.require_complete()

    report = build_report()
    print(f"BRANCH_ASSIGNMENT_GAPS={report['count']}")
    for item in report["findings"]:
        print(f"- {item['file']}:{item['line']} {item['function']} — {item['name']} ({item['detail']})")
    if args.json:
        output = Path(args.json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
