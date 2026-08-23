# -*- coding: utf-8 -*-
"""Contrats statiques de la barre d'outils commune des listes Repens."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ListToolsRepensContractTests(unittest.TestCase):
    def _read(self):
        path = ROOT / "noethys/Ctrl/CTRL_OutilsListeRepens.py"
        text = path.read_text(encoding="utf-8")
        ast.parse(text)
        return text

    def test_toolbar_uses_repens_actions_and_no_legacy_16px_assets(self):
        text = self._read()
        self.assertIn("CTRL_ActionRepens.CTRL", text)
        self.assertIn('icone="filter"', text)
        self.assertIn('icone="check"', text)
        self.assertNotIn("wx.lib.platebtn", text)
        self.assertNotIn("Chemins.GetStaticPath", text)
        self.assertNotIn("Images/16x16", text)

    def test_search_is_native_semantic_and_bounded_on_wide_screens(self):
        text = self._read()
        self.assertIn("class BarreRecherche(wx.SearchCtrl)", text)
        self.assertIn("Style.appliquer_saisie(self)", text)
        self.assertIn("self.SetMinSize((Style.px(180), Style.cible_action(\"compact\")))", text)
        self.assertIn("self.SetMaxSize((Style.px(360), -1))", text)
        self.assertIn('UTILS_IconesRepens.GetBitmap(\n                    "search"', text)
        self.assertIn('UTILS_IconesRepens.GetBitmap(\n                    "dismiss"', text)

    def test_layout_does_not_stretch_search_field_across_the_workspace(self):
        text = self._read()
        self.assertIn("sizer.Add(self.barreRecherche, 0,", text)
        self.assertIn("sizer.AddStretchSpacer(1)", text)
        self.assertNotIn("sizer.Add(self.barreRecherche, 1,", text)

    def test_historical_list_contracts_are_preserved(self):
        text = self._read()
        for marker in (
            "SetBarreRecherche",
            "SetFiltresColonnes",
            "Filtrer",
            "CocheListeTout",
            "CocheListeRien",
            "ctrl_regroupement",
            "regroupement",
        ):
            self.assertIn(marker, text)
        self.assertIn("DLG_Filtres_listes.Dialog", text)
        self.assertIn("Filtrer (%d)", text)


if __name__ == "__main__":
    unittest.main()
