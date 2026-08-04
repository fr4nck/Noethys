#!/usr/bin/env python3
"""Repère et modernise les constantes Pillow de rééchantillonnage supprimées.

Le mode par défaut ne modifie rien. ``--apply`` remplace uniquement les accès
``Image.<CONSTANTE>`` dont l'équivalent moderne est strictement identique :

- ``Image.NEAREST`` -> ``Image.Resampling.NEAREST``
- ``Image.BILINEAR`` -> ``Image.Resampling.BILINEAR``
- ``Image.BICUBIC`` -> ``Image.Resampling.BICUBIC``
- ``Image.LANCZOS`` -> ``Image.Resampling.LANCZOS``
- ``Image.ANTIALIAS`` -> ``Image.Resampling.LANCZOS``

Aucun appel ``resize`` ou ``thumbnail`` n'est modifié si le filtre n'est pas
explicite, afin de ne pas changer la qualité d'image par supposition.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT_DEFAULT = "noethys"
SKIP_DIRS = {".git", ".venv", "__pycache__", "build", "dist", "venv"}
MAPPING = {
    "NEAREST": "NEAREST",
    "BILINEAR": "BILINEAR",
    "BICUBIC": "BICUBIC",
    "LANCZOS": "LANCZOS",
    "ANTIALIAS": "LANCZOS",
}


def find_occurrences(source: str, filename: str) -> list[tuple[int, int, str]]:
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return []
    found: list[tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute):
            continue
        if not isinstance(node.value, ast.Name) or node.value.id != "Image":
            continue
        if node.attr not in MAPPING:
            continue
        if not hasattr(node, "end_col_offset"):
            continue
        found.append((node.lineno, node.col_offset, node.attr))
    return sorted(found)


def modernize_source(source: str, filename: str = "<memory>") -> tuple[str, int]:
    occurrences = find_occurrences(source, filename)
    if not occurrences:
        return source, 0
    lines = source.splitlines(keepends=True)
    changed = 0
    for lineno, col, old_name in sorted(occurrences, reverse=True):
        line = lines[lineno - 1]
        token = f"Image.{old_name}"
        position = line.find(token, col)
        if position < 0:
            continue
        replacement = f"Image.Resampling.{MAPPING[old_name]}"
        lines[lineno - 1] = line[:position] + replacement + line[position + len(token):]
        changed += 1
    return "".join(lines), changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=ROOT_DEFAULT)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    total = 0
    for path in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        source = path.read_text(encoding="utf-8")
        updated, changed = modernize_source(source, str(path))
        if not changed:
            continue
        total += changed
        if args.apply:
            path.write_text(updated, encoding="utf-8", newline="")
            print(f"{path}: {changed} constante(s) modernisée(s)")
        else:
            for lineno, _, old_name in find_occurrences(source, str(path)):
                print(f"{path}:{lineno}: Image.{old_name} -> Image.Resampling.{MAPPING[old_name]}")

    if args.apply:
        print(f"\n{total} constante(s) modernisée(s).")
        return 0
    print(f"\n{total} constante(s) Pillow à moderniser.")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
