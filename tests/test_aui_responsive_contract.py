# -*- coding: utf-8 -*-
"""Contrat statique du shell AUI responsive.

Ce test reste sans wxPython : il vérifie que le shell conserve les garanties
structurelles qui évitent les barres flottantes et les boucles de resize.
"""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUI = ROOT / "noethys" / "Utils" / "UTILS_Aui.py"


class AuiResponsiveContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = AUI.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text)

    def test_layout_generation_is_bumped(self):
        self.assertIn("PERSPECTIVE_LAYOUT_VERSION = 3", self.text)

    def test_system_toolbars_are_fixed_and_non_floating(self):
        self.assertIn('("barre_raccourcis", 0)', self.text)
        self.assertIn('("barre_utilisateur", 1)', self.text)
        self.assertIn('(\"Gripper\", (False,))', self.text)
        self.assertIn('(\"Floatable\", (False,))', self.text)
        self.assertIn('(\"DockFixed\", (True,))', self.text)

    def test_dashboard_geometry_uses_viewport_ratios(self):
        for ratio in ("0.32", "0.34", "0.37", "0.40"):
            self.assertIn(ratio, self.text)
        self.assertIn('"largeur_gauche"', self.text)
        self.assertIn('"hauteur_info"', self.text)
        self.assertIn("GetClientSize()", self.text)

    def test_resize_is_debounced_and_does_not_reinject_size_events(self):
        self.assertIn("wx.EVT_SIZE", self.text)
        self.assertIn("wx.CallAfter(_AppliquerPlusTard)", self.text)
        self.assertIn("_noethys_aui_responsive_pending", self.text)
        self.assertNotIn("SendSizeEvent", self.text)

    def test_old_ephemeride_caption_is_replaced_at_shell_level(self):
        self.assertIn("Aujourd'hui / Échéancier", self.text)


if __name__ == "__main__":
    unittest.main()
