# -*- coding: utf-8 -*-
"""Contrat statique du pack d'icônes modernes Noethys."""

import ast
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHEMINS = ROOT / "noethys" / "Chemins.py"
ICONES = ROOT / "noethys" / "Utils" / "UTILS_Icones_modernes.py"


class ModernIconsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chemins_text = CHEMINS.read_text(encoding="utf-8")
        cls.icones_text = ICONES.read_text(encoding="utf-8")
        ast.parse(cls.chemins_text)
        ast.parse(cls.icones_text)

        spec = importlib.util.spec_from_file_location("noethys_modern_icons_contract", ICONES)
        cls.icones = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.icones)

    def test_static_path_only_intercepts_common_icon_sizes(self):
        self.assertIn('normalise.startswith("Images/16x16/")', self.chemins_text)
        self.assertIn('normalise.startswith("Images/32x32/")', self.chemins_text)
        self.assertIn("GetLegacyOverridePath(normalise)", self.chemins_text)
        self.assertIn("return os.path.join(chemin, fichier)", self.chemins_text)

    def test_legacy_escape_hatch_is_preserved(self):
        self.assertIn('NOETHYS_LEGACY_ICONS', self.chemins_text)

    def test_main_toolbar_legacy_icons_have_modern_equivalents(self):
        attendus = {
            "Images/16x16/Calendrier.png": "calendar",
            "Images/16x16/Imprimante.png": "printer",
            "Images/16x16/Badgeage.png": "badge",
            "Images/16x16/Reglement.png": "payment",
            "Images/16x16/Calculatrice.png": "calculator",
            "Images/16x16/Homme.png": "user",
        }
        for chemin, icone in attendus.items():
            self.assertEqual(self.icones._icone_pour_chemin(chemin), icone)

    def test_unrecognized_business_art_keeps_historical_resource(self):
        self.assertIsNone(self.icones._icone_pour_chemin("Images/32x32/LogoAssociationTresSpecifique.png"))

    def test_generator_is_wx_independent_and_cached_outside_installation(self):
        self.assertNotIn("import wx", self.icones_text)
        self.assertIn("tempfile.gettempdir()", self.icones_text)
        self.assertIn("return None", self.icones_text)


if __name__ == "__main__":
    unittest.main()
