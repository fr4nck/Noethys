#!/usr/bin/env python3
"""Repère les usages XML dont l'encodage doit être vérifié sous Python 3."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "noethys")
SKIP_DIRS = {".git", ".venv", "venv", "build", "dist", "__pycache__"}
XML_CALLS = {
    "ElementTree.write", "ET.write", "tree.write", "etree.tostring",
    "etree.parse", "xml.etree.ElementTree.parse", "minidom.parse",
    "minidom.parseString", "xml.dom.minidom.parse", "xml.dom.minidom.parseString",
}


def call_name(node: ast.Call) -> str:
    func = node.func
    parts: list[str] = []
    while isinstance(func, ast.Attribute):
        parts.append(func.attr)
        func = func.value
    if isinstance(func, ast.Name):
        parts.append(func.id)
    return ".".join(reversed(parts))


def main() -> int:
    findings = 0
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, UnicodeError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = call_name(node)
            if name not in XML_CALLS and not name.endswith((".write", ".tostring", ".parse", ".parseString")):
                continue
            keywords = {kw.arg for kw in node.keywords if kw.arg}
            detail = []
            if name.endswith((".write", ".tostring")) and "encoding" not in keywords:
                detail.append("encoding absent")
            if name.endswith(".write") and "xml_declaration" not in keywords:
                detail.append("déclaration XML implicite")
            if detail:
                findings += 1
                print(f"{path}:{node.lineno}: {name} : {', '.join(detail)}")
    print(f"\n{findings} frontière(s) XML à examiner.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
