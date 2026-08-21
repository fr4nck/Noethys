# -*- coding: utf-8 -*-
"""Contrats des métriques sémantiques pour les surfaces Repens."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepensSurfaceMetricsContractTests(unittest.TestCase):
    def _read(self, relative_path):
        path = ROOT / relative_path
        text = path.read_text(encoding="utf-8")
        ast.parse(text)
        return text

    def test_surface_uses_semantic_defaults_from_stylesheet(self):
        text = self._read("noethys/Ctrl/CTRL_SurfaceRepens.py")
        self.assertIn('return Style.espace(2)', text)
        self.assertIn('return Style.rayon("surface")', text)
        self.assertIn('rayon=None', text)
        self.assertIn('padding=None', text)
        self.assertNotIn('self.rayon_base = rayon', text)
        self.assertNotIn('self.padding_base = padding', text)

    def test_window_sections_do_not_redeclare_surface_geometry(self):
        text = self._read("noethys/Ctrl/CTRL_FenetreRepens.py")
        self.assertIn("CTRL_SurfaceRepens.CTRL.__init__", text)
        self.assertNotIn("rayon=9", text)
        self.assertNotIn("padding=8", text)
        self.assertIn("marge = self.GetPadding()", text)


if __name__ == "__main__":
    unittest.main()
