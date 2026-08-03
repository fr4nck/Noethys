#!/usr/bin/env python3
"""Inventorie les imports dynamiques susceptibles d'échapper à PyInstaller.

Le contrôle est informatif : il signale les appels à __import__, importlib,
exec/eval et les imports dont le nom de module n'est pas une chaîne littérale.
Aucun fichier applicatif n'est modifié.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "noethys")
SKIP_DIRS = {".git", "build", "dist", "__pycache__", "venv", ".venv"}


def call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        parts = []
        current = func
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    return ""


def literal_module_name(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def scan(path: Path) -> list[tuple[int, str]]:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError):
        return []

    findings: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node)
        if name in {"__import__", "importlib.import_module", "import_module"}:
            module = literal_module_name(node.args[0] if node.args else None)
            if module is None:
                findings.append((node.lineno, f"import dynamique non littéral via {name}()"))
            else:
                findings.append((node.lineno, f"import dynamique littéral à vérifier dans PyInstaller : {module}"))
        elif name in {"exec", "eval"}:
            findings.append((node.lineno, f"chargement de code dynamique via {name}()"))
        elif name in {"pkgutil.iter_modules", "pkgutil.walk_packages", "importlib.util.spec_from_file_location"}:
            findings.append((node.lineno, f"découverte dynamique de modules via {name}()"))
    return sorted(set(findings))


def main() -> int:
    total = 0
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        for lineno, message in scan(path):
            total += 1
            print(f"{path}:{lineno}: {message}")
    print(f"\n{total} import(s) ou chargement(s) dynamique(s) à examiner.")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
