#!/usr/bin/env python3
"""Vérifie les principaux parcours UTF-8 sans toucher aux données utilisateur."""
from __future__ import annotations

import csv
import json
import sqlite3
import tempfile
from pathlib import Path

SAMPLE = "Élodie Frangeul — Léa Drouillé — José Muñoz — Łukasz — 😀"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="noethys_utf8_") as tmp:
        root = Path(tmp) / "Données été 2026"
        root.mkdir()

        # Texte brut
        text_path = root / "équipe.txt"
        text_path.write_text(SAMPLE, encoding="utf-8")
        if text_path.read_text(encoding="utf-8") != SAMPLE:
            raise RuntimeError("Échec aller-retour texte UTF-8")

        # JSON
        json_path = root / "config.json"
        json_path.write_text(json.dumps({"texte": SAMPLE}, ensure_ascii=False), encoding="utf-8")
        if json.loads(json_path.read_text(encoding="utf-8"))["texte"] != SAMPLE:
            raise RuntimeError("Échec aller-retour JSON UTF-8")

        # CSV
        csv_path = root / "personnes.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as stream:
            csv.writer(stream).writerow([SAMPLE])
        with csv_path.open("r", encoding="utf-8", newline="") as stream:
            if next(csv.reader(stream))[0] != SAMPLE:
                raise RuntimeError("Échec aller-retour CSV UTF-8")

        # SQLite avec chemin et contenu Unicode
        db_path = root / "base données été.dat"
        connexion = sqlite3.connect(str(db_path))
        try:
            connexion.execute("CREATE TABLE test (texte TEXT)")
            connexion.execute("INSERT INTO test (texte) VALUES (?)", (SAMPLE,))
            connexion.commit()
            valeur = connexion.execute("SELECT texte FROM test").fetchone()[0]
            if valeur != SAMPLE:
                raise RuntimeError("Échec aller-retour SQLite UTF-8")
        finally:
            connexion.close()

    print("Parcours UTF-8 texte/JSON/CSV/SQLite valides.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
