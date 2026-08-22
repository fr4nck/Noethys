# -*- coding: utf-8 -*-
"""Contrats statiques des sélecteurs métier modernisés."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SelectionControlsModernizationContractTests(unittest.TestCase):
    def _read(self, relative_path):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        ast.parse(text)
        return text

    def test_deposit_selector_is_semantic_and_tracks_available_width(self):
        text = self._read("noethys/Ctrl/CTRL_Selection_depots.py")
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn('Style.couleur("surface_container_lowest")', text)
        self.assertIn('Style.couleur("on_surface")', text)
        self.assertIn("wx.EVT_SIZE", text)
        self.assertIn("GetClientSize().GetWidth()", text)
        self.assertIn("wx.CallAfter(self._AjusterLargeur)", text)
        self.assertNotIn("SetColumnWidth(0, 400)", text)
        self.assertNotIn("wx.WHITE", text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)

    def test_deposit_year_sort_is_python3_safe(self):
        text = self._read("noethys/Ctrl/CTRL_Selection_depots.py")
        self.assertIn("sorted(dictDepots.keys(), key=", text)
        self.assertNotIn("listeAnnees.sort()", text)

    def test_registered_present_selector_uses_semantic_lists_and_box_sizers(self):
        text = self._read("noethys/Ctrl/CTRL_Selection_inscrits_presents.py")
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn("Style.appliquer_liste(ctrl)", text)
        self.assertIn('Style.appliquer_fenetre(self, "surface")', text)
        self.assertIn("wx.BoxSizer(wx.HORIZONTAL)", text)
        self.assertIn("wx.BoxSizer(wx.VERTICAL)", text)
        self.assertNotIn("wx.FlexGridSizer(", text)
        self.assertNotIn("SetMinSize((10, 10))", text)
        self.assertNotIn("SetMinSize((10, 100))", text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)

    def test_registered_present_business_callbacks_are_preserved(self):
        text = self._read("noethys/Ctrl/CTRL_Selection_inscrits_presents.py")
        for token in (
            "def GetSQLdates",
            "def SetListesPeriodes",
            "def SetGroupes",
            "def SetModePresents",
            "def GetParametres",
            "ctrl_calendrier.GetDatesSelections()",
            "ctrl_activites_inscrits.GetActivites()",
            "ctrl_activites_presents.GetListeActivites()",
            "ctrl_groupes.GetListeGroupes()",
        ):
            self.assertIn(token, text)

    def test_period_grid_selector_is_semantic_and_not_grid_locked(self):
        text = self._read("noethys/Ctrl/CTRL_Grille_periode.py")
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn('Style.cible_action("compact")', text)
        self.assertIn('Style.appliquer_fenetre(panel, "surface")', text)
        self.assertIn("wx.BoxSizer(wx.VERTICAL)", text)
        self.assertIn("wx.BoxSizer(wx.HORIZONTAL)", text)
        self.assertNotIn("wx.FlexGridSizer(", text)
        self.assertNotIn("wx.GridSizer(", text)
        self.assertNotIn("SetMinSize((60, -1))", text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)

    def test_period_grid_scrolls_months_and_holidays_not_year_page(self):
        text = self._read("noethys/Ctrl/CTRL_Grille_periode.py")
        self.assertIn("if indexPage in (0, 1):", text)
        self.assertNotIn("if indexPage in (0, 2):", text)

    def test_internet_account_summary_uses_semantic_status_and_scalable_text_indicator(self):
        text = self._read("noethys/Ctrl/CTRL_Compte_internet.py")
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn('wx.StaticText(self, -1, u"●")', text)
        self.assertIn('role_statut = "success_text"', text)
        self.assertIn('role_statut = "danger_text"', text)
        self.assertIn("Style.couleur(role_statut)", text)
        self.assertIn('Style.police("body_emphasis")', text)
        self.assertNotIn("wx.SystemSettings.GetColour(30)", text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)


if __name__ == "__main__":
    unittest.main()
