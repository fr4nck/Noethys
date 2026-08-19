#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Noe-001 - Audit SQL strict

Recherche les motifs SQL potentiellement sensibles pour MySQL/MariaDB
avec ONLY_FULL_GROUP_BY activé.

Ce script ne modifie aucun fichier. Il sert à préparer l'audit manuel.
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

PATTERNS = {
    "group_by": re.compile(r"GROUP\\s+BY", re.IGNORECASE),
    "select": re.compile(r"SELECT\\s+", re.IGNORECASE),
    "having": re.compile(r"HAVING\\s+", re.IGNORECASE),
}


def scan_file(path):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    findings = []
    for name, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append((name, line))
    return findings


def main():
    total = 0
    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        findings = scan_file(path)
        if findings:
            print(path.relative_to(ROOT))
            for kind, line in findings:
                print(f"  - {kind}: line {line}")
                total += 1

    print(f"\nTotal findings: {total}")


if __name__ == "__main__":
    main()
