#!/usr/bin/env python3
"""Vérifie que les fichiers texte du dépôt sont réellement encodés en UTF-8.

Le contrôle ignore les répertoires générés et les formats binaires. Il refuse
les fichiers impossibles à décoder en UTF-8 et signale les BOM UTF-8 afin de
garder un encodage homogène et prévisible sous Python 3 et Windows.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {
    ".git",
    ".github",
    ".venv",
    "venv",
    "build",
    "dist",
    "__pycache__",
}
TEXT_SUFFIXES = {
    ".py",
    ".pyw",
    ".spec",
    ".txt",
    ".md",
    ".rst",
    ".json",
    ".ini",
    ".cfg",
    ".conf",
    ".csv",
    ".tsv",
    ".xml",
    ".xsd",
    ".html",
    ".htm",
    ".css",
    ".js",
    ".sql",
    ".yaml",
    ".yml",
    ".toml",
    ".po",
    ".pot",
}
TEXT_FILENAMES = {
    "requirements.txt",
    "Dockerfile",
    "Makefile",
    "LICENSE",
    "COPYING",
}
UTF8_BOM = b"\xef\xbb\xbf"


def is_candidate(path: Path) -> bool:
    if not path.is_file():
        return False
    if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
        return False
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in TEXT_FILENAMES


def main() -> int:
    failures = 0
    checked = 0
    for path in sorted(ROOT.rglob("*")):
        if not is_candidate(path):
            continue
        checked += 1
        try:
            raw = path.read_bytes()
        except OSError as err:
            failures += 1
            print(f"{path.relative_to(ROOT)}: lecture impossible: {err}")
            continue

        if raw.startswith(UTF8_BOM):
            failures += 1
            print(f"{path.relative_to(ROOT)}: BOM UTF-8 détecté")
            continue

        try:
            raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as err:
            failures += 1
            print(
                f"{path.relative_to(ROOT)}: encodage non UTF-8 "
                f"(octet {err.start}: {err.reason})"
            )

    print(f"\n{checked} fichier(s) texte vérifié(s).")
    if failures:
        print(f"{failures} fichier(s) non conformes UTF-8.", file=sys.stderr)
        return 1
    print("Tous les fichiers texte contrôlés sont en UTF-8 sans BOM.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
