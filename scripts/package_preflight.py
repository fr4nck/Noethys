#!/usr/bin/env python3
"""Exécute les contrôles légers avant tout packaging Windows."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CHECKS = (
    ("Dépendances", [sys.executable, "scripts/audit_dependency_usage.py", "noethys", "requirements.txt"]),
    ("Compatibilité Python 3", [sys.executable, "scripts/audit_python3_compat.py", "noethys"]),
    ("API modernes", [sys.executable, "scripts/audit_modern_api_compat.py", "noethys"]),
    ("Compilation", [sys.executable, "-m", "compileall", "-q", "noethys"]),
)


def main() -> int:
    for label, command in CHECKS:
        print(f"\n== {label} ==")
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode != 0:
            print(f"Échec du préflight : {label}", file=sys.stderr)
            return result.returncode
    print("\nPréflight terminé avec succès.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
