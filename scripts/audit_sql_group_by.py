#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repère les requêtes SQL potentiellement fragiles avec ONLY_FULL_GROUP_BY.

Cet audit est volontairement conservateur : il ne modifie rien et ne prétend pas
valider la sémantique SQL. Il sert de liste de travail reproductible pour la
modernisation de Noethys, en particulier lors du maintien de la compatibilité
avec les anciennes bases MySQL/MariaDB.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

SQL_BLOCK_RE = re.compile(r'([ruRU]{0,2})?(["\']{3})(.*?)(?:\2)', re.DOTALL)
GROUP_BY_RE = re.compile(r'\bGROUP\s+BY\b', re.IGNORECASE)
SELECT_RE = re.compile(r'\bSELECT\b(.*?)\bFROM\b', re.IGNORECASE | re.DOTALL)
AGGREGATE_RE = re.compile(r'\b(?:SUM|COUNT|AVG|MIN|MAX|GROUP_CONCAT)\s*\(', re.IGNORECASE)


def iter_python_files(root: Path):
    for path in root.rglob('*.py'):
        if any(part in {'.git', '.venv', 'venv', '__pycache__'} for part in path.parts):
            continue
        yield path


def line_number(text: str, offset: int) -> int:
    return text.count('\n', 0, offset) + 1


def classify(sql: str) -> str:
    match = SELECT_RE.search(sql)
    select_part = match.group(1) if match else ''
    if AGGREGATE_RE.search(select_part):
        return 'aggregation'
    return 'group-by-without-visible-aggregate'


def scan_file(path: Path):
    try:
        text = path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        text = path.read_text(encoding='utf-8', errors='replace')

    findings = []
    for block in SQL_BLOCK_RE.finditer(text):
        sql = block.group(3)
        if not GROUP_BY_RE.search(sql):
            continue
        findings.append((line_number(text, block.start()), classify(sql), sql))
    return findings


def compact_sql(sql: str, limit: int = 220) -> str:
    value = ' '.join(sql.split())
    return value if len(value) <= limit else value[: limit - 3] + '...'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('root', nargs='?', default='noethys', help='Répertoire à auditer')
    parser.add_argument('--fail-on-findings', action='store_true', help='Retourne 1 si des GROUP BY sont trouvés')
    args = parser.parse_args()

    root = Path(args.root)
    total = 0
    suspicious = 0

    for path in iter_python_files(root):
        for lineno, category, sql in scan_file(path):
            total += 1
            if category == 'group-by-without-visible-aggregate':
                suspicious += 1
            print(f'{path}:{lineno}: {category}: {compact_sql(sql)}')

    print(f'\nGROUP BY trouvés: {total}')
    print(f'Sans agrégat visible dans SELECT: {suspicious}')
    print('Note: chaque résultat doit être revu manuellement avant modification.')

    if args.fail_on_findings and total:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
