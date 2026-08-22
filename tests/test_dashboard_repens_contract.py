# -*- coding: utf-8 -*-
"""Contrats statiques des surfaces visibles du cockpit Repens."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MESSAGES = ROOT / "noethys" / "Ctrl" / "CTRL_Messages.py"
AUJOURDHUI = ROOT / "noethys" / "Ctrl" / "CTRL_Ephemeride.py"
SURFACE = ROOT / "noethys" / "Ctrl" / "CTRL_SurfaceRepens.py"
ACTION = ROOT / "noethys" / "Ctrl" / "CTRL_ActionRepens.py"


class DashboardRepensContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.messages = MESSAGES.read_text(encoding="utf-8")
        cls.aujourdhui = AUJOURDHUI.read_text(encoding="utf-8")
        cls.surface = SURFACE.read_text(encoding="utf-8")
        cls.action = ACTION.read_text(encoding="utf-8")
        for texte in (cls.messages, cls.aujourdhui, cls.surface, cls.action):
            ast.parse(texte)

    def test_messages_is_data_first_and_uses_repens_actions(self):
        self.assertIn("class ListeMessagesAccueil", self.messages)
        self.assertIn("UTILS_ColonnesResponsive.Installer", self.messages)
        self.assertIn("CTRL_ActionRepens.CTRL", self.messages)
        self.assertNotIn("class ToolBar", self.messages)
        self.assertNotIn("size=(950", self.messages)
        self.assertNotIn("SetSize((950", self.messages)
        self.assertNotIn("Attention.png", self.messages)
        self.assertIn('label=_(u"Nouveau")', self.messages)
        self.assertIn('label=_(u"Modifier")', self.messages)
        self.assertIn('label=_(u"Plus")', self.messages)

    def test_today_uses_common_rounded_surfaces(self):
        self.assertIn("CTRL_SurfaceRepens.CTRL", self.aujourdhui)
        self.assertIn('role_fond="surface_container_low"', self.aujourdhui)
        self.assertIn('role_fond="surface_container"', self.aujourdhui)
        self.assertIn("DrawRoundedRectangle", self.surface)
        self.assertIn("UTILS_StyleRepens as Style", self.surface)
        self.assertIn('Style.couleur("surface")', self.surface)

    def test_today_reflows_when_workspace_becomes_narrow(self):
        self.assertIn("def _AppliquerResponsive", self.aujourdhui)
        self.assertIn("wx.BoxSizer(wx.VERTICAL)", self.aujourdhui)
        self.assertIn("wx.BoxSizer(wx.HORIZONTAL)", self.aujourdhui)
        self.assertIn("wx.EVT_SIZE", self.aujourdhui)
        self.assertIn("UTILS_UIMetrics.px(760)", self.aujourdhui)

    def test_visible_secondary_panes_expose_window_commands(self):
        for texte in (self.messages, self.aujourdhui):
            self.assertIn("CloseButton(True)", texte)
            self.assertIn("MinimizeButton(True)", texte)
            self.assertIn("MaximizeButton(True)", texte)
            self.assertIn("Resizable(True)", texte)

    def test_repens_action_has_semantic_primary_and_focus_states(self):
        self.assertIn('variante == "primaire"', self.action)
        self.assertIn('Style.couleur("focus")', self.action)
        self.assertIn("DrawRoundedRectangle", self.action)
        self.assertIn("UTILS_StyleRepens as Style", self.action)


if __name__ == "__main__":
    unittest.main()
