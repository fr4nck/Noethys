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
    "aggregate": re.compile(r"\b(SUM|COUNT|AVG|MIN|MAX)\s*\(", re.IGNORECASE),
    "executer_req": re.compile(r"ExecuterReq\s*\(", re.IGNORECASE),
    "req_select": re.compile(r"ReqSelect\s*\(", re.IGNORECASE),
    "cursor_execute": re.compile(r"\.execute\s*\(", re.IGNORECASE),
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
            context = text[max(0, match.start()-60):match.start()+180].replace("\n", " ")
            findings.append({
                "type": name,
                "line": line,
                "context": context,
            })
    return findings


def main():
    total = 0
    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue

        findings = scan_file(path)
        if findings:
            print(path.relative_to(ROOT))
            for item in findings:
                print(f"  - {item['type']}: line {item['line']}")
                print(f"    {item['context']}")
                total += 1

    print(f"\nTotal findings: {total}")


if __name__ == "__main__":
    main()
