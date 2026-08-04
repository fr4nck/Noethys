#!/usr/bin/env python3
"""Audit des usages CSV potentiellement fragiles sous Python 3/Windows.

Le contrôle est informatif. Il signale les fichiers CSV ouverts sans
``encoding=`` explicite, sans ``newline=''`` et les usages csv.* alimentés par
une ouverture binaire ou ambiguë.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "noethys")
SKIP_DIRS = {".git", ".venv", "__pycache__", "build", "dist", "venv"}


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


def keyword(node: ast.Call, name: str) -> ast.AST | None:
    for item in node.keywords:
        if item.arg == name:
            return item.value
    return None


def literal(node: ast.AST | None):
    if isinstance(node, ast.Constant):
        return node.value
    return None


def is_csv_path(node: ast.AST | None) -> bool:
    value = literal(node)
    return isinstance(value, str) and value.lower().endswith(".csv")


def scan(path: Path) -> list[tuple[int, str]]:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []

    findings: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node)

        if name in {"open", "io.open", "Path.open"}:
            filename = node.args[0] if node.args else None
            if not is_csv_path(filename):
                continue
            mode_node = keyword(node, "mode")
            if mode_node is None and len(node.args) > 1:
                mode_node = node.args[1]
            mode = literal(mode_node) or "r"
            if isinstance(mode, str) and "b" in mode:
                findings.append((node.lineno, "fichier CSV ouvert en mode binaire"))
                continue
            if keyword(node, "encoding") is None:
                findings.append((node.lineno, "fichier CSV texte sans encoding explicite"))
            newline_value = literal(keyword(node, "newline"))
            if newline_value != "":
                findings.append((node.lineno, "fichier CSV texte sans newline=''"))

        elif name in {"csv.reader", "csv.writer", "csv.DictReader", "csv.DictWriter"}:
            if not node.args:
                findings.append((node.lineno, f"{name} sans flux explicite"))

    return sorted(set(findings))


def main() -> int:
    total = 0
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        for lineno, message in scan(path):
            total += 1
            print(f"{path}:{lineno}: {message}")
    print(f"\n{total} frontière(s) CSV à examiner.")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
