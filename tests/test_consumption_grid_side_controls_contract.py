# -*- coding: utf-8 -*-
"""Contrats statiques des contrôles latéraux de la grille de consommations."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ConsumptionGridSideControlsContractTests(unittest.TestCase):
    def _read(self, relative_path):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        ast.parse(text)
        return text

    def test_family_individual_selector_is_semantic_and_not_grid_locked(self):
        text = self._read("noethys/Ctrl/CTRL_Grille_individus.py")
        self.assertIn("UTILS_Interface", text)
        self.assertIn("UTILS_UIMetrics", text)
        self.assertIn('GetCouleurRole("surface_container_high")', text)
        self.assertIn('GetCouleurRole("surface_container_lowest")', text)
        self.assertIn("html_std.escape", text)
        self.assertIn("wx.BoxSizer(wx.VERTICAL)", text)
        self.assertNotIn("FlexGridSizer", text)
        self.assertNotIn('couleurFond="#316AC5"', text)
        self.assertNotIn("SetDisabledTextColour(wx.Colour(255, 0, 0))", text)

    def test_family_names_handle_three_or_more_holders_without_legacy_bug(self):
        text = self._read("noethys/Ctrl/CTRL_Grille_individus.py")
        self.assertIn('u", ".join(listeTitulaires[:-1])', text)
        self.assertNotIn("listeTitulaires[:-2]", text)

    def test_grid_totals_use_semantic_surfaces_and_responsive_columns(self):
        text = self._read("noethys/Ctrl/CTRL_Grille_totaux.py")
        self.assertIn("UTILS_Interface", text)
        self.assertIn("UTILS_UIMetrics", text)
        self.assertIn('GetCouleurRole("surface_container_high")', text)
        self.assertIn('GetCouleurRole("danger")', text)
        self.assertIn("GetClientSize().GetWidth()", text)
        self.assertIn("wx.EVT_SIZE", text)
        self.assertNotIn("wx.Colour(200, 200, 200)", text)
        self.assertNotIn("wx.RED", text)
        self.assertNotIn("SetColumnWidth(numColonne, largeur)", text)

    def test_grid_totals_preserve_data_sources_and_total_calculation(self):
        text = self._read("noethys/Ctrl/CTRL_Grille_totaux.py")
        for token in (
            "self.grille.dictGroupes",
            "self.grille.dictActivites",
            "self.grille.dictListeUnites",
            "self.grille.dictRemplissage2",
            "self.grille.dictConsoUnites",
            'd.get("reservation", 0)',
            'd.get("present", 0)',
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
