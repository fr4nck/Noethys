#!/usr/bin/env python3
"""Vérifie les lectures/écritures UTF-8 du module UTILS_Json de Noethys."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))

from Utils import UTILS_Json


def main() -> int:
    attendu = {
        "nom": "Élodie Drouillé",
        "ville": "La Guerche-de-Bretagne",
        "international": "José Muñoz — Łukasz — Ægir",
    }

    with tempfile.TemporaryDirectory(prefix="noethys-json-") as temp_dir:
        path = Path(temp_dir) / "Configuration été.json"
        UTILS_Json.Ecrire(str(path), attendu)
        brut = path.read_text(encoding="utf-8")
        if "Élodie" not in brut or "\\u00c9" in brut:
            raise RuntimeError("Le JSON n'est pas écrit en UTF-8 lisible")
        obtenu = UTILS_Json.Lire(str(path))
        if obtenu != attendu:
            raise RuntimeError(f"Aller-retour JSON incorrect : {obtenu!r}")

    print("UTILS_Json UTF-8 valide.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
