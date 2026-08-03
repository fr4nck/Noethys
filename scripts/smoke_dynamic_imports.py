#!/usr/bin/env python3
"""Vérifie que les imports dynamiques littéraux de Noethys sont résolvables.

Les imports calculés restent signalés par audit_dynamic_imports.py. Ce contrôle
bloquant traite uniquement les noms de modules écrits explicitement dans le
code, afin d'éviter un exécutable qui plante tardivement à l'ouverture d'un
écran.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SKIP_DIRS = {".git", "build", "dist", "__pycache__", "venv", ".venv"}

if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))


def call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts: list[str] = []
        current: ast.AST = func
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    return ""


def iter_literal_imports(path: Path):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
    except (OSError, SyntaxError):
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if call_name(node) not in {"__import__", "importlib.import_module", "import_module"}:
            continue
        if not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            yield node.lineno, first.value


def main() -> int:
    failures = 0
    checked: set[str] = set()
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        for lineno, module_name in iter_literal_imports(path) or ():
            if module_name in checked:
                continue
            checked.add(module_name)
            try:
                spec = importlib.util.find_spec(module_name)
            except (ImportError, AttributeError, ValueError) as err:
                spec = None
                detail = f"{type(err).__name__}: {err}"
            else:
                detail = "ok" if spec is not None else "introuvable"
            print(f"- {module_name}: {detail} ({path}:{lineno})")
            if spec is None:
                failures += 1

    print(f"\n{len(checked)} import(s) dynamique(s) littéral(aux) vérifié(s).")
    if failures:
        print(f"{failures} module(s) dynamique(s) introuvable(s).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
