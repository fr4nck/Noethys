#!/usr/bin/env python3
"""Bloque les modifications de schéma SQL ajoutées silencieusement au code Noethys.

Le contrôle porte uniquement sur les lignes ajoutées entre deux révisions Git.
Les tests et outils qui construisent des bases jetables sont hors périmètre :
ils ne modifient ni le schéma applicatif ni une base utilisateur existante.
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
# Outils explicitement destinés à fabriquer des bases temporaires de recette.
IGNORED_PATHS = {
    "scripts/build_synthetic_recette_db.py",
    "scripts/qualify_noe032_mysql.py",
}
IGNORED_PREFIXES = ("tests/",)


def is_ignored_path(filename: str) -> bool:
    return filename in IGNORED_PATHS or any(filename.startswith(prefix) for prefix in IGNORED_PREFIXES)


def is_qualified_ephemeral_sql(filename: str, line: str) -> bool:
    """Ignore uniquement le marqueur de fin NOE-032c, créé puis supprimé pendant une restauration."""
    if filename != "noethys/Utils/UTILS_Sauvegarde.py":
        return False
    return (
        "CREATE TABLE %s (`jeton` CHAR(32) NOT NULL PRIMARY KEY)" in line
        or (
            "DROP TABLE IF EXISTS %s" in line
            and '_QuoteIdentifiantMySQL(marqueur["table"])' in line
        )
    )


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
        if is_ignored_path(current_file):
            continue
        if current_file and Path(current_file).suffix.lower() in TEXT_SUFFIXES:
            additions.append((current_file, line[1:]))

    return additions


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: check_schema_compatibility.py <base> <head>", file=sys.stderr)
        return 2

    findings: list[tuple[str, str]] = []
    for filename, line in added_lines(sys.argv[1], sys.argv[2]):
        if is_qualified_ephemeral_sql(filename, line):
            continue
        if any(pattern.search(line) for pattern in SCHEMA_PATTERNS):
            findings.append((filename, line.strip()))

    if findings:
        print("Modification potentielle du schéma de base détectée :", file=sys.stderr)
        for filename, line in findings:
            print(f"- {filename}: {line}", file=sys.stderr)
        print(
            "Isolez cette évolution dans une migration explicitement revue, "
            "ou supprimez la modification afin de préserver la cohabitation des versions.",
            file=sys.stderr,
        )
        return 1

    print("Aucune modification du schéma applicatif SQL ajoutée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
