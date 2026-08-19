#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Préflight de recette sur une copie de base Noethys existante.

Le script n'exécute que des lectures. Pour SQLite, la base est ouverte avec
``mode=ro`` et son SHA-256 est vérifié avant/après l'audit. Pour MySQL/MariaDB,
seules des requêtes SELECT/SHOW sont autorisées par le garde-fou interne ; un
compte SQL limité à SELECT reste recommandé pour une garantie côté serveur.

Aucune donnée nominative n'est exportée : le rapport contient uniquement
structure, volumes, agrégats, plages de dates et compteurs d'anomalies métier.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

CORE_TABLES = ("familles", "individus", "rattachements")
RECIPE_TABLES = (
    "familles",
    "individus",
    "rattachements",
    "inscriptions",
    "consommations",
    "prestations",
    "factures",
    "reglements",
    "ventilation",
    "modes_reglements",
    "activites",
    "cotisations",
)
DATE_METRICS = (
    ("familles", "date_creation"),
    ("individus", "date_creation"),
    ("inscriptions", "date_inscription"),
    ("consommations", "date"),
    ("prestations", "date"),
    ("factures", "date_edition"),
    ("reglements", "date"),
)
SUM_METRICS = (
    ("prestations", "montant"),
    ("reglements", "montant"),
    ("ventilation", "montant"),
)
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class AuditError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def ident(name: str, backend: str) -> str:
    if not _SAFE_IDENTIFIER.match(name):
        raise AuditError(f"Identifiant SQL refusé: {name!r}")
    return f'"{name}"' if backend == "sqlite" else f"`{name}`"


def assert_read_query(sql: str) -> None:
    normalized = sql.lstrip().upper()
    if not (normalized.startswith("SELECT") or normalized.startswith("SHOW")):
        raise AuditError(f"Requête non-lecture refusée: {sql[:80]!r}")


class Reader:
    backend: str

    def query(self, sql: str, params=()) -> list[tuple]:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class SQLiteReader(Reader):
    backend = "sqlite"

    def __init__(self, path: Path):
        self.path = path.resolve()
        uri_path = quote(self.path.as_posix(), safe="/:")
        self.conn = sqlite3.connect(f"file:{uri_path}?mode=ro", uri=True)
        self.conn.execute("PRAGMA query_only=ON")

    def query(self, sql: str, params=()) -> list[tuple]:
        assert_read_query(sql)
        return list(self.conn.execute(sql, params).fetchall())

    def close(self) -> None:
        self.conn.close()


class MySQLReader(Reader):
    backend = "mysql"

    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        try:
            import mysql.connector  # type: ignore
        except ImportError as exc:
            raise AuditError(
                "mysql-connector-python est requis pour --mysql-host"
            ) from exc
        self.database = database
        self.conn = mysql.connector.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            autocommit=False,
            connection_timeout=10,
        )
        self.cursor = self.conn.cursor()

    def query(self, sql: str, params=()) -> list[tuple]:
        assert_read_query(sql)
        self.cursor.execute(sql, params)
        return list(self.cursor.fetchall())

    def close(self) -> None:
        try:
            self.conn.rollback()
        finally:
            self.cursor.close()
            self.conn.close()


