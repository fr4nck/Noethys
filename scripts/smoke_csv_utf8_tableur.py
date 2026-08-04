#!/usr/bin/env python3
"""Vérifie les conventions CSV UTF-8 sûres sous Windows."""
from __future__ import annotations

import csv
import tempfile
from pathlib import Path


def verifier(encodage: str) -> None:
    lignes = [
        ["Nom", "Ville", "Commentaire"],
        ["Élodie Frangeul", "La Guerche-de-Bretagne", "Très bien"],
        ["José Muñoz", "Łódź", "Données UTF-8"],
    ]

    with tempfile.TemporaryDirectory(prefix="noethys-csv-") as dossier:
        chemin = Path(dossier) / f"export-{encodage}.csv"
        with chemin.open("w", encoding=encodage, newline="") as flux:
            writer = csv.writer(flux, delimiter=";")
            writer.writerows(lignes)

        octets = chemin.read_bytes()
        if b"\r\n\r\n" in octets:
            raise RuntimeError("Lignes vides parasites détectées dans le CSV")

        with chemin.open("r", encoding=encodage, newline="") as flux:
            relu = list(csv.reader(flux, delimiter=";"))
        if relu != lignes:
            raise RuntimeError(f"Aller-retour CSV incorrect avec {encodage}")

        if encodage == "utf-8-sig" and not octets.startswith(b"\xef\xbb\xbf"):
            raise RuntimeError("BOM UTF-8 attendu pour le profil Excel")
        if encodage == "utf-8" and octets.startswith(b"\xef\xbb\xbf"):
            raise RuntimeError("BOM UTF-8 inattendu pour le profil standard")


def main() -> int:
    verifier("utf-8")
    verifier("utf-8-sig")
    print("Conventions CSV UTF-8 valides.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
