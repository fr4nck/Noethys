# -*- coding: utf-8 -*-
"""Garde-fous d'architecture des contrôles transversaux migrés vers Repens."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepensSharedControlsContractTests(unittest.TestCase):
    def _read(self, relative_path):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        ast.parse(text)
        return text

    def test_shared_controls_consume_repens_facade_only(self):
        for relative_path in (
            "noethys/Ctrl/CTRL_TableauResponsive.py",
            "noethys/Ctrl/CTRL_Ticker_presents.py",
            "noethys/Ctrl/CTRL_Portail_messages.py",
            "noethys/Ctrl/CTRL_Saisie_adresse.py",
            "noethys/Ctrl/CTRL_Planning_semaine.py",
        ):
            text = self._read(relative_path)
            self.assertIn("UTILS_StyleRepens as Style", text)
            self.assertNotIn("UTILS_Interface", text)
            self.assertNotIn("UTILS_UIMetrics", text)

    def test_responsive_table_uses_repens_actions_and_drops_vertical_grid_lines(self):
        text = self._read("noethys/Ctrl/CTRL_TableauResponsive.py")
        self.assertIn("CTRL_ActionRepens", text)
        self.assertIn("Style.appliquer_liste(self)", text)
        self.assertIn("Style.appliquer_saisie(self.recherche)", text)
        self.assertNotIn("UTILS_FluentIcons", text)
        self.assertNotIn("wx.LC_VRULES", text)

    def test_teamworks_week_uses_repens_navigation_without_changing_data_source(self):
        text = self._read("noethys/Ctrl/CTRL_Planning_semaine.py")
        self.assertIn("CTRL_ActionRepens", text)
        self.assertIn('icone="arrow_left"', text)
        self.assertIn('icone="arrow_right"', text)
        self.assertIn('icone="calendar"', text)
        self.assertIn("UTILS_Teamworks_Planning.GetSemaine", text)
        self.assertIn("threading.Thread", text)
        self.assertNotIn("wx.Button", text)

    def test_address_editor_uses_repens_search_action(self):
        text = self._read("noethys/Ctrl/CTRL_Saisie_adresse.py")
        self.assertIn("CTRL_ActionRepens", text)
        self.assertIn('icone="search"', text)
        self.assertIn("Style.appliquer_saisie(ctrl)", text)
        self.assertNotIn("CTRL_Bouton_image", text)
        self.assertNotIn("_PoliceInterface", text)

    def test_semantic_trees_keep_business_icons_but_scale_them(self):
        for relative_path in (
            "noethys/Ctrl/CTRL_Stats_objets.py",
            "noethys/Ctrl/CTRL_Filtres_transports.py",
        ):
            text = self._read(relative_path)
            self.assertIn("UTILS_StyleRepens as Style", text)
            self.assertIn("Style.appliquer_liste(self)", text)
            self.assertIn('Style.taille_icone("inline")', text)
            self.assertNotIn("wx.WHITE", text)


if __name__ == "__main__":
    unittest.main()
