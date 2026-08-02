#!/usr/bin/env python3
"""Repère les conversions de dates fragiles héritées de Python 2.

Cible notamment les motifs vus dans Teamworks : conversion directe en entier
de tranches fixes (ex. int(date_str[5:7])) et construction manuelle de dates
sans validation préalable. Le script est informatif : il n'altère aucun fichier.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "noethys")
DATE_HINTS = ("date", "jour", "mois", "annee", "année", "naiss", "debut", "début", "fin")


def looks_like_date_name(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        name = node.id.lower()
    elif isinstance(node, ast.Attribute):
        name = node.attr.lower()
    else:
        return False
    return any(hint in name for hint in DATE_HINTS)


def is_slice(node: ast.AST) -> bool:
    return isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice)


def scan(path: Path) -> list[tuple[int, str]]:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    findings: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id != "int" or len(node.args) != 1:
            continue
        arg = node.args[0]
        if is_slice(arg) and looks_like_date_name(arg.value):
            findings.append((node.lineno, "int() appliqué à une tranche fixe de date"))
    return findings


def main() -> int:
    total = 0
    for path in sorted(ROOT.rglob("*.py")):
        for lineno, message in scan(path):
            total += 1
            print(f"{path}:{lineno}: {message}")
    print(f"\n{total} occurrence(s) de parsing de date fragile détectée(s).")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
