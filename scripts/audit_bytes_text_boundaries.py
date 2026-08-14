#!/usr/bin/env python3
"""Repère les mélanges bytes/str susceptibles de casser Noethys sous Python 3.

Audit informatif uniquement. Il cible surtout les valeurs encodées envoyées à
wxPython, les chemins encodés et les écritures texte/binaire incohérentes.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "noethys")
WX_TEXT_METHODS = {
    "SetValue", "ChangeValue", "AppendText", "WriteText", "SetLabel",
    "SetTitle", "SetStatusText", "SetToolTip", "SetHelpText",
}
PATH_METHODS = {
    "open", "exists", "isfile", "isdir", "join", "basename", "dirname",
    "abspath", "normpath", "remove", "unlink", "rename", "replace",
}


def call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def is_encode_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "encode"
    )


def contains_bytes_literal(node: ast.AST) -> bool:
    return any(isinstance(child, ast.Constant) and isinstance(child.value, bytes) for child in ast.walk(node))


def scan(path: Path) -> list[tuple[int, str]]:
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    findings: set[tuple[int, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node)
        if name in WX_TEXT_METHODS:
            for arg in node.args:
                if is_encode_call(arg) or contains_bytes_literal(arg):
                    findings.add((node.lineno, f"bytes envoyés à wxPython via {name}()"))
        if name in PATH_METHODS:
            for arg in node.args:
                if is_encode_call(arg) or contains_bytes_literal(arg):
                    findings.add((node.lineno, f"chemin potentiellement encodé via {name}()"))
        if name == "write" and node.args:
            arg = node.args[0]
            if is_encode_call(arg):
                findings.add((node.lineno, "écriture de bytes à vérifier selon le mode du fichier"))

    return sorted(findings)


def main() -> int:
    total = 0
    for path in sorted(ROOT.rglob("*.py")):
        for lineno, message in scan(path):
            total += 1
            print(f"{path}:{lineno}: {message}")
    print(f"\n{total} frontière(s) bytes/texte à examiner.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
