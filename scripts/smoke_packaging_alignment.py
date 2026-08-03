#!/usr/bin/env python3
"""Vérifie la cohérence entre dépendances, tests et spec PyInstaller.

Ce contrôle statique empêche qu'une pile obligatoire soit déclarée dans
requirements.txt mais oubliée du packaging ou des smoke-tests.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"
SPEC = ROOT / "packaging" / "noethys.spec"
IMPORT_SMOKE = ROOT / "scripts" / "smoke_import_dependencies.py"
STACK_SMOKE = ROOT / "scripts" / "smoke_optional_feature_stacks.py"

# Paquet PyPI -> marqueur attendu dans le spec ou les tests.
CRITICAL = {
    "Pillow": "PIL",
    "pycryptodome": "Crypto",
    "reportlab": "reportlab",
    "Twisted": "twisted",
    "paramiko": "paramiko",
    "lxml": "lxml",
    "matplotlib": "matplotlib",
    "sqlalchemy": "sqlalchemy",
    "mysql-connector-python": "mysql.connector",
    "pyttsx3": "pyttsx3",
    "pytz": "pytz",
    "icalendar": "icalendar",
    "python-dateutil": "dateutil",
    "comtypes": "comtypes",
    "XlsxWriter": "xlsxwriter",
}


def declared_packages() -> set[str]:
    packages: set[str] = set()
    for raw in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        name = re.split(r"[<>=!~;\[]", line, maxsplit=1)[0].strip()
        packages.add(name.lower())
    return packages


def main() -> int:
    spec_text = SPEC.read_text(encoding="utf-8")
    smoke_text = (
        IMPORT_SMOKE.read_text(encoding="utf-8")
        + "\n"
        + STACK_SMOKE.read_text(encoding="utf-8")
    )
    declared = declared_packages()
    failures = 0

    for package, marker in CRITICAL.items():
        if package.lower() not in declared:
            print(f"- {package}: absent de requirements.txt")
            failures += 1
            continue
        if marker not in spec_text:
            print(f"- {package}: marqueur PyInstaller absent ({marker})")
            failures += 1
            continue
        if marker not in smoke_text:
            print(f"- {package}: aucun smoke-test associé ({marker})")
            failures += 1
            continue
        print(f"- {package}: cohérent")

    if failures:
        print(f"\n{failures} incohérence(s) de packaging.", file=sys.stderr)
        return 1
    print("\nDépendances critiques, smoke-tests et spec PyInstaller sont alignés.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
