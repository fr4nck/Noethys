#!/usr/bin/env python3
"""Repère les motifs wxPython susceptibles de provoquer des assertions UI.

Audit informatif inspiré des incidents Teamworks : widget ajouté plusieurs fois
au même sizer, SetSizer répété sur la même fenêtre et appels sensibles d'un
AuiManager. Aucun fichier applicatif n'est modifié.
"""
from __future__ import annotations

import ast
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "noethys")
AUI_METHODS = {"SavePerspective", "LoadPerspective", "AddPane", "DetachPane", "Update", "UnInit"}
AUI_RECEIVER_HINTS = ("aui", "mgr", "manager", "gestionnaire")
SIZER_METHODS = {"Add", "Insert", "Prepend"}


def expression_key(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None


def call_parts(node: ast.Call) -> tuple[str | None, str | None]:
    func = node.func
    if isinstance(func, ast.Attribute):
        return expression_key(func.value), func.attr
    if isinstance(func, ast.Name):
        return None, func.id
    return None, None


def iter_scope_nodes(scope: ast.AST):
    """Parcourt une méthode sans incorporer ses fonctions/classes imbriquées."""
    stack = list(reversed(getattr(scope, "body", [])))
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        stack.extend(reversed(list(ast.iter_child_nodes(node))))


def looks_like_aui_receiver(receiver: str | None) -> bool:
    if not receiver:
        return False
    lowered = receiver.lower()
    return any(hint in lowered for hint in AUI_RECEIVER_HINTS)


def scan(path: Path) -> list[tuple[int, str]]:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    findings: list[tuple[int, str]] = []
    scopes = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    for scope in scopes:
        set_sizers: list[tuple[str, int]] = []
        added_objects: list[tuple[tuple[str, str], int]] = []

        for node in iter_scope_nodes(scope):
            if not isinstance(node, ast.Call):
                continue
            receiver, name = call_parts(node)

            if name in {"SetSizer", "SetSizerAndFit"}:
                set_sizers.append((receiver or "<appel direct>", node.lineno))

            if name in SIZER_METHODS and receiver and node.args:
                object_key = expression_key(node.args[0])
                if object_key and object_key not in {"None", "0", "1"}:
                    added_objects.append(((receiver, object_key), node.lineno))

            if name in AUI_METHODS and looks_like_aui_receiver(receiver):
                findings.append((node.lineno, f"appel AUI à vérifier : {receiver}.{name}()"))

        set_sizer_counts = Counter(receiver for receiver, _ in set_sizers)
        for receiver, count in set_sizer_counts.items():
            if count > 1:
                lines = [line for candidate, line in set_sizers if candidate == receiver]
                findings.append((lines[1], f"plusieurs SetSizer/SetSizerAndFit sur {receiver}"))

        add_counts = Counter(key for key, _ in added_objects)
        for (sizer, object_key), count in add_counts.items():
            if count > 1:
                first_line = next(
                    line for candidate, line in added_objects
                    if candidate == (sizer, object_key)
                )
                findings.append((
                    first_line,
                    f"objet potentiellement ajouté plusieurs fois à {sizer} : {object_key}",
                ))

    return sorted(set(findings))


def main() -> int:
    total = 0
    for path in sorted(ROOT.rglob("*.py")):
        for lineno, message in scan(path):
            total += 1
            print(f"{path}:{lineno}: {message}")
    print(f"\n{total} motif(s) wx layout/AUI à examiner.")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
