#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mesure quelques lectures représentatives sans modifier la base Noethys.

Par défaut, le script ouvre la base configurée par Noethys via GestionDB.DB()
avec modeCreation=False. L'option --db permet de cibler explicitement une base
SQLite (par exemple la base synthétique de recette) sans charger l'interface
Noethys ni wxPython.

Aucune requête d'écriture, DDL, transaction explicite ou migration n'est
exécutée par ce script.
"""

from __future__ import annotations

import argparse
import sqlite3
import statistics
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"


READ_ONLY_QUERIES = (
    ("individus", "SELECT COUNT(*) FROM individus;"),
    ("familles", "SELECT COUNT(*) FROM familles;"),
    ("inscriptions", "SELECT COUNT(*) FROM inscriptions;"),
    ("consommations", "SELECT COUNT(*) FROM consommations;"),
    ("prestations", "SELECT COUNT(*) FROM prestations;"),
    ("reglements", "SELECT COUNT(*) FROM reglements;"),
)


class SQLiteReadOnlyDB:
    """Adaptateur minimal compatible avec la sonde, limité à SQLite."""

    isNetwork = False
    echec = 0

    def __init__(self, path: Path):
        uri = f"file:{path.resolve().as_posix()}?mode=ro"
        self.connexion = sqlite3.connect(uri, uri=True)
        self.cursor = self.connexion.cursor()

    def ExecuterReq(self, req: str):
        self.cursor.execute(req)
        return True

    def ResultatReq(self):
        return self.cursor.fetchall()

    def Close(self):
        self.connexion.close()


def _assert_read_only(sql: str) -> None:
    normalized = " ".join(sql.strip().split()).upper()
    if not normalized.startswith("SELECT "):
        raise ValueError(f"Requête non autorisée en mode lecture seule: {sql!r}")
    forbidden = (
        " INSERT ", " UPDATE ", " DELETE ", " REPLACE ", " ALTER ",
        " CREATE ", " DROP ", " TRUNCATE ", " GRANT ", " REVOKE ",
    )
    padded = f" {normalized} "
    if any(token in padded for token in forbidden):
        raise ValueError(f"Requête potentiellement destructive refusée: {sql!r}")


def _measure(db: Any, sql: str, repeats: int) -> tuple[int, float, float]:
    _assert_read_only(sql)
    durations = []
    count = 0
    for _ in range(repeats):
        start = time.perf_counter()
        result = db.ExecuterReq(sql)
        if result not in ("ok", None, True):
            raise RuntimeError(f"Échec d'exécution SQL: {result!r}")
        rows = db.ResultatReq()
        elapsed = time.perf_counter() - start
        durations.append(elapsed)
        if rows:
            count = int(rows[0][0])
    return count, statistics.median(durations), max(durations)


def sqlite_version(db: Any) -> str | None:
    try:
        db.cursor.execute("SELECT sqlite_version();")
        row = db.cursor.fetchone()
        return row[0] if row else None
    except Exception:
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "legacy_repeats",
        nargs="?",
        type=int,
        help="Compatibilité: ancien argument positionnel du nombre de répétitions",
    )
    parser.add_argument("--repeats", type=int, default=None)
    parser.add_argument(
        "--db",
        type=Path,
        help="Base SQLite explicite à ouvrir strictement en lecture seule",
    )
    args = parser.parse_args()
    repeats = args.repeats if args.repeats is not None else args.legacy_repeats
    args.repeats = max(1, repeats if repeats is not None else 5)
    return args


def open_db(args: argparse.Namespace):
    if args.db is not None:
        if not args.db.is_file():
            raise FileNotFoundError(f"Base SQLite introuvable: {args.db}")
        return SQLiteReadOnlyDB(args.db), f"SQLite lecture seule: {args.db}"

    if str(NOETHYS) not in sys.path:
        sys.path.insert(0, str(NOETHYS))
    import GestionDB  # noqa: E402

    db = GestionDB.DB(modeCreation=False)
    return db, "MySQL/MariaDB" if db.isNetwork else "SQLite"


def main() -> int:
    args = parse_args()
    try:
        db, backend = open_db(args)
    except Exception as err:
        print(f"Impossible d'ouvrir la base: {err}", file=sys.stderr)
        return 2

    try:
        if getattr(db, "echec", 0):
            print("Impossible d'ouvrir la base configurée.", file=sys.stderr)
            return 2

        print("Sonde Noethys DB — lecture seule")
        print(f"Backend: {backend}")
        version = db.GetVersionServeur() if getattr(db, "isNetwork", False) else sqlite_version(db)
        if version:
            print(f"Version serveur: {version}")
        print(f"Mesures par requête: {args.repeats}\n")

        errors = 0
        for label, sql in READ_ONLY_QUERIES:
            try:
                count, median, worst = _measure(db, sql, args.repeats)
            except Exception as err:
                errors += 1
                print(f"{label:16s} ERREUR  {err}")
                continue
            print(
                f"{label:16s} lignes={count:<8d} "
                f"médiane={median * 1000:8.2f} ms  max={worst * 1000:8.2f} ms"
            )
        return 1 if errors else 0
    finally:
        try:
            db.Close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
