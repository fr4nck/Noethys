# -*- coding: utf-8 -*-
"""Contrats statiques des contrôles de saisie migrés vers Repens Design."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepensInputsContractTests(unittest.TestCase):
    def _read(self, relative_path):
        path = ROOT / relative_path
        text = path.read_text(encoding="utf-8")
        ast.parse(text)
        return text

    def test_country_selector_uses_repens_facade_and_action(self):
        text = self._read("noethys/Ctrl/CTRL_Saisie_pays.py")
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn("CTRL_ActionRepens", text)
        self.assertIn('icone="edit"', text)
        self.assertIn('Style.taille_icone("inline")', text)
        self.assertIn('Style.appliquer_fenetre(self, "surface")', text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)
        self.assertNotIn("CTRL_Bouton_image", text)

    def test_bank_statement_selector_uses_repens_action(self):
        text = self._read("noethys/Ctrl/CTRL_Saisie_releve_bancaire.py")
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn("CTRL_ActionRepens", text)
        self.assertIn("Style.appliquer_saisie(self)", text)
        self.assertIn('icone="edit"', text)
        self.assertNotIn("CTRL_Bouton_image", text)


if __name__ == "__main__":
    unittest.main()
