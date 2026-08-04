#!/usr/bin/env python3
"""Remplace les chemins SQLite encodés en bytes par des chemins Unicode natifs.

Le script est volontairement déterministe : il ne touche qu'aux appels
``sqlite3.connect(<expression>.encode('utf-8'))`` et conserve le reste du
fichier à l'identique. Par défaut il vérifie seulement ; utiliser ``--write``
pour appliquer la migration.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "noethys" / "GestionDB.py"


def find_replacements(source: str) -> list[tuple[int, int, str]]:
    tree = ast.parse(source)
    replacements: list[tuple[int, int, str]] = []
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))

    def absolute(line: int, column: int) -> int:
        return offsets[line - 1] + column

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        func = node.func
        if not (
            isinstance(func, ast.Attribute)
            and func.attr == "connect"
            and isinstance(func.value, ast.Name)
            and func.value.id == "sqlite3"
        ):
            continue
        argument = node.args[0]
        if not (
            isinstance(argument, ast.Call)
            and isinstance(argument.func, ast.Attribute)
            and argument.func.attr == "encode"
            and not argument.keywords
            and len(argument.args) <= 1
        ):
            continue
        if argument.args:
            codec = argument.args[0]
            if not isinstance(codec, ast.Constant) or str(codec.value).lower().replace("_", "-") != "utf-8":
                continue
        value = argument.func.value
        if not hasattr(value, "end_lineno"):
            continue
        start = absolute(argument.lineno, argument.col_offset)
        end = absolute(argument.end_lineno, argument.end_col_offset)
        replacement = ast.get_source_segment(source, value)
        if replacement is None:
            continue
        replacements.append((start, end, replacement))
    return sorted(replacements, reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="applique les remplacements")
    args = parser.parse_args()

    source = TARGET.read_text(encoding="utf-8")
    replacements = find_replacements(source)
    if not replacements:
        print("GestionDB.py utilise déjà des chemins Unicode natifs pour SQLite.")
        return 0

    print(f"{len(replacements)} appel(s) sqlite3.connect avec chemin encodé détecté(s).")
    if not args.write:
        print("Relancer avec --write pour appliquer la migration.")
        return 1

    updated = source
    for start, end, replacement in replacements:
        updated = updated[:start] + replacement + updated[end:]
    TARGET.write_text(updated, encoding="utf-8", newline="")
    print("Migration SQLite Unicode appliquée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
