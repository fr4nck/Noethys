#!/usr/bin/env python3
"""Vérifie les chemins de fichiers utilisés par Noethys sans toucher aux données réelles."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))

import Chemins
from Utils import UTILS_Fichiers


def main() -> int:
    original_get_main_path = Chemins.GetMainPath

    with tempfile.TemporaryDirectory(prefix="Noëthys test ") as temp_dir:
        root = Path(temp_dir)
        portable = root / "Portable"
        portable.mkdir()

        def get_main_path(filename: str = "") -> str:
            return str(root / filename) if filename else str(root)

        Chemins.GetMainPath = get_main_path
        try:
            user_file = Path(UTILS_Fichiers.GetRepUtilisateur("Config été.json"))
            data_file = Path(UTILS_Fichiers.GetRepData("Familles été_DATA.dat"))
            temp_file = Path(UTILS_Fichiers.GetRepTemp("aperçu été.txt"))

            expected_user = portable / "Config été.json"
            expected_data = portable / "Data" / "Familles été_DATA.dat"
            expected_temp = portable / "Temp" / "aperçu été.txt"

            if user_file != expected_user:
                raise RuntimeError(f"Chemin utilisateur portable incorrect : {user_file}")
            if data_file != expected_data:
                raise RuntimeError(f"Chemin de données portable incorrect : {data_file}")
            if temp_file != expected_temp:
                raise RuntimeError(f"Chemin temporaire portable incorrect : {temp_file}")

            user_file.write_text("été", encoding="utf-8")
            data_file.write_bytes(b"SQLite format 3\x00")
            temp_file.parent.mkdir(parents=True, exist_ok=True)
            temp_file.write_text("aperçu", encoding="utf-8")

            if user_file.read_text(encoding="utf-8") != "été":
                raise RuntimeError("Lecture Unicode du fichier utilisateur incorrecte")
            if not data_file.is_file() or not temp_file.is_file():
                raise RuntimeError("Écriture dans les répertoires portables impossible")
        finally:
            Chemins.GetMainPath = original_get_main_path

    print("Chemins Unicode, espaces et mode portable valides.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
