#!/usr/bin/env python3
"""Inventorie les usages Pillow et ReportLab fragiles sous Python moderne.

Le contrôle est informatif. Il cible les constantes Pillow supprimées ou
obsolètes, les redimensionnements sans stratégie explicite, les polices
ReportLab chargées depuis des chemins fragiles et les sorties PDF dont le nom
ou le chemin est potentiellement encodé en bytes.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "noethys")
SKIP_DIRS = {".git", ".venv", "__pycache__", "build", "dist", "venv"}

PILLOW_CONSTANTS = {
    "Image.ANTIALIAS": "utiliser Image.Resampling.LANCZOS",
    "Image.NEAREST": "préférer Image.Resampling.NEAREST",
    "Image.BILINEAR": "préférer Image.Resampling.BILINEAR",
    "Image.BICUBIC": "préférer Image.Resampling.BICUBIC",
    "Image.LANCZOS": "préférer Image.Resampling.LANCZOS",
}
REPORTLAB_CALLS = {
    "TTFont",
    "pdfmetrics.registerFont",
    "canvas.Canvas",
    "SimpleDocTemplate",
    "BaseDocTemplate",
}


def dotted_name(node: ast.AST) -> str:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def is_bytes_expression(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return isinstance(node.value, bytes)
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "encode"


def scan(path: Path) -> list[tuple[int, str]]:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []

    findings: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            name = dotted_name(node)
            if name in PILLOW_CONSTANTS:
                findings.append((node.lineno, f"Pillow obsolète {name} : {PILLOW_CONSTANTS[name]}"))

        if not isinstance(node, ast.Call):
            continue
        name = dotted_name(node.func)

        if name.endswith(".resize") or name.endswith(".thumbnail"):
            if len(node.args) < 2 and not any(k.arg in {"resample", "reducing_gap"} for k in node.keywords):
                findings.append((node.lineno, f"{name} sans filtre de rééchantillonnage explicite"))

        if name in REPORTLAB_CALLS or any(name.endswith(f".{suffix}") for suffix in REPORTLAB_CALLS):
            for arg in node.args[:2]:
                if is_bytes_expression(arg):
                    findings.append((node.lineno, f"{name} reçoit un chemin ou nom encodé en bytes"))
            if name.endswith("TTFont") and len(node.args) >= 2:
                font_path = node.args[1]
                if isinstance(font_path, ast.Constant) and isinstance(font_path.value, str):
                    if not Path(font_path.value).suffix.lower() in {".ttf", ".otf", ".ttc"}:
                        findings.append((node.lineno, "TTFont utilise un chemin de police sans extension reconnue"))

    return sorted(set(findings))


def main() -> int:
    total = 0
    for path in sorted(ROOT.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        for lineno, message in scan(path):
            total += 1
            print(f"{path}:{lineno}: {message}")
    print(f"\n{total} point(s) Pillow/ReportLab à examiner.")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
