#!/usr/bin/env python3
"""Repère les arguments numériques wxPython susceptibles de devenir flottants.

Cible les appels de taille, position et dimensions contenant une division `/`
non protégée par une conversion entière. Les occurrences restent informatives,
mais un fichier non analysé rend désormais l'audit invalide.
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
TARGETS = {
    "Size", "Point", "Rect", "SetSize", "SetMinSize", "SetMaxSize",
    "SetPosition", "SetToolBitmapSize", "SetColumnWidth", "SetItemSize",
    "SetRowSize", "SetColSize", "SetScrollRate",
}
INTEGER_CONVERSIONS = {"int", "round", "floor", "ceil", "trunc"}


def call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    if isinstance(node.func, ast.Name):
        return node.func.id
    return None


def conversion_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def contains_unprotected_division(node: ast.AST, protected: bool = False) -> bool:
    if isinstance(node, ast.Call) and conversion_name(node) in INTEGER_CONVERSIONS:
        protected = True
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) and not protected:
        return True
    return any(contains_unprotected_division(child, protected) for child in ast.iter_child_nodes(node))


def scan_tree(tree: ast.AST) -> list[tuple[int, str]]:
    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or call_name(node) not in TARGETS:
            continue
        if any(contains_unprotected_division(arg) for arg in node.args):
            findings.append((node.lineno, f"division potentiellement flottante dans {call_name(node)}()"))
            continue
        for keyword in node.keywords:
            if keyword.arg in {"size", "pos", "width", "height"} and contains_unprotected_division(keyword.value):
                findings.append((node.lineno, f"argument {keyword.arg} potentiellement flottant dans {call_name(node)}()"))
                break
    return sorted(set(findings))


def scan(path: Path) -> list[tuple[int, str]]:
    session = SourceAuditSession([path])
    loaded = session.parse(path)
    if loaded is None:
        raise RuntimeError(session.coverage.failures[0].format())
    _source, tree = loaded
    return scan_tree(tree)


def main() -> int:
    session = SourceAuditSession(iter_python_files(ROOT))
    total = 0
    for path in session.paths:
        loaded = session.parse(path)
        if loaded is None:
            continue
        _source, tree = loaded
        for lineno, message in scan_tree(tree):
            total += 1
            print(f"{path}:{lineno}: {message}")
    print(f"\n{total} argument(s) wxPython potentiellement flottant(s).")
    if not session.report():
        print("Audit incomplet : inventaire wx numérique non exhaustif.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
