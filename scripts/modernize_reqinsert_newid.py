#!/usr/bin/env python3
"""Sécurise GestionDB.DB.ReqInsert sans masquer les erreurs SQL.

Le script ajoute ``newID = None`` avant le bloc ``try`` de ReqInsert si cette
initialisation manque encore. Par défaut il vérifie seulement ; ``--write``
applique la correction.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "noethys" / "GestionDB.py"

MARKER = '        req = "INSERT INTO %s %s VALUES %s" % (nomTable, champs, interr)\n        \n        try:\n'
REPLACEMENT = '        req = "INSERT INTO %s %s VALUES %s" % (nomTable, champs, interr)\n        newID = None\n        \n        try:\n'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="applique la correction")
    args = parser.parse_args()

    source = TARGET.read_text(encoding="utf-8")
    if REPLACEMENT in source:
        print("ReqInsert initialise déjà newID.")
        return 0
    if MARKER not in source:
        print("Motif ReqInsert attendu introuvable : aucune modification effectuée.")
        return 2

    print("ReqInsert peut retourner newID non initialisé après une erreur SQL.")
    if not args.write:
        print("Relancer avec --write pour appliquer la correction.")
        return 1

    updated = source.replace(MARKER, REPLACEMENT, 1)
    TARGET.write_text(updated, encoding="utf-8", newline="")
    print("Initialisation de newID ajoutée dans ReqInsert.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())