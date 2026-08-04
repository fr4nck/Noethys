#!/usr/bin/env python3
"""Vérifie la configuration UTF-8, sa sauvegarde et sa récupération."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))

from Utils import UTILS_Config, UTILS_Fichiers  # noqa: E402


def main() -> int:
    original_get_rep_utilisateur = UTILS_Fichiers.GetRepUtilisateur
    try:
        with tempfile.TemporaryDirectory(prefix="noethys-config-utf8-") as temp_dir:
            base = Path(temp_dir) / "Préférences Noëthys"
            base.mkdir()

            def get_rep_utilisateur(fichier: str = "") -> str:
                return str(base / fichier)

            UTILS_Fichiers.GetRepUtilisateur = get_rep_utilisateur

            config = UTILS_Config.FichierConfig()
            donnees = {
                "nomFichier": "Été 2026 – José Muñoz",
                "utilisateur": "Léa Drouillé",
                "ville": "Łódź",
                "symbole": "✅",
            }
            config.SetDictConfig(donnees)

            config_path = Path(config.nomFichier)
            backup_path = Path(str(config_path) + ".bak")
            if not config_path.is_file() or not backup_path.is_file():
                raise RuntimeError("Config.json ou sa sauvegarde n'a pas été créée")

            if config.GetDictConfig() != donnees:
                raise RuntimeError("La configuration UTF-8 n'a pas été relue à l'identique")

            config_path.write_text("{ configuration corrompue", encoding="utf-8")
            recovered = config.GetDictConfig()
            if recovered != donnees:
                raise RuntimeError("La récupération depuis Config.json.bak a échoué")

            quarantines = list(base.glob("Config.json.corrupt-*"))
            if not quarantines:
                raise RuntimeError("La configuration corrompue n'a pas été mise en quarantaine")

            if config.GetDictConfig() != donnees:
                raise RuntimeError("La configuration restaurée n'est pas exploitable")
    finally:
        UTILS_Fichiers.GetRepUtilisateur = original_get_rep_utilisateur

    print("Configuration UTF-8, sauvegarde et récupération valides.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
