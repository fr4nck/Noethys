#!/usr/bin/env python3
"""Repère les motifs wxPython susceptibles de provoquer des assertions UI.

Audit informatif inspiré des incidents Teamworks : widgets ajoutés plusieurs
fois à un sizer, SetSizer répété dans une même méthode et anciens appels AUI.
Aucun fichier applicatif n'est modifié.
"""
from __future__ import annotations

import ast
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "noethys")
AUI_METHODS = {"SavePerspective", "LoadPerspective", "AddPane", "DetachPane", "Update", "UnInit"}


def call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def first_arg_key(node: ast.Call) -> str | None:
    if not node.args:
        return None
    try:
        return ast.unparse(node.args[0])
    except Exception:
        return None


def scan(path: Path) -> list[tuple[int, str]]:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    findings: list[tuple[int, str]] = []
    for scope in [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        set_sizer_lines: list[int] = []
        added_objects: list[tuple[str, int]] = []
        for node in ast.walk(scope):
            if not isinstance(node, ast.Call):
                continue
            name = call_name(node)
            if name in {"SetSizer", "SetSizerAndFit"}:
                set_sizer_lines.append(node.lineno)
            if name in {"Add", "AddMany", "Insert", "Prepend"}:
                key = first_arg_key(node)
                if key and key not in {"None", "0", "1"}:
                    added_objects.append((key, node.lineno))
            if name in AUI_METHODS:
                findings.append((node.lineno, f"appel AUI à vérifier : {name}()"))

        if len(set_sizer_lines) > 1:
            findings.append((set_sizer_lines[1], "plusieurs SetSizer/SetSizerAndFit dans la même méthode"))

        counts = Counter(key for key, _ in added_objects)
        for key, count in counts.items():
            if count > 1:
                first_line = next(line for candidate, line in added_objects if candidate == key)
                findings.append((first_line, f"objet potentiellement ajouté plusieurs fois au sizer : {key}"))

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
