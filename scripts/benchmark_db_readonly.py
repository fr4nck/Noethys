#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mesure quelques lectures représentatives sans modifier la base Noethys.

Ce script ouvre la base configurée par Noethys via GestionDB.DB() avec
modeCreation=False, puis exécute uniquement des SELECT COUNT(*). Il est conçu
pour pouvoir être utilisé sur une base existante même lorsqu'aucune copie de
travail n'est disponible.

Aucune requête d'écriture, DDL, transaction explicite ou migration n'est
exécutée par ce script.
"""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))

import GestionDB  # noqa: E402


READ_ONLY_QUERIES = (
    ("individus", "SELECT COUNT(*) FROM individus;"),
    ("familles", "SELECT COUNT(*) FROM familles;"),
    ("inscriptions", "SELECT COUNT(*) FROM inscriptions;"),
    ("consommations", "SELECT COUNT(*) FROM consommations;"),
    ("prestations", "SELECT COUNT(*) FROM prestations;"),
    ("reglements", "SELECT COUNT(*) FROM reglements;"),
)


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


def _measure(db: GestionDB.DB, sql: str, repeats: int) -> tuple[int, float, float]:
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


def main() -> int:
    repeats = 5
    if len(sys.argv) > 1:
        repeats = max(1, int(sys.argv[1]))

    db = GestionDB.DB(modeCreation=False)
    try:
        if getattr(db, "echec", 0):
            print("Impossible d'ouvrir la base configurée.", file=sys.stderr)
            return 2

        print("Sonde Noethys DB — lecture seule")
        print(f"Backend: {'MySQL/MariaDB' if db.isNetwork else 'SQLite'}")
        version = db.GetVersionServeur() if db.isNetwork else sqlite_version(db)
        if version:
            print(f"Version serveur: {version}")
        print(f"Mesures par requête: {repeats}\n")

        for label, sql in READ_ONLY_QUERIES:
            try:
                count, median, worst = _measure(db, sql, repeats)
            except Exception as err:
                print(f"{label:16s} ERREUR  {err}")
                continue
            print(
                f"{label:16s} lignes={count:<8d} "
                f"médiane={median * 1000:8.2f} ms  max={worst * 1000:8.2f} ms"
            )
        return 0
    finally:
        try:
            db.Close()
        except Exception:
            pass


def sqlite_version(db: GestionDB.DB) -> str | None:
    try:
        db.cursor.execute("SELECT sqlite_version();")
        row = db.cursor.fetchone()
        return row[0] if row else None
    except Exception:
        return None


if __name__ == "__main__":
    raise SystemExit(main())