def list_tables(reader: Reader, database: str | None = None) -> list[str]:
    if reader.backend == "sqlite":
        rows = reader.query(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    else:
        rows = reader.query(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema=%s AND table_type='BASE TABLE' ORDER BY table_name",
            (database,),
        )
    return [str(row[0]) for row in rows]


def table_columns(reader: Reader, table: str, database: str | None = None) -> list[dict]:
    if reader.backend == "sqlite":
        rows = reader.query(
            'SELECT cid, name, type, "notnull", dflt_value, pk '
            "FROM pragma_table_info(?) ORDER BY cid",
            (table,),
        )
        return [
            {
                "ordinal": int(row[0]),
                "name": str(row[1]),
                "type": str(row[2] or ""),
                "nullable": not bool(row[3]),
                "primary": bool(row[5]),
            }
            for row in rows
        ]

    rows = reader.query(
        "SELECT ordinal_position, column_name, column_type, is_nullable, column_key "
        "FROM information_schema.columns "
        "WHERE table_schema=%s AND table_name=%s ORDER BY ordinal_position",
        (database, table),
    )
    return [
        {
            "ordinal": int(row[0]),
            "name": str(row[1]),
            "type": str(row[2] or ""),
            "nullable": str(row[3]).upper() == "YES",
            "primary": str(row[4]).upper() == "PRI",
        }
        for row in rows
    ]


def scalar(reader: Reader, sql: str, params=()) -> Any:
    rows = reader.query(sql, params)
    return rows[0][0] if rows else None


def business_anomalies(reader: Reader, table_set: set[str], columns_by_table: dict[str, set[str]]) -> dict:
    """Compteurs non nominatifs d'invariants métier utiles à la recette.

    Le modèle de saisie des cotisations crée une prestation propre à chaque
    cotisation et la suppression d'une cotisation supprime sa prestation. Un
    ``IDprestation`` partagé par plusieurs cotisations est donc une anomalie de
    données/historique, même si le schéma ne possède pas de contrainte UNIQUE.
    """
    result = {}
    if (
        "cotisations" in table_set
        and "IDprestation" in columns_by_table.get("cotisations", set())
    ):
        qtable = ident("cotisations", reader.backend)
        qprestation = ident("IDprestation", reader.backend)
        result["cotisations_shared_prestation_count"] = int(
            scalar(
                reader,
                f"SELECT COUNT(*) FROM ("
                f"SELECT {qprestation} FROM {qtable} "
                f"WHERE {qprestation} IS NOT NULL "
                f"GROUP BY {qprestation} HAVING COUNT(*) > 1"
                f") shared_cotisation_prestations",
            )
            or 0
        )
    return result


def build_report(reader: Reader, source: dict, database: str | None = None) -> dict:
    start = time.perf_counter()
    tables = list_tables(reader, database)
    table_set = set(tables)

    schema = []
    columns_by_table: dict[str, set[str]] = {}
    for table in tables:
        cols = table_columns(reader, table, database)
        schema.append({"table": table, "columns": cols})
        columns_by_table[table] = {str(item["name"]) for item in cols}

    counts = {}
    for table in RECIPE_TABLES:
        if table in table_set:
            counts[table] = int(
                scalar(reader, f"SELECT COUNT(*) FROM {ident(table, reader.backend)}") or 0
            )

    date_ranges = {}
    for table, column in DATE_METRICS:
        if table in table_set and column in columns_by_table.get(table, set()):
            qtable = ident(table, reader.backend)
            qcol = ident(column, reader.backend)
            rows = reader.query(f"SELECT MIN({qcol}), MAX({qcol}) FROM {qtable}")
            date_ranges[f"{table}.{column}"] = {
                "min": rows[0][0] if rows else None,
                "max": rows[0][1] if rows else None,
            }

    sums = {}
    for table, column in SUM_METRICS:
        if table in table_set and column in columns_by_table.get(table, set()):
            qtable = ident(table, reader.backend)
            qcol = ident(column, reader.backend)
            value = scalar(reader, f"SELECT SUM({qcol}) FROM {qtable}")
            sums[f"{table}.{column}"] = None if value is None else str(value)

    anomalies = business_anomalies(reader, table_set, columns_by_table)

    missing_core = [table for table in CORE_TABLES if table not in table_set]
    missing_recipe = [table for table in RECIPE_TABLES if table not in table_set]
    elapsed = time.perf_counter() - start

    canonical_schema = [
        {
            "table": item["table"],
            "columns": [
                {
                    "ordinal": col["ordinal"],
                    "name": col["name"],
                    "type": col["type"],
                    "nullable": col["nullable"],
                    "primary": col["primary"],
                }
                for col in item["columns"]
            ],
        }
        for item in schema
    ]

    return {
        "format": 1,
        "source": source,
        "backend": reader.backend,
        "schema_digest": canonical_digest(canonical_schema),
        "table_count": len(tables),
        "missing_core_tables": missing_core,
        "missing_recipe_tables": missing_recipe,
        "counts": counts,
        "date_ranges": date_ranges,
        "sums": sums,
        "business_anomalies": anomalies,
        "elapsed_seconds": round(elapsed, 3),
    }


def load_expected_schema(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        digest = data["schema_digest"]
    except Exception as exc:
        raise AuditError(f"Rapport de référence invalide: {path}") from exc
    if not isinstance(digest, str) or not digest:
        raise AuditError(f"schema_digest absent du rapport: {path}")
    return digest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--sqlite", type=Path, help="copie SQLite .dat à auditer")
    source.add_argument("--mysql-host", help="hôte MySQL/MariaDB")
    parser.add_argument("--mysql-port", type=int, default=3306)
    parser.add_argument("--mysql-database")
    parser.add_argument("--mysql-user")
    parser.add_argument(
        "--mysql-password-env",
        default="NOETHYS_DB_PASSWORD",
        help="variable d'environnement contenant le mot de passe",
    )
    parser.add_argument("--json", type=Path, help="écrit le rapport dans ce fichier")
    parser.add_argument(
        "--expect-schema-from",
        type=Path,
        help="échoue si le schema_digest diffère de ce rapport antérieur",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sqlite_before = None
    reader: Reader | None = None

    try:
        if args.sqlite:
            path = args.sqlite.resolve()
            if not path.is_file():
                raise AuditError(f"Base SQLite introuvable: {path}")
            sqlite_before = sha256_file(path)
            source = {
                "kind": "sqlite-copy",
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256_before": sqlite_before,
            }
            reader = SQLiteReader(path)
            report = build_report(reader, source)
        else:
            if not args.mysql_database or not args.mysql_user:
                raise AuditError("--mysql-database et --mysql-user sont requis avec --mysql-host")
            password = os.environ.get(args.mysql_password_env)
            if password is None:
                raise AuditError(
                    f"Variable {args.mysql_password_env} absente (mot de passe MySQL/MariaDB)"
                )
            source = {
                "kind": "mysql-readonly-recipe",
                "host": args.mysql_host,
                "port": args.mysql_port,
                "database": args.mysql_database,
                "user": args.mysql_user,
            }
            reader = MySQLReader(
                args.mysql_host,
                args.mysql_port,
                args.mysql_database,
                args.mysql_user,
                password,
            )
            version = scalar(reader, "SELECT VERSION()")
            source["server_version"] = str(version)
            report = build_report(reader, source, args.mysql_database)

        if reader is not None:
            reader.close()
            reader = None

        if args.sqlite:
            sqlite_after = sha256_file(args.sqlite.resolve())
            report["source"]["sha256_after"] = sqlite_after
            report["source"]["unchanged_during_audit"] = sqlite_after == sqlite_before
            if sqlite_after != sqlite_before:
                raise AuditError("La copie SQLite a changé pendant l'audit en lecture seule")

        if args.expect_schema_from:
            expected = load_expected_schema(args.expect_schema_from)
            report["expected_schema_digest"] = expected
            report["schema_matches_reference"] = report["schema_digest"] == expected
            if report["schema_digest"] != expected:
                raise AuditError(
                    "Le schéma diffère du rapport de référence: migration ou changement de structure détecté"
                )

        text = json.dumps(report, ensure_ascii=False, indent=2, default=str)
        print(text)
        if args.json:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(text + "\n", encoding="utf-8")

        if report["missing_core_tables"]:
            print(
                "Tables cœur manquantes: " + ", ".join(report["missing_core_tables"]),
                file=sys.stderr,
            )
            return 2
        return 0
    except (AuditError, sqlite3.DatabaseError) as exc:
        print(f"ERREUR: {exc}", file=sys.stderr)
        return 3
    finally:
        if reader is not None:
            reader.close()


if __name__ == "__main__":
    raise SystemExit(main())
