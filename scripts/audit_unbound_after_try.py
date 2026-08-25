#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Détecte les variables locales définies seulement dans un ``try`` puis lues
après un ``except`` qui peut continuer.

Ce motif produit un ``UnboundLocalError`` uniquement sur le chemin d'erreur et
échappe donc facilement aux tests heureux. L'analyse reste conservative, mais
respecte l'ordre d'exécution à l'intérieur des blocs suivants afin de ne pas
confondre une réaffectation dans un nouveau ``try``/une boucle avec une lecture
de l'ancienne variable.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
EXCLUDED_PARTS = {"ObjectListView", "Outils"}


def _assigned_names(node):
    names = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
            names.add(child.id)
    return names


def _loaded_names(node):
    names = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
            names.add(child.id)
    return names


def _handler_terminates(handler):
    if not handler.body:
        return False
    last = handler.body[-1]
    return isinstance(last, (ast.Return, ast.Raise, ast.Break, ast.Continue))


def _arguments(function):
    args = set()
    if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        return args
    a = function.args
    for item in list(a.posonlyargs) + list(a.args) + list(a.kwonlyargs):
        args.add(item.arg)
    if a.vararg:
        args.add(a.vararg.arg)
    if a.kwarg:
        args.add(a.kwarg.arg)
    return args


def _first_name_line(node, name, ctx_type):
    return min(
        (getattr(child, "lineno", getattr(node, "lineno", 0))
         for child in ast.walk(node)
         if isinstance(child, ast.Name) and isinstance(child.ctx, ctx_type) and child.id == name),
        default=0,
    )


def _first_event(statements, name):
    """Retourne ('load'|'store', ligne) pour le premier événement exécutable.

    Les affectations dans un bloc conditionnel ne sont pas considérées comme
    garanties pour les instructions *suivantes*. En revanche, une affectation
    qui précède une lecture dans le même bloc protège cette lecture : si cette
    affectation lève une exception, le reste du bloc n'est pas exécuté.
    """
    for stmt in statements:
        if isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            loads = set()
            if isinstance(stmt, ast.Assign):
                loads = _loaded_names(stmt.value)
            elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
                loads = _loaded_names(stmt.value)
            elif isinstance(stmt, ast.AugAssign):
                loads = _loaded_names(stmt.value) | _loaded_names(stmt.target)
            if name in loads:
                return "load", _first_name_line(stmt, name, ast.Load) or getattr(stmt, "lineno", 0)
            if name in _assigned_names(stmt):
                return "store", getattr(stmt, "lineno", 0)
            continue

        if isinstance(stmt, (ast.For, ast.AsyncFor)):
            if name in _loaded_names(stmt.iter):
                return "load", _first_name_line(stmt.iter, name, ast.Load)
            target_assigns = name in _assigned_names(stmt.target)
            if target_assigns:
                # La cible est affectée avant chaque exécution du corps. Les
                # lectures du corps sont donc sûres ; seul le ``else`` peut
                # s'exécuter sans itération.
                event, line = _first_event(stmt.orelse, name)
                if event == "load":
                    return event, line
                continue
            event, line = _first_event(stmt.body, name)
            if event == "load":
                return event, line
            event, line = _first_event(stmt.orelse, name)
            if event == "load":
                return event, line
            continue

        if isinstance(stmt, ast.If):
            if name in _loaded_names(stmt.test):
                return "load", _first_name_line(stmt.test, name, ast.Load)
            for branch in (stmt.body, stmt.orelse):
                event, line = _first_event(branch, name)
                if event == "load":
                    return event, line
            continue

        if isinstance(stmt, ast.Try):
            event, line = _first_event(stmt.body, name)
            if event == "load":
                return event, line
            # Si le corps commence par une affectation, les lectures suivantes
            # de ce même corps sont protégées. Un handler peut toutefois lire
            # le nom si l'affectation a échoué avant de le lier.
            for handler in stmt.handlers:
                handler_event, handler_line = _first_event(handler.body, name)
                if handler_event == "load":
                    return handler_event, handler_line
            for block in (stmt.orelse, stmt.finalbody):
                block_event, block_line = _first_event(block, name)
                if block_event == "load" and event != "store":
                    return block_event, block_line
            if event == "store":
                return "store", line
            continue

        if isinstance(stmt, (ast.With, ast.AsyncWith)):
            for item in stmt.items:
                if name in _loaded_names(item.context_expr):
                    return "load", _first_name_line(item.context_expr, name, ast.Load)
                if item.optional_vars is not None and name in _assigned_names(item.optional_vars):
                    # Affecté avant le corps si l'entrée du contexte réussit.
                    event, line = _first_event(stmt.body, name)
                    if event == "load":
                        return "store", getattr(stmt, "lineno", line)
            event, line = _first_event(stmt.body, name)
            if event == "load":
                return event, line
            continue

        if name in _loaded_names(stmt):
            return "load", _first_name_line(stmt, name, ast.Load) or getattr(stmt, "lineno", 0)

        # Une affectation top-level dans une instruction simple garantit le nom
        # pour la suite. Pour les structures complexes, les cas ci-dessus ont
        # déjà traité les branches sans prétendre à une garantie globale.
        if name in _assigned_names(stmt):
            return "store", getattr(stmt, "lineno", 0)

    return None, 0


