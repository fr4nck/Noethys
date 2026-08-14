#!/usr/bin/env python3
"""Échoue uniquement sur les chargements dynamiques difficiles à empaqueter.

Le contrôle vise les motifs que PyInstaller ne peut pas résoudre statiquement :
imports dynamiques non littéraux, exec/eval et découverte dynamique de modules.
Les imports dynamiques avec nom de module littéral restent autorisés : ils peuvent
être couverts explicitement par la spec PyInstaller si nécessaire.
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


def is_literal_string(node: ast.AST | None) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


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
            argument = node.args[0] if node.args else None
            if not is_literal_string(argument):
                findings.append((node.lineno, f"import dynamique non littéral via {name}()"))
        elif name in {"exec", "eval"}:
            findings.append((node.lineno, f"exécution dynamique via {name}()"))
        elif name in {"pkgutil.iter_modules", "pkgutil.walk_packages", "importlib.util.spec_from_file_location"}:
            findings.append((node.lineno, f"découverte dynamique via {name}()"))
    return sorted(set(findings))


def main() -> int:
    total = 0
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        for lineno, message in scan(path):
            total += 1
            print(f"{path}:{lineno}: {message}")
    if total:
        print(f"\n{total} chargement(s) dynamique(s) risqué(s) détecté(s).")
        return 1
    print("Aucun chargement dynamique risqué détecté.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
