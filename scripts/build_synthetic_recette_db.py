#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Construit une base SQLite de recette Noethys à partir de Defaut.dat.

Le script ne touche jamais à une base utilisateur : il copie le modèle livré
avec Noethys vers un fichier de sortie, crée les tables métier absentes depuis
Data.DATA_Tables.DB_DATA, puis ajoute des données synthétiques.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))

from Data import DATA_Tables  # noqa: E402

DEFAULT_DB = NOETHYS / "Static" / "Databases" / "Defaut.dat"
DEFAULT_OUT = ROOT / "tmp" / "recette_synthetique.dat"


def columns(conn: sqlite3.Connection, table: str) -> set[str]:
    try:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    except sqlite3.DatabaseError:
        return set()


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row is not None


def create_business_schema(conn: sqlite3.Connection) -> int:
    """Reproduit la création SQLite des tables métier de GestionDB.CreationTables."""
    created = 0
    for table, description in DATA_Tables.DB_DATA.items():
        if table_exists(conn, table):
            continue
        fields = []
        for name, sql_type, _info in description:
            adapted = sql_type
            if adapted == "LONGBLOB":
                adapted = "BLOB"
            elif adapted == "BIGINT":
                adapted = "INTEGER"
            fields.append(f'"{name}" {adapted}')
        conn.execute(f'CREATE TABLE "{table}" ({", ".join(fields)})')
        created += 1
    return created


def insert_filtered(conn: sqlite3.Connection, table: str, values: dict) -> int | None:
    if not table_exists(conn, table):
        return None
    cols = columns(conn, table)
    data = {k: v for k, v in values.items() if k in cols}
    if data:
        names = ", ".join(f'"{name}"' for name in data)
        marks = ", ".join("?" for _ in data)
        cur = conn.execute(
            f'INSERT INTO "{table}" ({names}) VALUES ({marks})', tuple(data.values())
        )
    else:
        cur = conn.execute(f'INSERT INTO "{table}" DEFAULT VALUES')
    return int(cur.lastrowid)


def generate(args: argparse.Namespace) -> Path:
    if not DEFAULT_DB.is_file():
        raise FileNotFoundError(f"Base modèle introuvable: {DEFAULT_DB}")

    out = args.output.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    shutil.copy2(DEFAULT_DB, out)

    conn = sqlite3.connect(out)
    try:
        conn.execute("PRAGMA foreign_keys=OFF")
        conn.execute("BEGIN")
        created = create_business_schema(conn)
        print(f"Tables métier créées: {created}")

        for fidx in range(1, args.families + 1):
            parent_id = insert_filtered(conn, "individus", {
                "IDcivilite": 1, "nom": f"TEST{fidx:05d}", "prenom": "Parent",
                "date_naiss": "1985-01-01", "rue_resid": f"{fidx} rue de la Recette",
                "cp_resid": "35000", "ville_resid": "RENNES",
                "mail": f"parent{fidx}@example.invalid", "date_creation": "2026-08-15",
                "etat": "actif",
            })
            family_id = insert_filtered(conn, "familles", {
                "date_creation": "2026-08-15", "allocataire": parent_id,
                "internet_actif": 0, "etat": "actif",
            })
            if parent_id is not None and family_id is not None:
                insert_filtered(conn, "rattachements", {
                    "IDindividu": parent_id, "IDfamille": family_id,
                    "IDcategorie": 1, "titulaire": 1,
                })

            for cidx in range(1, args.children + 1):
                child_id = insert_filtered(conn, "individus", {
                    "IDcivilite": 3, "nom": f"TEST{fidx:05d}", "prenom": f"Enfant{cidx}",
                    "date_naiss": f"201{cidx}-06-15", "adresse_auto": parent_id,
                    "date_creation": "2026-08-15", "etat": "actif",
                })
                if child_id is None:
                    continue
                if family_id is not None:
                    insert_filtered(conn, "rattachements", {
                        "IDindividu": child_id, "IDfamille": family_id,
                        "IDcategorie": 2, "titulaire": 0,
                    })

                inscription_id = insert_filtered(conn, "inscriptions", {
                    "IDindividu": child_id, "IDfamille": family_id,
                    "IDactivite": 1, "IDgroupe": 1, "IDcategorie_tarif": 1,
                    "date_inscription": "2026-08-15", "statut": "ok",
                })

                for n in range(args.consumptions_per_child):
                    day = (n % 28) + 1
                    month = ((n // 28) % 12) + 1
                    insert_filtered(conn, "consommations", {
                        "IDindividu": child_id, "IDinscription": inscription_id,
                        "IDactivite": 1, "IDgroupe": 1, "IDunite": 1,
                        "date": f"2026-{month:02d}-{day:02d}",
                        "heure_debut": "08:30", "heure_fin": "17:30",
                        "etat": "reservation",
                    })

                for n in range(args.prestations_per_child):
                    insert_filtered(conn, "prestations", {
                        "IDcompte_payeur": family_id, "IDindividu": child_id,
                        "IDactivite": 1, "date": "2026-08-15",
                        "categorie": "consommation", "label": f"Prestation synthétique {n + 1}",
                        "montant": 12.5,
                    })

            for n in range(args.payments_per_family):
                insert_filtered(conn, "reglements", {
                    "IDcompte_payeur": family_id, "date": "2026-08-15",
                    "IDmode": 1, "montant": 25.0,
                    "numero_piece": f"T{fidx:05d}-{n+1:02d}",
                })

        conn.commit()
        print(f"Base de recette créée : {out}")
        for table in ("individus", "familles", "rattachements", "inscriptions",
                      "consommations", "prestations", "reglements"):
            count = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
            print(f"{table:16s} {count:8d}")
        return out
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--families", type=int, default=500)
    parser.add_argument("--children", type=int, default=2)
    parser.add_argument("--consumptions-per-child", type=int, default=80)
    parser.add_argument("--prestations-per-child", type=int, default=12)
    parser.add_argument("--payments-per-family", type=int, default=6)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    for name in ("families", "children", "consumptions_per_child",
                 "prestations_per_child", "payments_per_family"):
        if getattr(args, name) < 0:
            parser.error(f"--{name.replace('_', '-')} doit être >= 0")
    return args


if __name__ == "__main__":
    generate(parse_args())
