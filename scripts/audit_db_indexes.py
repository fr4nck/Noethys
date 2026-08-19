#!/usr/bin/env python3
"""Audit Noethys database indexes without modifying a database.

Default mode parses the index declarations in ``noethys/Data/DATA_Tables.py``.
With ``--sqlite`` or ``--mysql-host``, the tool opens an existing database in
read-only usage and reports:

- indexes actually present ;
- coverage of query-driven index candidates ;
- EXPLAIN / EXPLAIN QUERY PLAN for representative lookups ;
- a small repeated SELECT timing using an existing non-null key value.

No CREATE/ALTER/DROP statement is ever executed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import statistics
import time
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
DATA_TABLES = ROOT / "noethys" / "Data" / "DATA_Tables.py"

INDEX_RE = re.compile(
    r"CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?P<name>[A-Za-z0-9_]+)\s+"
    r"ON\s+(?P<table>[A-Za-z0-9_]+)\s*\((?P<columns>[^)]+)\)",
    re.IGNORECASE,
)
SAFE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Observations à mesurer, jamais instructions de migration automatique.
CANDIDATES: Sequence[Tuple[str, Tuple[str, ...], str]] = (
    (
        "cotisations",
        ("IDprestation",),
        "export comptable et invariant cotisation/prestation",
    ),
    (
        "prestations",
        ("IDfacture",),
        "jointures et regroupements de facturation",
    ),
    (
        "ventilation",
        ("IDprestation",),
        "accès à la ventilation depuis une prestation",
    ),
    (
        "prestations",
        ("IDfamille",),
        "consultations de prestations par famille",
    ),
    (
        "prestations",
        ("IDactivite",),
        "consultations de prestations par activité",
    ),
)


def normalize_columns(raw: Iterable[str]) -> Tuple[str, ...]:
    return tuple(column.strip().strip("`\"").lower() for column in raw if column.strip())


def safe_identifier(value: str) -> str:
    if not SAFE_IDENTIFIER_RE.match(value):
        raise ValueError("Identifiant SQL refusé: %r" % value)
    return value


def parse_declared_indexes(path: Path = DATA_TABLES) -> Dict[str, List[Tuple[str, Tuple[str, ...]]]]:
    text = path.read_text(encoding="utf-8")
    indexes: Dict[str, List[Tuple[str, Tuple[str, ...]]]] = {}
    for match in INDEX_RE.finditer(text):
        table = match.group("table").lower()
        columns = normalize_columns(match.group("columns").split(","))
        indexes.setdefault(table, []).append((match.group("name"), columns))
    return indexes


def sqlite_indexes(connection: sqlite3.Connection) -> Dict[str, List[Tuple[str, Tuple[str, ...]]]]:
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


def mysql_indexes(connection, database: str) -> Dict[str, List[Tuple[str, Tuple[str, ...]]]]:
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT table_name, index_name, seq_in_index, column_name "
            "FROM information_schema.statistics "
            "WHERE table_schema=%s ORDER BY table_name, index_name, seq_in_index",
            (database,),
        )
        grouped: Dict[Tuple[str, str], List[Tuple[int, str]]] = {}
        for table, name, sequence, column in cursor.fetchall():
            grouped.setdefault((str(table).lower(), str(name)), []).append((int(sequence), str(column)))
    finally:
        cursor.close()

    result: Dict[str, List[Tuple[str, Tuple[str, ...]]]] = {}
    for (table, name), parts in grouped.items():
        columns = normalize_columns(column for _seq, column in sorted(parts))
        result.setdefault(table, []).append((name, columns))
    return result


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


def candidate_status(indexes: Dict[str, List[Tuple[str, Tuple[str, ...]]]]) -> list[dict]:
    rows = []
    for table, columns, reason in CANDIDATES:
        rows.append(
            {
                "table": table,
                "columns": list(columns),
                "covered": covers(indexes, table, columns),
                "reason": reason,
            }
        )
    return rows


def print_indexes(title: str, indexes: Dict[str, List[Tuple[str, Tuple[str, ...]]]]) -> None:
    print(title)
    for table in sorted(indexes):
        for name, columns in sorted(indexes[table]):
            print("  %-28s %-24s %s" % (name, table, ", ".join(columns)))
    print()


def print_candidates(indexes: Dict[str, List[Tuple[str, Tuple[str, ...]]]]) -> int:
    missing = 0
    print("Query-driven candidates")
    for row in candidate_status(indexes):
        state = "covered" if row["covered"] else "MISSING/TO MEASURE"
        if not row["covered"]:
            missing += 1
        print(
            "  %-18s %-24s %-18s %s"
            % (state, row["table"], ", ".join(row["columns"]), row["reason"])
        )
    print()
    return missing


def sqlite_tables(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0]).lower()
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }


def mysql_tables(connection, database: str) -> set[str]:
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema=%s AND table_type='BASE TABLE'",
            (database,),
        )
        return {str(row[0]).lower() for row in cursor.fetchall()}
    finally:
        cursor.close()


def measure_sqlite_candidate(connection: sqlite3.Connection, table: str, column: str, repeats: int) -> dict:
    table = safe_identifier(table)
    column = safe_identifier(column)
    value_row = connection.execute(
        'SELECT "%s" FROM "%s" WHERE "%s" IS NOT NULL LIMIT 1' % (column, table, column)
    ).fetchone()
    value = value_row[0] if value_row else None
    plan_rows = connection.execute(
        'EXPLAIN QUERY PLAN SELECT COUNT(*) FROM "%s" WHERE "%s" = ?' % (table, column),
        (value,),
    ).fetchall()

    timings = []
    count = None
    if value_row:
        for _ in range(repeats):
            started = time.perf_counter()
            count = connection.execute(
                'SELECT COUNT(*) FROM "%s" WHERE "%s" = ?' % (table, column),
                (value,),
            ).fetchone()[0]
            timings.append((time.perf_counter() - started) * 1000.0)

    return {
        "table": table,
        "column": column,
        "sample_value_available": value_row is not None,
        "matched_rows": count,
        "median_ms": round(statistics.median(timings), 3) if timings else None,
        "max_ms": round(max(timings), 3) if timings else None,
        "plan": [list(row) for row in plan_rows],
    }


def measure_mysql_candidate(connection, table: str, column: str, repeats: int) -> dict:
    table = safe_identifier(table)
    column = safe_identifier(column)
    cursor = connection.cursor()
    try:
        cursor.execute(
            "SELECT `%s` FROM `%s` WHERE `%s` IS NOT NULL LIMIT 1" % (column, table, column)
        )
        value_row = cursor.fetchone()
        value = value_row[0] if value_row else None

        cursor.execute(
            "EXPLAIN SELECT COUNT(*) FROM `%s` WHERE `%s` = %%s" % (table, column),
            (value,),
        )
        headers = [description[0] for description in cursor.description]
        plan = [dict(zip(headers, row)) for row in cursor.fetchall()]

        timings = []
        count = None
        if value_row:
            for _ in range(repeats):
                started = time.perf_counter()
                cursor.execute(
                    "SELECT COUNT(*) FROM `%s` WHERE `%s` = %%s" % (table, column),
                    (value,),
                )
                count = cursor.fetchone()[0]
                timings.append((time.perf_counter() - started) * 1000.0)
    finally:
        cursor.close()

    return {
        "table": table,
        "column": column,
        "sample_value_available": value_row is not None,
        "matched_rows": int(count) if count is not None else None,
        "median_ms": round(statistics.median(timings), 3) if timings else None,
        "max_ms": round(max(timings), 3) if timings else None,
        "plan": plan,
    }


def print_measurements(measurements: list[dict]) -> None:
    print("Representative read-only plans and timings")
    for item in measurements:
        print(
            "  %-24s %-18s median=%s ms max=%s ms rows=%s"
            % (
                item["table"],
                item["column"],
                item["median_ms"],
                item["max_ms"],
                item["matched_rows"],
            )
        )
        for plan in item["plan"]:
            print("    PLAN %s" % plan)
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--sqlite", type=Path, help="existing SQLite database to inspect read-only")
    source.add_argument("--mysql-host", help="MySQL/MariaDB host to inspect")
    parser.add_argument("--mysql-port", type=int, default=3306)
    parser.add_argument("--mysql-database")
    parser.add_argument("--mysql-user")
    parser.add_argument("--mysql-password-env", default="NOETHYS_DB_PASSWORD")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--json", type=Path, help="optional JSON report path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.repeats < 1:
        raise SystemExit("--repeats doit être >= 1")

    declared = parse_declared_indexes()
    print_indexes("Indexes declared by DATA_Tables.py", declared)
    declared_missing = print_candidates(declared)
    print("Declared candidates still requiring measurement: %d" % declared_missing)

    report = {
        "declared_candidates": candidate_status(declared),
        "database": None,
    }

    if args.sqlite is not None:
        if not args.sqlite.is_file():
            raise SystemExit("SQLite database does not exist: %s" % args.sqlite)
        uri = args.sqlite.resolve().as_uri() + "?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
        connection.execute("PRAGMA query_only=ON")
        try:
            actual = sqlite_indexes(connection)
            tables = sqlite_tables(connection)
            measurements = [
                measure_sqlite_candidate(connection, table, columns[0], args.repeats)
                for table, columns, _reason in CANDIDATES
                if table.lower() in tables
            ]
        finally:
            connection.close()

        print()
        print_indexes("Indexes present in SQLite database (read-only)", actual)
        actual_missing = print_candidates(actual)
        print("Database candidates still requiring measurement: %d" % actual_missing)
        print_measurements(measurements)
        report["database"] = {
            "backend": "sqlite",
            "path": str(args.sqlite.resolve()),
            "candidates": candidate_status(actual),
            "measurements": measurements,
        }

    elif args.mysql_host:
        if not args.mysql_database or not args.mysql_user:
            raise SystemExit("--mysql-database et --mysql-user sont requis avec --mysql-host")
        password = os.environ.get(args.mysql_password_env)
        if password is None:
            raise SystemExit("Variable %s absente" % args.mysql_password_env)
        try:
            import mysql.connector  # type: ignore
        except ImportError as exc:
            raise SystemExit("mysql-connector-python est requis") from exc

        connection = mysql.connector.connect(
            host=args.mysql_host,
            port=args.mysql_port,
            database=args.mysql_database,
            user=args.mysql_user,
            password=password,
            autocommit=False,
            connection_timeout=10,
        )
        try:
            actual = mysql_indexes(connection, args.mysql_database)
            tables = mysql_tables(connection, args.mysql_database)
            measurements = [
                measure_mysql_candidate(connection, table, columns[0], args.repeats)
                for table, columns, _reason in CANDIDATES
                if table.lower() in tables
            ]
            connection.rollback()
        finally:
            connection.close()

        print()
        print_indexes("Indexes present in MySQL/MariaDB database (read-only usage)", actual)
        actual_missing = print_candidates(actual)
        print("Database candidates still requiring measurement: %d" % actual_missing)
        print_measurements(measurements)
        report["database"] = {
            "backend": "mysql",
            "host": args.mysql_host,
            "port": args.mysql_port,
            "database": args.mysql_database,
            "candidates": candidate_status(actual),
            "measurements": measurements,
        }

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")

    print("\nAudit only: no CREATE/ALTER/DROP statement was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
