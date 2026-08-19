#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Noe-001 - Audit SQL strict

Analyse les fichiers Python pour identifier les zones SQL sensibles
(MySQL/MariaDB avec ONLY_FULL_GROUP_BY).

Le script ne modifie aucun fichier.
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

PATTERNS = {
    "sql_select": re.compile(r"\bSELECT\b", re.IGNORECASE),
    "group_by": re.compile(r"\bGROUP\s+BY\b", re.IGNORECASE),
    "having": re.compile(r"\bHAVING\b", re.IGNORECASE),
    "executer_req": re.compile(r"ExecuterReq\s*\(", re.IGNORECASE),
    "req_select": re.compile(r"ReqSelect\s*\(", re.IGNORECASE),
    "cursor_execute": re.compile(r"\.execute\s*\(", re.IGNORECASE),
}

SQL_CONTEXT = re.compile(r"(?:SELECT|FROM|JOIN|GROUP\s+BY|HAVING|WHERE).{0,120}", re.IGNORECASE | re.DOTALL)


def scan_file(path):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    findings = []
    for name, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            context = text[match.start():match.start() + 160].replace("\n", " ")
            findings.append((name, line, context))
    return findings


def main():
    total = 0
    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue

        findings = scan_file(path)
        if findings:
            print(path.relative_to(ROOT))
            for kind, line, context in findings:
                print(f"  - {kind}: line {line}")
                print(f"    {context}")
                total += 1

    print(f"\nTotal findings: {total}")


if __name__ == "__main__":
    main()
