#!/usr/bin/env python3
"""Repère les arguments numériques wxPython susceptibles de devenir flottants.

Cible les appels de taille, position et dimensions contenant une division `/`
non protégée par une conversion entière. Audit informatif uniquement, inspiré
des TypeError rencontrées dans Teamworks.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "noethys")
TARGETS = {
    "Size", "Point", "Rect",
    "SetSize", "SetMinSize", "SetMaxSize", "SetPosition",
    "SetToolBitmapSize", "SetColumnWidth", "SetItemSize",
    "SetRowSize", "SetColSize", "SetScrollRate",
}
INTEGER_CONVERSIONS = {"int", "round", "floor", "ceil", "trunc"}


def call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def conversion_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def contains_unprotected_division(node: ast.AST, protected: bool = False) -> bool:
    """Détecte une division qui n'est pas sous une conversion entière."""
    if isinstance(node, ast.Call) and conversion_name(node) in INTEGER_CONVERSIONS:
        protected = True

    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) and not protected:
        return True

    return any(
        contains_unprotected_division(child, protected)
        for child in ast.iter_child_nodes(node)
    )


def scan(path: Path) -> list[tuple[int, str]]:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    findings: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or call_name(node) not in TARGETS:
            continue
        for arg in node.args:
            if contains_unprotected_division(arg):
                findings.append((node.lineno, f"division potentiellement flottante dans {call_name(node)}()"))
                break
        for keyword in node.keywords:
            if keyword.arg not in {"size", "pos", "width", "height"}:
                continue
            if contains_unprotected_division(keyword.value):
                findings.append((node.lineno, f"argument {keyword.arg} potentiellement flottant dans {call_name(node)}()"))
                break
    return sorted(set(findings))


def main() -> int:
    total = 0
    for path in sorted(ROOT.rglob("*.py")):
        for lineno, message in scan(path):
            total += 1
            print(f"{path}:{lineno}: {message}")
    print(f"\n{total} argument(s) wxPython potentiellement flottant(s).")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
