#!/usr/bin/env python3
"""Vérifie que les dépendances critiques du package sont importables.

Le test ne se connecte à aucune base et n'ouvre aucune interface. Il identifie
uniquement les modules absents ou incompatibles avant le lancement de
PyInstaller.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))

REQUIRED = (
    "wx",
    "PIL.Image",
    "sqlalchemy",
    "matplotlib",
    "reportlab",
    "lxml",
    "dateutil",
    "pytz",
    "icalendar",
    "paramiko",
    "Crypto",
    "pyttsx3",
    "mysql.connector",
    "comtypes",
    "xlsxwriter",
    "anydbm",
    "dbhash",
)

OPTIONAL = (
    "MySQLdb",
    "cv2",
    "twisted",
)


def check(module_name: str) -> tuple[bool, str]:
    try:
        importlib.import_module(module_name)
    except Exception as err:  # diagnostic volontairement large
        return False, f"{type(err).__name__}: {err}"
    return True, "ok"


def main() -> int:
    failures = 0
    print("Dépendances obligatoires")
    for module_name in REQUIRED:
        ok, detail = check(module_name)
        print(f"- {module_name}: {detail}")
        if not ok:
            failures += 1

    print("\nDépendances optionnelles")
    for module_name in OPTIONAL:
        _, detail = check(module_name)
        print(f"- {module_name}: {detail}")

    if failures:
        print(f"\n{failures} dépendance(s) obligatoire(s) non importable(s).", file=sys.stderr)
        return 1
    print("\nToutes les dépendances obligatoires sont importables.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
