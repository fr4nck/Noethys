#!/usr/bin/env python3
"""Repère les conversions de dates fragiles héritées de Python 2.

Cible les conversions directes en entier de tranches fixes et les constructions
manuelles de dates à partir de ces tranches. Audit informatif uniquement.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "noethys")
DATE_HINTS = (
    "date", "jour", "mois", "annee", "année", "naiss",
    "debut", "début", "echeance", "échéance",
)
CALENDAR_SLICES = {(0, 2), (0, 4), (2, 4), (3, 5), (4, 6), (5, 7), (6, 8), (8, 10)}


def looks_like_date_name(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        name = node.id.lower()
    elif isinstance(node, ast.Attribute):
        name = node.attr.lower()
    else:
        return False
    return any(hint in name for hint in DATE_HINTS)


def slice_bounds(node: ast.AST) -> tuple[int | None, int | None] | None:
    if not isinstance(node, ast.Subscript) or not isinstance(node.slice, ast.Slice):
        return None
    lower, upper = node.slice.lower, node.slice.upper
    if lower is not None and not isinstance(lower, ast.Constant):
        return None
    if upper is not None and not isinstance(upper, ast.Constant):
        return None
    start = lower.value if isinstance(lower, ast.Constant) else None
    stop = upper.value if isinstance(upper, ast.Constant) else None
    if not isinstance(start, (int, type(None))) or not isinstance(stop, (int, type(None))):
        return None
    return start, stop


def is_fragile_date_slice(node: ast.AST) -> bool:
    return isinstance(node, ast.Subscript) and slice_bounds(node) in CALENDAR_SLICES and looks_like_date_name(node.value)


def call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        parts = [node.func.attr]
        value = node.func.value
        while isinstance(value, ast.Attribute):
            parts.append(value.attr)
            value = value.value
        if isinstance(value, ast.Name):
            parts.append(value.id)
        return ".".join(reversed(parts))
    return ""


def scan(path: Path) -> list[tuple[int, str]]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
    except (OSError, SyntaxError):
        return []
    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node)
        if name == "int" and len(node.args) == 1 and is_fragile_date_slice(node.args[0]):
            findings.append((node.lineno, "int() appliqué à une tranche fixe de date"))
        elif name in {"date", "datetime", "datetime.date", "datetime.datetime"}:
            if any(isinstance(arg, ast.Call) and call_name(arg) == "int" and arg.args and is_fragile_date_slice(arg.args[0]) for arg in node.args):
                findings.append((node.lineno, "construction de date à partir d'une tranche fixe"))
    return sorted(set(findings))


def main() -> int:
    total = 0
    for path in sorted(ROOT.rglob("*.py")):
        for lineno, message in scan(path):
            total += 1
            print(f"{path}:{lineno}: {message}")
    print(f"\n{total} occurrence(s) de parsing de date fragile détectée(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
