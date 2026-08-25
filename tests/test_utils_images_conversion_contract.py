# -*- coding: utf-8 -*-
import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FICHIER = ROOT / "noethys" / "Utils" / "UTILS_Images.py"


def _charger_hex_to_rgb():
    arbre = ast.parse(FICHIER.read_text(encoding="utf-8"), filename=str(FICHIER))
    fonction = next(
        noeud
        for noeud in arbre.body
        if isinstance(noeud, ast.FunctionDef) and noeud.name == "hex_to_rgb"
    )
    module = ast.Module(body=[fonction], type_ignores=[])
    ast.fix_missing_locations(module)
    espace = {}
    exec(compile(module, str(FICHIER), "exec"), espace)
    return espace["hex_to_rgb"]


class UtilsImagesConversionTests(unittest.TestCase):
    def test_hex_to_rgb_fonctionne_sous_python_3(self):
        convertir = _charger_hex_to_rgb()

        self.assertEqual(convertir("#336699"), (51, 102, 153))
        self.assertEqual(convertir("FFFFFF"), (255, 255, 255))


if __name__ == "__main__":
    unittest.main()
