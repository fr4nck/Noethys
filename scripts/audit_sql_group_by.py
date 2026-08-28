#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repère les requêtes SQL potentiellement fragiles avec ONLY_FULL_GROUP_BY.

Cet audit est volontairement conservateur : il ne modifie rien et ne prétend pas
valider la sémantique SQL. Il sert de liste de travail reproductible pour la
modernisation de Noethys. Les occurrences restent informatives ; la couverture
des sources Python est bloquante.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

try:
    from scripts.audit_source_coverage import SourceAuditSession, iter_python_files
except ModuleNotFoundError:
    from audit_source_coverage import SourceAuditSession, iter_python_files

SQL_BLOCK_RE = re.compile(r'([ruRU]{0,2})?(["\']{3})(.*?)(?:\2)', re.DOTALL)
GROUP_BY_RE = re.compile(r'\bGROUP\s+BY\b', re.IGNORECASE)
SELECT_RE = re.compile(r'\bSELECT\b(.*?)\bFROM\b', re.IGNORECASE | re.DOTALL)
AGGREGATE_RE = re.compile(r'\b(?:SUM|COUNT|AVG|MIN|MAX|GROUP_CONCAT)\s*\(', re.IGNORECASE)
SKIP_DIRS = {'.git', '.venv', 'venv', '__pycache__'}


def line_number(text: str, offset: int) -> int:
    return text.count('\n', 0, offset) + 1


def classify(sql: str) -> str:
    match = SELECT_RE.search(sql)
    select_part = match.group(1) if match else ''
    if AGGREGATE_RE.search(select_part):
        return 'aggregation'
    return 'group-by-without-visible-aggregate'


def scan_text(text: str):
    findings = []
    for block in SQL_BLOCK_RE.finditer(text):
        sql = block.group(3)
        if not GROUP_BY_RE.search(sql):
            continue
        findings.append((line_number(text, block.start()), classify(sql), sql))
    return findings


def scan_file(path: Path):
    session = SourceAuditSession([path])
    loaded = session.parse(path)
    session.require_complete()
    assert loaded is not None
    text, _tree = loaded
    return scan_text(text)


def compact_sql(sql: str, limit: int = 220) -> str:
    value = ' '.join(sql.split())
    return value if len(value) <= limit else value[: limit - 3] + '...'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('root', nargs='?', default='noethys', help='Répertoire à auditer')
    parser.add_argument('--fail-on-findings', action='store_true', help='Retourne 1 si des GROUP BY sont trouvés')
    args = parser.parse_args()

    root = Path(args.root)
    session = SourceAuditSession(iter_python_files(root, skip_dirs=SKIP_DIRS))
    total = 0
    suspicious = 0

    for path in session.paths:
        loaded = session.parse(path)
        if loaded is None:
            continue
        text, _tree = loaded
        for lineno, category, sql in scan_text(text):
            total += 1
            if category == 'group-by-without-visible-aggregate':
                suspicious += 1
            print(f'{path}:{lineno}: {category}: {compact_sql(sql)}')

    print(f'\nGROUP BY trouvés: {total}')
    print(f'Sans agrégat visible dans SELECT: {suspicious}')
    print('Note: chaque résultat doit être revu manuellement avant modification.')
    session.report(prefix='Couverture audit SQL GROUP BY')
    session.require_complete()

    if args.fail_on_findings and total:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
