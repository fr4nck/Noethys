#!/usr/bin/env python3
"""Inventorie les frontières d'encodage potentiellement fragiles sous Python 3.

Le contrôle est informatif. Il signale les ouvertures texte sans encodage,
les codecs historiques, les conversions encode/decode et certains usages CSV.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "noethys")
SKIP_DIRS = {".git", "build", "dist", "__pycache__", "venv", ".venv"}
TEXT_MODES = {"r", "w", "a", "x", "r+", "w+", "a+", "x+"}


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


def constant_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def keyword_value(node: ast.Call, name: str) -> ast.AST | None:
    for keyword in node.keywords:
        if keyword.arg == name:
            return keyword.value
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

        if name in {"open", "io.open", "Path.open"}:
            mode_node = keyword_value(node, "mode")
            if mode_node is None and len(node.args) > 1:
                mode_node = node.args[1]
            mode = constant_string(mode_node) or "r"
            binary = "b" in mode
            has_encoding = keyword_value(node, "encoding") is not None
            if not binary and not has_encoding:
                findings.append((node.lineno, f"ouverture texte sans encoding explicite via {name}()"))

        elif name == "codecs.open":
            findings.append((node.lineno, "codecs.open() historique à vérifier"))

        elif name.endswith(".encode") or name.endswith(".decode"):
            codec = constant_string(node.args[0] if node.args else None)
            detail = codec or "codec implicite"
            findings.append((node.lineno, f"conversion {name.split('.')[-1]}() : {detail}"))

        elif name in {"csv.reader", "csv.writer", "csv.DictReader", "csv.DictWriter"}:
            findings.append((node.lineno, f"usage CSV à vérifier via {name}()"))

        elif name in {"json.load", "json.dump"}:
            findings.append((node.lineno, f"flux JSON à vérifier via {name}()"))

    return sorted(set(findings))


def main() -> int:
    total = 0
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        for lineno, message in scan(path):
            total += 1
            print(f"{path}:{lineno}: {message}")
    print(f"\n{total} frontière(s) d'encodage à examiner.")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
