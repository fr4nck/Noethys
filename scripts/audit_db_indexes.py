#!/usr/bin/env python3
"""Audit Noethys database indexes without modifying a database.

Default mode parses the index declarations in noethys/Data/DATA_Tables.py.
With --sqlite, the tool opens an existing SQLite database in read-only mode and
compares its indexes with a small set of query-driven candidates.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
DATA_TABLES = ROOT / "noethys" / "Data" / "DATA_Tables.py"

INDEX_RE = re.compile(
    r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?P<name>[A-Za-z0-9_]+)\s+"
    r"ON\s+(?P<table>[A-Za-z0-9_]+)\s*\((?P<columns>[^)]+)\)",
    re.IGNORECASE,
)

# Candidates identified by the Noe-003/Noe-004 static query audit.
# They are observations to measure, never automatic migration instructions.
CANDIDATES: Sequence[Tuple[str, Tuple[str, ...], str]] = (
    (
        "cotisations",
        ("IDprestation",),
        "Quadra/Cerig lookup and deterministic cotisation subquery",
    ),
    (
        "prestations",
        ("IDfacture",),
        "invoice/export joins and grouping paths",
    ),
    (
        "ventilation",
        ("IDprestation",),
        "queries that enter ventilation from a prestation",
    ),
    (
        "prestations",
        ("IDfamille",),
        "family-scoped prestation lookups; benchmark before adding",
    ),
    (
        "prestations",
        ("IDactivite",),
        "activity-scoped prestation lookups; benchmark before adding",
    ),
)


def normalize_columns(raw: Iterable[str]) -> Tuple[str, ...]:
    return tuple(column.strip().strip("`\"").lower() for column in raw if column.strip())


def parse_declared_indexes(path: Path = DATA_TABLES) -> Dict[str, List[Tuple[str, Tuple[str, ...]]]]:
    text = path.read_text(encoding="utf-8")
    indexes: Dict[str, List[Tuple[str, Tuple[str, ...]]]] = {}
    for match in INDEX_RE.finditer(text):
        table = match.group("table").lower()
        columns = normalize_columns(match.group("columns").split(","))
        indexes.setdefault(table, []).append((match.group("name"), columns))
    return indexes


def sqlite_indexes(path: Path) -> Dict[str, List[Tuple[str, Tuple[str, ...]]]]:
    uri = path.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        result: Dict[str, List[Tuple[str, Tuple[str, ...]]]] = {}
        for table in tables:
            quoted_table = table.replace("'", "''")
            for row in connection.execute("PRAGMA index_list('%s')" % quoted_table):
                index_name = row[1]
                quoted_index = index_name.replace("'", "''")
                columns = normalize_columns(
                    info[2]
                    for info in connection.execute("PRAGMA index_info('%s')" % quoted_index)
                    if info[2] is not None
                )
                result.setdefault(table.lower(), []).append((index_name, columns))
        return result
    finally:
        connection.close()


def covers(
    indexes: Dict[str, List[Tuple[str, Tuple[str, ...]]]],
    table: str,
    required_columns: Sequence[str],
) -> bool:
    required = normalize_columns(required_columns)
    for _name, columns in indexes.get(table.lower(), []):
        if columns[: len(required)] == required:
            return True
    return False


def print_indexes(title: str, indexes: Dict[str, List[Tuple[str, Tuple[str, ...]]]]) -> None:
    print(title)
    for table in sorted(indexes):
        for name, columns in sorted(indexes[table]):
            print("  %-28s %-24s %s" % (name, table, ", ".join(columns)))
    print()


def print_candidates(indexes: Dict[str, List[Tuple[str, Tuple[str, ...]]]]) -> int:
    missing = 0
    print("Query-driven candidates")
    for table, columns, reason in CANDIDATES:
        present = covers(indexes, table, columns)
        state = "covered" if present else "MISSING/TO MEASURE"
        if not present:
            missing += 1
        print("  %-18s %-24s %-18s %s" % (state, table, ", ".join(columns), reason))
    print()
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sqlite",
        type=Path,
        help="Optional existing SQLite database to inspect in mode=ro (no writes).",
    )
    args = parser.parse_args()

    declared = parse_declared_indexes()
    print_indexes("Indexes declared by DATA_Tables.py", declared)
    declared_missing = print_candidates(declared)
    print("Declared candidates still requiring measurement: %d" % declared_missing)

    if args.sqlite is not None:
        if not args.sqlite.is_file():
            parser.error("SQLite database does not exist: %s" % args.sqlite)
        actual = sqlite_indexes(args.sqlite)
        print()
        print_indexes("Indexes present in SQLite database (read-only)", actual)
        actual_missing = print_candidates(actual)
        print("Database candidates still requiring measurement: %d" % actual_missing)

    print("\nAudit only: no CREATE INDEX statement was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
