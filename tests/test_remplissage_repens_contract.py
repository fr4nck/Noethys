# -*- coding: utf-8 -*-
"""Contrat statique du tableau de fréquentation Repens.

Le test ne charge pas wxPython : il garantit que le cockpit construit le
nouveau panneau directement, que son rendu est sémantique/arrondi et qu'il ne
réintroduit ni anciens RGB criards ni faux relief 3D.
"""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPENS = ROOT / "noethys" / "Ctrl" / "CTRL_Remplissage_Repens.py"
PANEL = ROOT / "noethys" / "Dlg" / "DLG_Remplissage_Repens.py"
EFFECTIFS = ROOT / "noethys" / "Dlg" / "DLG_Effectifs.py"


class RemplissageRepensContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repens = REPENS.read_text(encoding="utf-8")
        cls.panel = PANEL.read_text(encoding="utf-8")
        cls.effectifs = EFFECTIFS.read_text(encoding="utf-8")
        ast.parse(cls.repens)
        ast.parse(cls.panel)
        ast.parse(cls.effectifs)

    def test_dashboard_uses_complete_repens_panel(self):
        self.assertIn("from Dlg import DLG_Remplissage_Repens as DLG_Remplissage", self.effectifs)
        self.assertIn("DLG_Remplissage.Panel(self.notebook)", self.effectifs)
        self.assertIn("class Panel(wx.Panel)", self.panel)
        self.assertIn("CTRL_Remplissage_Repens.CTRL", self.panel)

    def test_panel_is_built_directly_without_creating_legacy_widgets_first(self):
        self.assertNotIn("class Panel(Legacy.Panel)", self.panel)
        self.assertNotIn("Legacy.Panel.__init__", self.panel)
        self.assertNotIn("ancienne_toolbar", self.panel)
        self.assertNotIn("ancienne_grille", self.panel)
        self.assertIn("CTRL_Ticker_presents.CTRL", self.panel)
        self.assertIn("wx.BoxSizer(wx.VERTICAL)", self.panel)

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

    def test_toolbar_uses_explicit_fluent_icons_and_semantic_surface(self):
        self.assertIn("UTILS_FluentIcons.GetBitmap", self.panel)
        self.assertIn('GetCouleurRole("surface_container_low")', self.panel)
        self.assertIn("wx.TB_FLAT", self.panel)
        self.assertIn("AddStretchableSpace", self.panel)


if __name__ == "__main__":
    unittest.main()
