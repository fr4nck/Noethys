# -*- coding: utf-8 -*-
"""Contrats statiques des listes arborescentes et rendues migrées vers Repens Design."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepensTreeListsContractTests(unittest.TestCase):
    def _read(self, relative_path):
        path = ROOT / relative_path
        text = path.read_text(encoding="utf-8")
        ast.parse(text)
        return text

    def test_present_consumption_tree_uses_repens_stylesheet(self):
        text = self._read("noethys/Ctrl/CTRL_Liste_presents.py")
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn("Style.appliquer_liste(self)", text)
        self.assertIn('Style.couleur("surface_container")', text)
        self.assertIn("Style.px(250)", text)
        self.assertNotIn("SetBackgroundColour(wx.WHITE)", text)
        self.assertNotIn("UTILS_Linux.AdaptePolice", text)
        self.assertNotIn("CTRL_Bouton_image", text)

    def test_file_list_keeps_custom_renderer_but_uses_repens_tokens(self):
        text = self._read("noethys/Ctrl/CTRL_Liste_fichiers.py")
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn("Style.appliquer_liste(self)", text)
        self.assertIn('Style.police("body_emphasis")', text)
        self.assertIn('Style.police("body_small")', text)
        self.assertIn('Style.couleur("on_surface_variant")', text)
        self.assertIn('Style.taille_icone("hero")', text)
        self.assertNotIn("wx.SystemSettings.GetFont", text)
        self.assertNotIn("wx.SystemSettings.GetColour", text)
        self.assertNotIn("wx.BLACK", text)

    def test_consumption_totals_grid_uses_repens_facade(self):
        text = self._read("noethys/Ctrl/CTRL_Grille_totaux.py")
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn("Style.appliquer_liste(self)", text)
        self.assertIn('Style.couleur("surface_container_high")', text)
        self.assertIn('Style.couleur("danger")', text)
        self.assertIn("Style.cible_action(\"compact\")", text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)
        self.assertNotIn("wx.SystemSettings.GetFont", text)


if __name__ == "__main__":
    unittest.main()
