#!/usr/bin/env python3
"""Bloque les modifications de schéma SQL ajoutées silencieusement dans une PR.

Le contrôle porte uniquement sur les lignes ajoutées entre deux révisions Git.
Une évolution volontaire du schéma doit être isolée dans une PR dédiée et
explicitement exclue de ce garde-fou après revue.

Les fichiers de tests et les smoke tests sont ignorés : ils peuvent créer des
bases SQLite temporaires autonomes sans modifier le schéma métier de Noethys.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SCHEMA_PATTERNS = (
    re.compile(r"\bALTER\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bCREATE\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bRENAME\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\b", re.IGNORECASE),
    re.compile(r"\bDROP\s+INDEX\b", re.IGNORECASE),
    re.compile(r"\bPRAGMA\s+user_version\b", re.IGNORECASE),
)

TEXT_SUFFIXES = {".py", ".sql", ".txt", ".ini", ".cfg", ".json", ".yaml", ".yml"}
TEST_DIRECTORIES = {"test", "tests"}


def is_test_file(filename: str) -> bool:
    """Retourne True pour les tests isolés qui ne modifient pas le schéma métier."""
    path = Path(filename)
    if any(part.lower() in TEST_DIRECTORIES for part in path.parts):
        return True
    return path.name.lower().startswith(("test_", "smoke_"))


def added_lines(base: str, head: str) -> list[tuple[str, str]]:
    command = ["git", "diff", "--unified=0", f"{base}...{head}", "--"]
    completed = subprocess.run(command, check=True, text=True, capture_output=True)
    current_file = ""
    additions: list[tuple[str, str]] = []

    for line in completed.stdout.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            continue
        if not line.startswith("+") or line.startswith("+++"):
            continue
        if (
            current_file
            and not is_test_file(current_file)
            and Path(current_file).suffix.lower() in TEXT_SUFFIXES
        ):
            additions.append((current_file, line[1:]))

    return additions


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: check_schema_compatibility.py <base> <head>", file=sys.stderr)
        return 2

    findings: list[tuple[str, str]] = []
    for filename, line in added_lines(sys.argv[1], sys.argv[2]):
        if any(pattern.search(line) for pattern in SCHEMA_PATTERNS):
            findings.append((filename, line.strip()))

    if findings:
        print("Modification potentielle du schéma de base détectée :", file=sys.stderr)
        for filename, line in findings:
            print(f"- {filename}: {line}", file=sys.stderr)
        print(
            "Isolez cette évolution dans une PR de migration explicitement revue, "
            "ou supprimez la modification afin de préserver la cohabitation des versions.",
            file=sys.stderr,
        )
        return 1

    print("Aucune modification de schéma SQL ajoutée dans cette PR.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
