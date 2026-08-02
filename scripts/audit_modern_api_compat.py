#!/usr/bin/env python3
"""Inventorie les API anciennes susceptibles de casser avec le runtime moderne.

Ce script est informatif : il ne modifie rien et ne fait pas échouer la CI.
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
    "PIL_ANTIALIAS": re.compile(r"\bImage\.ANTIALIAS\b"),
    "PIL_TOSTRING": re.compile(r"\.(?:tostring|fromstring)\s*\("),
    "SQLA_ENGINE_EXECUTE": re.compile(r"\.execute\s*\("),
    "SQLA_AUTOCOMMIT": re.compile(r"\bautocommit\s*="),
}

SKIP_DIRS = {".git", "build", "dist", "__pycache__", "venv", ".venv"}


def iter_python_files(root: Path):
    for path in root.rglob("*.py"):
        if not any(part in SKIP_DIRS for part in path.parts):
            yield path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default="noethys")
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
            for name, pattern in PATTERNS.items():
                if pattern.search(line):
                    counts[name] += 1
                    findings.append((name, path, lineno, line.strip()))

    for name, path, lineno, line in findings:
        print(f"{name}: {path}:{lineno}: {line}")

    print("\nRésumé")
    for name in PATTERNS:
        print(f"- {name}: {counts[name]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
