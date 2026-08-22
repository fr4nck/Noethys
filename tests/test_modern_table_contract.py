# -*- coding: utf-8 -*-
"""Contrats du tableau moderne et de l'iconographie Fluent."""

import ast
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COLONNES = ROOT / "noethys" / "Utils" / "UTILS_ColonnesResponsive.py"
FLUENT = ROOT / "noethys" / "Utils" / "UTILS_FluentIcons.py"
TABLEAU = ROOT / "noethys" / "Ctrl" / "CTRL_TableauResponsive.py"
INDIVIDUS = ROOT / "noethys" / "Ctrl" / "CTRL_Recherche_individus.py"


class ModernTableContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.colonnes_text = COLONNES.read_text(encoding="utf-8")
        cls.fluent_text = FLUENT.read_text(encoding="utf-8")
        cls.tableau_text = TABLEAU.read_text(encoding="utf-8")
        cls.individus_text = INDIVIDUS.read_text(encoding="utf-8")
        for texte in (cls.colonnes_text, cls.fluent_text, cls.tableau_text, cls.individus_text):
            ast.parse(texte)

        spec = importlib.util.spec_from_file_location("colonnes_responsive", str(COLONNES))
        cls.colonnes = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.colonnes)

    def test_weighted_columns_keep_minimum_when_narrow(self):
        specs = [(120, 1), (80, 0), (200, 2)]
        self.assertEqual(self.colonnes.CalculerLargeurs(300, specs, marge=0), [120, 80, 200])

    def test_weighted_columns_consume_available_width(self):
        specs = [(100, 1), (100, 0), (100, 3)]
        result = self.colonnes.CalculerLargeurs(500, specs, marge=0)
        self.assertEqual(sum(result), 500)
        self.assertEqual(result[1], 100)
        self.assertGreater(result[2], result[0])

    def test_responsive_columns_are_explicit_not_monkey_patched(self):
        self.assertIn("def Installer(controle, specs", self.colonnes_text)
        self.assertIn("wx.EVT_SIZE", self.colonnes_text)
        self.assertIn("wx.CallAfter", self.colonnes_text)
        self.assertNotIn("setattr(wx", self.colonnes_text)

    def test_fluent_catalog_is_opt_in_and_vector(self):
        self.assertIn("Microsoft Fluent UI System Icons", self.fluent_text)
        self.assertIn("wx.svg", self.fluent_text)
        self.assertIn('"add":', self.fluent_text)
        self.assertIn('"edit":', self.fluent_text)
        self.assertIn('"delete":', self.fluent_text)
        self.assertIn('"calendar":', self.fluent_text)
        self.assertIn('"people":', self.fluent_text)
        self.assertIn('"settings":', self.fluent_text)
        self.assertIn("GetCouleurRole(role)", self.fluent_text)
        self.assertNotIn("GetLegacyOverridePath", self.fluent_text)

    def test_new_table_component_uses_native_desktop_controls_and_repens_actions(self):
        self.assertIn("class PanneauTableau(wx.Panel)", self.tableau_text)
        self.assertIn("class ListeTableau(wx.ListCtrl)", self.tableau_text)
        self.assertIn("wx.SearchCtrl", self.tableau_text)
        self.assertIn("CTRL_ActionRepens.CTRL", self.tableau_text)
        self.assertIn("UTILS_ColonnesResponsive.Installer", self.tableau_text)
        self.assertNotIn("wx.FlexGridSizer(", self.tableau_text)
        self.assertNotIn("wx.GridSizer(", self.tableau_text)

    def test_individuals_screen_uses_repens_common_primitives(self):
        self.assertIn("UTILS_ColonnesResponsive.Installer", self.individus_text)
        self.assertIn("UTILS_IconesRepens.GetBitmap", self.individus_text)
        self.assertIn("CTRL_ActionRepens.CTRL", self.individus_text)
        self.assertNotIn("Famille_ajouter.png\", \"tooltip", self.individus_text)
        self.assertNotIn("def _AjusteColonnes", self.individus_text)


if __name__ == "__main__":
    unittest.main()
