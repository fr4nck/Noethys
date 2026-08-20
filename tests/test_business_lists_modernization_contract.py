# -*- coding: utf-8 -*-
"""Contrats statiques des listes métier courantes."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BusinessListsModernizationContractTests(unittest.TestCase):
    def _read(self, relative_path):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        ast.parse(text)
        return text

    def test_common_lists_use_named_actions_and_box_layout(self):
        for relative_path in (
            "noethys/Ctrl/CTRL_Liste_factures.py",
            "noethys/Ctrl/CTRL_Liste_cotisations.py",
            "noethys/Ctrl/CTRL_Liste_inscriptions.py",
            "noethys/Ctrl/CTRL_Liste_locations.py",
            "noethys/Ctrl/CTRL_Liste_locations_demandes.py",
        ):
            text = self._read(relative_path)
            self.assertIn("CTRL_Bouton_image.CTRL", text)
            self.assertIn("UTILS_Interface", text)
            self.assertIn("UTILS_UIMetrics", text)
            self.assertIn("wx.BoxSizer(wx.HORIZONTAL)", text)
            self.assertIn("wx.BoxSizer(wx.VERTICAL)", text)
            self.assertNotIn("wx.BitmapButton", text)
            self.assertNotIn("FlexGridSizer", text)
            self.assertNotIn("GridSizer", text)

    def test_invoice_list_replaces_blue_hyperlinks_with_action_buttons(self):
        text = self._read("noethys/Ctrl/CTRL_Liste_factures.py")
        self.assertNotIn("HyperLinkCtrl", text)
        self.assertIn("def OnBoutonTout", text)
        self.assertIn("def OnBoutonRien", text)
        self.assertIn("CocheListeTout()", text)
        self.assertIn("CocheListeRien()", text)

    def test_location_filters_use_scaled_system_text(self):
        for relative_path in (
            "noethys/Ctrl/CTRL_Liste_locations.py",
            "noethys/Ctrl/CTRL_Liste_locations_demandes.py",
        ):
            text = self._read(relative_path)
            self.assertIn("wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)", text)
            self.assertIn("UTILS_Interface.GetTailleTexte()", text)
            self.assertNotIn("wx.Font(8,", text)

    def test_business_actions_preserve_underlying_list_operations(self):
        expectations = {
            "noethys/Ctrl/CTRL_Liste_factures.py": (
                "Reedition(None)", "EnvoyerEmail(None)", "Supprimer(None)",
                "Apercu(None)", "Imprimer(None)", "ExportTexte(None)", "ExportExcel(None)",
            ),
            "noethys/Ctrl/CTRL_Liste_cotisations.py": (
                "Reedition(None)", "EnvoyerEmail(None)", "Supprimer(None)",
                "Apercu(None)", "Imprimer(None)", "ExportTexte(None)", "ExportExcel(None)",
            ),
            "noethys/Ctrl/CTRL_Liste_inscriptions.py": (
                "ImprimerPDF(None)", "EnvoyerEmail(None)",
                "Apercu(None)", "Imprimer(None)", "ExportTexte(None)", "ExportExcel(None)",
            ),
            "noethys/Ctrl/CTRL_Liste_locations.py": (
                "Reedition(None)", "EnvoyerEmail(None)", "Supprimer(None)",
                "Apercu(None)", "Imprimer(None)", "ExportTexte(None)", "ExportExcel(None)",
            ),
            "noethys/Ctrl/CTRL_Liste_locations_demandes.py": (
                "Reedition(None)", "EnvoyerEmail(None)", "Supprimer(None)",
                "Apercu(None)", "Imprimer(None)", "ExportTexte(None)", "ExportExcel(None)",
            ),
        }
        for relative_path, tokens in expectations.items():
            text = self._read(relative_path)
            for token in tokens:
                self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
