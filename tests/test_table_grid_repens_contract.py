# -*- coding: utf-8 -*-
"""Contrats statiques de la couche tableaux/grilles Repens."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE = ROOT / "noethys" / "Utils" / "UTILS_StyleRepens.py"
AUI = ROOT / "noethys" / "Utils" / "UTILS_Aui.py"
TABLEAU = ROOT / "noethys" / "Ctrl" / "CTRL_TableauResponsive.py"


class TableGridRepensContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.style_text = STYLE.read_text(encoding="utf-8")
        cls.aui_text = AUI.read_text(encoding="utf-8")
        cls.tableau_text = TABLEAU.read_text(encoding="utf-8")
        for texte in (cls.style_text, cls.aui_text, cls.tableau_text):
            ast.parse(texte)

    def test_grid_style_is_owned_by_repens_facade(self):
        self.assertIn("def appliquer_grille", self.style_text)
        self.assertIn('SetLabelFont", police("label")', self.style_text)
        self.assertIn('SetSelectionBackground", couleur("selection")', self.style_text)
        self.assertIn('SetSelectionForeground", couleur("selection_text")', self.style_text)
        self.assertIn('hauteur_ligne("table")', self.style_text)
        self.assertNotIn("wx.Colour(", self.style_text)

    def test_aui_grid_adapter_delegates_without_business_geometry(self):
        debut = self.aui_text.index("def ConfigurerGrille")
        fin = self.aui_text.index("\ndef ConfigurerNotebook", debut)
        bloc = self.aui_text[debut:fin]
        self.assertIn("UTILS_StyleRepens as Style", bloc)
        self.assertIn("Style.appliquer_grille(grille)", bloc)
        self.assertNotIn("UTILS_Interface", bloc)
        self.assertNotIn("UTILS_UIMetrics", bloc)
        self.assertNotIn("SetColSize", bloc)
        self.assertNotIn("SetRowSize", bloc)

    def test_responsive_table_uses_semantic_zebra_rows(self):
        self.assertIn("def _StyliserLigne", self.tableau_text)
        self.assertIn('"surface_container_lowest" if index % 2 == 0 else "surface_container_low"', self.tableau_text)
        self.assertIn('Style.couleur("on_surface")', self.tableau_text)
        self.assertNotIn("wx.Colour(", self.tableau_text)

    def test_search_and_count_are_above_the_data_surface(self):
        self.assertIn("self.barre_donnees = wx.Panel", self.tableau_text)
        self.assertIn("self.recherche.SetMaxSize((Style.px(360), -1))", self.tableau_text)
        position_barre = self.tableau_text.index("sizer.Add(self.barre_donnees")
        position_tableau = self.tableau_text.index("sizer.Add(self.tableau", position_barre)
        self.assertLess(position_barre, position_tableau)
        self.assertNotIn("wx.FlexGridSizer(", self.tableau_text)
        self.assertNotIn("wx.GridSizer(", self.tableau_text)


if __name__ == "__main__":
    unittest.main()
