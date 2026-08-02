#!/usr/bin/env python3
"""Inventorie les API anciennes susceptibles de casser avec le runtime moderne.

Le script reste informatif : il ne modifie rien et ne fait pas échouer la CI.
Les motifs sont volontairement conservateurs afin d'éviter de signaler tous les
appels ``execute()`` du projet comme des usages SQLAlchemy incompatibles.
"""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

PATTERNS = {
    "WX_EMPTY": re.compile(r"\bwx\.(?:EmptyBitmap|EmptyIcon|EmptyImage)\b"),
    "WX_NEWID": re.compile(r"\bwx\.NewId\s*\("),
    "WX_PYDEPRECATED": re.compile(r"\bwx\.Py(?:SimpleApp|Validator|Control|Window)\b"),
    "WX_BITMAPFROMIMAGE": re.compile(r"\bwx\.BitmapFromImage\b"),
    "WX_SETFONT_POINTSIZE_FLOAT": re.compile(r"\.SetPointSize\s*\([^\n]*(?:/|\.\d)"),
    "PIL_ANTIALIAS": re.compile(r"\bImage\.ANTIALIAS\b"),
    "PIL_TOSTRING": re.compile(r"\.(?:tostring|fromstring)\s*\("),
    "PIL_RESAMPLING_LEGACY": re.compile(r"\bImage\.(?:NEAREST|BILINEAR|BICUBIC|LANCZOS)\b"),
    # SQLAlchemy 2 retire Engine.execute(). On ne cible que les récepteurs dont
    # le nom indique explicitement un moteur SQLAlchemy, afin d'éviter les
    # curseurs sqlite/mysql et les nombreux objets métier possédant execute().
    "SQLA_ENGINE_EXECUTE": re.compile(
        r"\b(?:engine|sqlalchemy_engine|db_engine|self\.engine)\.execute\s*\("
    ),
    "SQLA_AUTOCOMMIT": re.compile(r"\b(?:create_engine|sessionmaker)\s*\([^\n]*\bautocommit\s*="),
    "SQLA_LEGACY_SELECT_LIST": re.compile(r"\bselect\s*\(\s*\["),
}

SKIP_DIRS = {
    ".git",
    "build",
    "dist",
    "__pycache__",
    "venv",
    ".venv",
    # Bibliothèques historiques embarquées : leur modernisation doit être
    # qualifiée séparément du code Noethys.
    "ObjectListView",
    "wxScheduler",
}


def iter_python_files(root: Path):
    for path in root.rglob("*.py"):
        if not any(part in SKIP_DIRS for part in path.parts):
            yield path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default="noethys")
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="N'afficher que les compteurs par catégorie.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    counts: Counter[str] = Counter()
    findings: list[tuple[str, Path, int, str]] = []

    for path in iter_python_files(root):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for name, pattern in PATTERNS.items():
                if pattern.search(line):
                    counts[name] += 1
                    findings.append((name, path, lineno, stripped))

    if not args.summary_only:
        for name, path, lineno, line in findings:
            print(f"{name}: {path}:{lineno}: {line}")

    print("\nRésumé")
    for name in PATTERNS:
        print(f"- {name}: {counts[name]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
