#!/usr/bin/env python3
"""Inventorie les motifs Python 2/anciens encore présents dans le code Noethys.

Audit informatif uniquement : il ne modifie aucun fichier et retourne toujours 0.
"""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

PATTERNS = {
    "PY2_PRINT": re.compile(r"^\s*print\s+[^\(]"),
    "PY2_EXCEPT": re.compile(r"except\s+[^:]+,\s*\w+\s*:"),
    "PY2_RAISE": re.compile(r"raise\s+\w+\s*,"),
    "PY2_XRANGE": re.compile(r"\bxrange\s*\("),
    "PY2_ITERITEMS": re.compile(r"\.(?:iteritems|iterkeys|itervalues)\s*\("),
    "PY2_RAW_INPUT": re.compile(r"\braw_input\s*\("),
    "PY2_UNICODE": re.compile(r"\bunicode\s*\("),
    "PY2_BASESTRING": re.compile(r"\bbasestring\b"),
    "PY2_LONG": re.compile(r"\blong\s*\("),
    "PY2_IMPORTS": re.compile(r"\b(?:ConfigParser|cPickle|cStringIO|Queue|urllib2|urlparse|StringIO)\b"),
    "PY2_SHELVE": re.compile(r"\b(?:anydbm|dbhash)\b"),
    "PY2_HAS_KEY": re.compile(r"\.has_key\s*\("),
    "PY2_CMP": re.compile(r"\bcmp\s*\("),
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

    for path in iter_python_files(root):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            if line.lstrip().startswith("#"):
                continue
            for name, pattern in PATTERNS.items():
                if pattern.search(line):
                    counts[name] += 1
                    print(f"{name}: {path}:{lineno}: {line.strip()}")

    print("\nRésumé")
    for name in PATTERNS:
        print(f"- {name}: {counts[name]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
