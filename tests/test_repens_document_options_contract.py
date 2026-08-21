# -*- coding: utf-8 -*-
"""Contrat d'architecture des panneaux d'options documentaires Repens."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepensDocumentOptionsContractTests(unittest.TestCase):
    def _read(self, relative_path):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        ast.parse(text)
        return text

    def test_document_option_panels_use_repens_facade_and_actions(self):
        for relative_path in (
            "noethys/Ctrl/CTRL_Cotisations_options.py",
            "noethys/Ctrl/CTRL_Rappels_options.py",
            "noethys/Ctrl/CTRL_Inscriptions_options.py",
            "noethys/Ctrl/CTRL_Locations_options.py",
            "noethys/Ctrl/CTRL_Locations_demandes_options.py",
        ):
            text = self._read(relative_path)
            self.assertIn("UTILS_StyleRepens as Style", text)
            self.assertIn("CTRL_ActionRepens", text)
            self.assertIn('Style.appliquer_fenetre(self, "surface")', text)
            self.assertIn("Style.espace(", text)
            self.assertNotIn("UTILS_Interface", text)
            self.assertNotIn("UTILS_UIMetrics", text)
            self.assertNotIn("CTRL_Bouton_image", text)
            self.assertNotIn("wx.BitmapButton", text)
            self.assertNotIn("FlexGridSizer", text)

    def test_questionnaire_option_panels_style_native_choices(self):
        for relative_path in (
            "noethys/Ctrl/CTRL_Inscriptions_options.py",
            "noethys/Ctrl/CTRL_Locations_options.py",
            "noethys/Ctrl/CTRL_Locations_demandes_options.py",
        ):
            text = self._read(relative_path)
            self.assertIn("class CTRL_Question(wx.Choice)", text)
            self.assertIn("Style.appliquer_saisie(self)", text)
            self.assertIn("Style.appliquer_saisie(self.ctrl_questionnaire)", text)


if __name__ == "__main__":
    unittest.main()
