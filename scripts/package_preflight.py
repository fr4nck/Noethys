#!/usr/bin/env python3
"""Exécute les contrôles légers avant tout packaging Windows."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CHECKS = (
    ("Dépendances", [sys.executable, "scripts/audit_dependency_usage.py", "noethys", "requirements.txt"], False),
    ("Compatibilité Python 3", [sys.executable, "scripts/audit_python3_compat.py", "noethys"], False),
    ("API modernes", [sys.executable, "scripts/audit_modern_api_compat.py", "noethys"], False),
    ("Imports critiques", [sys.executable, "scripts/smoke_import_dependencies.py"], True),
    ("Hooks runtime", [sys.executable, "scripts/smoke_runtime_hooks.py"], True),
    ("Compilation", [sys.executable, "-m", "compileall", "-q", "noethys"], True),
)


def main() -> int:
    warnings = 0
    for label, command, blocking in CHECKS:
        level = "bloquant" if blocking else "informatif"
        print(f"\n== {label} ({level}) ==")
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode == 0:
            continue
        if blocking:
            print(f"Échec bloquant du préflight : {label}", file=sys.stderr)
            return result.returncode
        warnings += 1
        print(
            f"Avertissement : l’audit {label} a retourné le code {result.returncode}, "
            "mais le packaging peut continuer.",
            file=sys.stderr,
        )

    if warnings:
        print(f"\nPréflight terminé avec {warnings} avertissement(s).")
    else:
        print("\nPréflight terminé sans erreur.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
