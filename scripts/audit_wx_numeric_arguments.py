#!/usr/bin/env python3
"""Repère les arguments numériques wxPython susceptibles de devenir flottants.

Cible les appels de taille, position et dimensions contenant une division `/`
ou une expression arithmétique non explicitement convertie en entier. Audit
informatif uniquement, inspiré des TypeError rencontrées dans Teamworks.
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


def call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def contains_true_division(node: ast.AST) -> bool:
    return any(isinstance(child, ast.BinOp) and isinstance(child.op, ast.Div) for child in ast.walk(node))


def protected_by_int(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"int", "round"}
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
            if protected_by_int(arg):
                continue
            if contains_true_division(arg):
                findings.append((node.lineno, f"division potentiellement flottante dans {call_name(node)}()"))
                break
        for keyword in node.keywords:
            if keyword.arg not in {"size", "pos", "width", "height"}:
                continue
            if not protected_by_int(keyword.value) and contains_true_division(keyword.value):
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