def _scan_block(statements, relpath, inherited_defined=None):
    findings = []
    defined = set(inherited_defined or ())

    for index, stmt in enumerate(statements):
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            findings.extend(_scan_block(stmt.body, relpath, _arguments(stmt)))
            defined.add(stmt.name)
            continue
        if isinstance(stmt, ast.ClassDef):
            for child in stmt.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    findings.extend(_scan_block(child.body, relpath, _arguments(child)))
            defined.add(stmt.name)
            continue

        if isinstance(stmt, ast.Try) and stmt.handlers:
            assigned_try = set()
            for child in stmt.body:
                assigned_try |= _assigned_names(child)

            continuing = [handler for handler in stmt.handlers if not _handler_terminates(handler)]
            if continuing:
                guaranteed_in_handlers = None
                for handler in continuing:
                    assigned_handler = set()
                    for child in handler.body:
                        assigned_handler |= _assigned_names(child)
                    if guaranteed_in_handlers is None:
                        guaranteed_in_handlers = assigned_handler
                    else:
                        guaranteed_in_handlers &= assigned_handler
                guaranteed_in_handlers = guaranteed_in_handlers or set()

                risky = assigned_try - defined - guaranteed_in_handlers
                following = statements[index + 1:]
                for name in sorted(risky):
                    event, line = _first_event(following, name)
                    if event == "load":
                        findings.append({
                            "file": relpath,
                            "try_line": getattr(stmt, "lineno", 0),
                            "read_line": line,
                            "name": name,
                            "reason": "variable définie dans try, handler continuant sans définition garantie, puis lecture après le try",
                        })

            for child in stmt.finalbody:
                defined |= _assigned_names(child)
        else:
            defined |= _assigned_names(stmt)

        for attr in ("body", "orelse"):
            child_block = getattr(stmt, attr, None)
            if isinstance(child_block, list) and not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Try)):
                findings.extend(_scan_block(child_block, relpath, defined))

    return findings


def iter_python_files(root=NOETHYS):
    for path in root.rglob("*.py"):
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        yield path


def scan(root=NOETHYS):
    findings = []
    for path in iter_python_files(root):
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(path))
        except (OSError, SyntaxError):
            continue
        relpath = str(path.relative_to(root)).replace("\\", "/")
        findings.extend(_scan_block(tree.body, relpath))
    findings.sort(key=lambda item: (item["file"], item["read_line"], item["name"]))
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default="", metavar="FILE")
    parser.add_argument("--fail-on-findings", action="store_true")
    args = parser.parse_args(argv)

    findings = scan()
    print(f"TRY_DEFINED_USED_AFTER={len(findings)}")
    for item in findings:
        print(f"- {item['file']}:{item['read_line']} {item['name']} (try ligne {item['try_line']})")

    if args.json:
        output = Path(args.json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({"count": len(findings), "findings": findings}, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Rapport JSON exporté : {output}")

    if args.fail_on_findings and findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
