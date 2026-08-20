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

    def test_static_path_intercepts_only_common_icon_folders(self):
        for size in (16, 20, 24, 32, 40, 48):
            self.assertIn('"Images/{0}x{0}/"'.format(size), self.chemins_text)
        self.assertIn("normalise.startswith(dossiers)", self.chemins_text)
        self.assertIn("GetStaticIconPath", self.chemins_text)
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
        }
        for chemin, icone in attendus.items():
            self.assertEqual(self.icones._icone_pour_chemin(chemin), icone)

    def test_agenda_navigation_has_distinct_modern_icons(self):
        attendus = {
            "Images/32x32/Calendrier_jour.png": "calendar_day",
            "Images/32x32/Calendrier_semaine.png": "calendar_week",
            "Images/32x32/Calendrier_mois.png": "calendar_month",
            "Images/32x32/Calendrier_horizontal.png": "layout_horizontal",
            "Images/32x32/Calendrier_vertical.png": "layout_vertical",
            "Images/32x32/Precedent.png": "previous",
            "Images/32x32/Suivant.png": "next",
            "Images/32x32/zoom_moins.png": "zoom_out",
            "Images/32x32/zoom_plus.png": "zoom_in",
            "Images/32x32/Jour.png": "today",
            "Images/32x32/Calendrier_zoom.png": "calendar_search",
            "Images/32x32/Apercu.png": "preview",
        }
        for chemin, icone in attendus.items():
            self.assertEqual(self.icones._icone_pour_chemin(chemin), icone)

    def test_short_tokens_do_not_match_arbitrary_substrings(self):
        self.assertIsNone(self.icones._icone_pour_chemin("Images/16x16/Hotel.png"))
        self.assertIsNone(self.icones._icone_pour_chemin("Images/16x16/ProfilExpert.png"))
        self.assertEqual(self.icones._icone_pour_chemin("Images/16x16/Tel.png"), "phone")

    def test_requested_target_size_reaches_generic_modern_pack(self):
        self.assertIn("GetLegacyOverridePath(normalise, taille=taille_cible)", self.chemins_text)
        self.assertIn("def GetLegacyOverridePath(chemin, taille=None):", self.icones_text)
        self.assertIn("(16, 20, 24, 32, 40, 48)", self.icones_text)

    def test_identity_layer_is_resolved_before_generic_icons(self):
        self.assertLess(
            self.chemins_text.index("UTILS_Icones_identites"),
            self.chemins_text.index("UTILS_Icones_adaptatives"),
        )

    def test_unrecognized_business_art_keeps_historical_resource(self):
        self.assertIsNone(self.icones._icone_pour_chemin("Images/32x32/LogoAssociationTresSpecifique.png"))

    def test_generator_is_wx_independent_and_cached_outside_installation(self):
        self.assertNotIn("import wx", self.icones_text)
        self.assertIn("tempfile.gettempdir()", self.icones_text)
        self.assertIn("return None", self.icones_text)


if __name__ == "__main__":
    unittest.main()
