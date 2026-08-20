# -*- coding: utf-8 -*-
"""Contrat statique des adaptations de toolbar desktop."""

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUI = ROOT / "noethys" / "Utils" / "UTILS_Aui.py"
RESPONSIVE = ROOT / "noethys" / "Utils" / "UTILS_Responsive.py"


class ResponsiveToolbarContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.aui_text = AUI.read_text(encoding="utf-8")
        cls.responsive_text = RESPONSIVE.read_text(encoding="utf-8")
        ast.parse(cls.aui_text)
        ast.parse(cls.responsive_text)

    def test_agw_toolbars_request_plain_background(self):
        self.assertIn("AUI_TB_PLAIN_BACKGROUND", self.aui_text)
        self.assertIn("SetBackgroundColour", self.aui_text)

    def test_both_toolbar_families_use_responsive_bitmap_sizes(self):
        self.assertIn("aui.AuiToolBar.SetToolBitmapSize", self.aui_text)
        self.assertIn("wx.ToolBar.SetToolBitmapSize", self.aui_text)
        self.assertIn("UTILS_Responsive.AdapterTailleWx", self.aui_text)

    def test_responsive_rules_are_capped_and_step_based(self):
        self.assertIn("def GetTailleIcone", self.responsive_text)
        self.assertIn("return 20", self.responsive_text)
        self.assertIn("return 24", self.responsive_text)
        self.assertIn("return 40", self.responsive_text)
        self.assertIn("min(48", self.responsive_text)
        self.assertIn("wx.GetDisplayPPI()", self.responsive_text)
        self.assertIn("wx.GetDisplaySize()", self.responsive_text)


if __name__ == "__main__":
    unittest.main()
