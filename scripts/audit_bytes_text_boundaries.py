#!/usr/bin/env python3
"""Repère les mélanges bytes/str susceptibles de casser Noethys sous Python 3.

Audit informatif sur les occurrences, mais bloquant sur sa couverture. Il cible
surtout les valeurs encodées envoyées à wxPython, les chemins encodés et les
écritures texte/binaire incohérentes.
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
WX_TEXT_METHODS = {
    "SetValue", "ChangeValue", "AppendText", "WriteText", "SetLabel",
    "SetTitle", "SetStatusText", "SetToolTip", "SetHelpText",
}
PATH_METHODS = {
    "open", "exists", "isfile", "isdir", "join", "basename", "dirname",
    "abspath", "normpath", "remove", "unlink", "rename",
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


def is_bytesio_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id == "BytesIO"
    if isinstance(func, ast.Attribute):
        return func.attr == "BytesIO"
    return False


def bytesio_names(tree: ast.AST) -> set[str]:
    """Noms locaux initialisés avec BytesIO()/six.BytesIO()/io.BytesIO()."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        value = node.value
        if value is None or not is_bytesio_call(value):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name):
                names.add(target.id)
    return names


def is_write_to_known_bytesio(node: ast.Call, known: set[str]) -> bool:
    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "write"
        and isinstance(func.value, ast.Name)
        and func.value.id in known
    )


def scan_tree(tree: ast.AST) -> list[tuple[int, str]]:
    known_bytesio = bytesio_names(tree)
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
            if is_encode_call(arg) and not is_write_to_known_bytesio(node, known_bytesio):
                findings.add((node.lineno, "écriture de bytes à vérifier selon le mode du fichier"))

    return sorted(findings)


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
    print(f"\n{total} frontière(s) bytes/texte à examiner.")
    if not session.report():
        print("Audit incomplet : inventaire bytes/texte non exhaustif.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
