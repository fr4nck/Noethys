#!/usr/bin/env python3
"""Inventorie les frontières d'encodage réellement actionnables sous Python 3.

L'audit se concentre sur les flux texte ouverts sans encodage explicite.
Les occurrences restent informatives ; la couverture des sources est bloquante.
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


def constant_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def keyword_value(node: ast.Call, name: str) -> ast.AST | None:
    for keyword in node.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def positional_or_keyword(node: ast.Call, position: int, keyword: str) -> ast.AST | None:
    value = keyword_value(node, keyword)
    if value is not None:
        return value
    if len(node.args) > position:
        return node.args[position]
    return None


def scan_tree(tree: ast.AST) -> list[tuple[int, str]]:
    findings: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node)

        if name in {"open", "io.open", "Path.open"}:
            mode_node = positional_or_keyword(node, 1, "mode")
            mode = constant_string(mode_node) or "r"
            if "b" not in mode and keyword_value(node, "encoding") is None:
                findings.append((node.lineno, f"ouverture texte sans encoding explicite via {name}()"))
            continue

        if name == "codecs.open":
            mode_node = positional_or_keyword(node, 2, "mode")
            mode = constant_string(mode_node) or "r"
            encoding_node = positional_or_keyword(node, 1, "encoding")
            encoding = constant_string(encoding_node)
            if "b" not in mode and not encoding:
                findings.append((node.lineno, "codecs.open() texte sans encoding explicite"))

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
    files_with_findings = 0
    for path in session.paths:
        loaded = session.parse(path)
        if loaded is None:
            continue
        _source, tree = loaded
        findings = scan_tree(tree)
        if findings:
            files_with_findings += 1
        for lineno, message in findings:
            total += 1
            print(f"{path}:{lineno}: {message}")
    print(f"\n{total} frontière(s) texte/encodage actionnable(s) dans {files_with_findings} fichier(s).")
    if not session.report():
        print("Audit incomplet : inventaire encodage non exhaustif.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
