# -*- coding: utf-8 -*-
"""Contrat statique du tableau de fréquentation Repens.

Le test ne charge pas wxPython : il garantit que le cockpit utilise le nouveau
renderer et que son rendu est sémantique, arrondi et indépendant des anciens
RGB criards.
"""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPENS = ROOT / "noethys" / "Ctrl" / "CTRL_Remplissage_Repens.py"
EFFECTIFS = ROOT / "noethys" / "Dlg" / "DLG_Effectifs.py"


class RemplissageRepensContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repens = REPENS.read_text(encoding="utf-8")
        cls.effectifs = EFFECTIFS.read_text(encoding="utf-8")
        ast.parse(cls.repens)
        ast.parse(cls.effectifs)

    def test_dashboard_uses_repens_grid(self):
        self.assertIn("from Ctrl import CTRL_Remplissage_Repens", self.effectifs)
        self.assertIn("CTRL_Remplissage_Repens.CreerPanel", self.effectifs)
        self.assertNotIn("from Dlg import DLG_Remplissage\n", self.effectifs)

    def test_renderer_uses_semantic_repens_states(self):
        for role in (
            '"success"', '"warning"', '"danger"', '"info"',
            '"surface_container_low"', '"primary_container"',
        ):
            self.assertIn(role, self.repens)

    def test_cells_are_rounded_and_old_3d_border_is_not_reimplemented(self):
        self.assertIn("DrawRoundedRectangle", self.repens)
        self.assertNotIn("SYS_COLOUR_3DSHADOW", self.repens)
        self.assertNotIn("wx.WHITE_PEN", self.repens)
        self.assertNotIn("DrawBorder", self.repens)

    def test_renderer_does_not_copy_legacy_literal_colours(self):
        for literal in (
            "E3FEDB", "FEFCDB", "F7ACB2", "YELLOW", "RED",
            "252, 213, 0", "205, 144, 233",
        ):
            self.assertNotIn(literal, self.repens)

    def test_repens_subclass_keeps_business_grid_instead_of_monkey_patching_it(self):
        self.assertIn("class CTRL(Legacy.CTRL)", self.repens)
        self.assertIn("Legacy.CTRL.InitGrid(self)", self.repens)
        self.assertIn("self.SetCellRenderer(row, col, renderer)", self.repens)
        self.assertNotIn("Legacy.RendererCase =", self.repens)
        self.assertNotIn("CTRL_Remplissage.RendererCase =", self.repens)


if __name__ == "__main__":
    unittest.main()
