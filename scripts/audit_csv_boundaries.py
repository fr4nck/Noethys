#!/usr/bin/env python3
"""Audit des usages CSV potentiellement fragiles sous Python 3/Windows.

Les occurrences restent informatives. La couverture des sources, elle, est
bloquante : un fichier illisible ou non parsable invalide l'inventaire.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

try:
    from scripts.audit_source_coverage import SourceAuditSession, iter_python_files
except ModuleNotFoundError:
    from audit_source_coverage import SourceAuditSession, iter_python_files

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


def scan_tree(tree: ast.AST) -> list[tuple[int, str]]:
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
            if literal(keyword(node, "newline")) != "":
                findings.append((node.lineno, "fichier CSV texte sans newline=''"))
    return sorted(set(findings))


def scan(path: Path) -> list[tuple[int, str]]:
    session = SourceAuditSession([path])
    loaded = session.parse(path)
    if loaded is None:
        raise RuntimeError(session.coverage.failures[0].format())
    _source, tree = loaded
    return scan_tree(tree)


def main() -> int:
    session = SourceAuditSession(iter_python_files(ROOT, skip_dirs=SKIP_DIRS))
    total = 0
    for path in session.paths:
        loaded = session.parse(path)
        if loaded is None:
            continue
        _source, tree = loaded
        for lineno, message in scan_tree(tree):
            total += 1
            print(f"{path}:{lineno}: {message}")
    print(f"\n{total} frontière(s) CSV à examiner.")
    if not session.report():
        print("Audit incomplet : inventaire CSV non exhaustif.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
