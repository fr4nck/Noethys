# -*- coding: utf-8 -*-
"""Contrats statiques des contrôles de communication et présence."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CommunicationControlsModernizationContractTests(unittest.TestCase):
    def _read(self, relative_path):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        ast.parse(text)
        return text

    def test_email_attachments_use_scaled_icons_and_semantic_states(self):
        text = self._read("noethys/Ctrl/CTRL_Pieces_jointes_emails.py")
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn('Style.taille_icone("inline")', text)
        self.assertIn('Style.couleur("on_surface_variant")', text)
        self.assertIn("GetStaticIconPath", text)
        self.assertIn("wx.EVT_KEY_DOWN", text)
        self.assertIn("wx.WXK_DELETE", text)
        self.assertIn("wx.WXK_INSERT", text)
        self.assertNotIn("wx.Colour(150, 150, 150)", text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)

    def test_portal_messages_use_named_actions_and_semantic_list(self):
        text = self._read("noethys/Ctrl/CTRL_Portail_messages.py")
        self.assertIn("CTRL_ActionRepens.CTRL", text)
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn("Style.appliquer_liste(self)", text)
        self.assertIn('Style.appliquer_fenetre(self, "surface")', text)
        self.assertIn("wx.BoxSizer(wx.HORIZONTAL)", text)
        self.assertIn("wx.BoxSizer(wx.VERTICAL)", text)
        self.assertNotIn("wx.BitmapButton", text)
        self.assertNotIn("wx.FlexGridSizer(", text)
        for token in ("def Ajouter", "def Modifier", "def Supprimer", 'ReqDEL("portail_messages"'):
            self.assertIn(token, text)

    def test_presence_ticker_follows_theme_and_text_scale(self):
        text = self._read("noethys/Ctrl/CTRL_Ticker_presents.py")
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn('Style.couleur("surface_container")', text)
        self.assertIn('Style.couleur("on_surface")', text)
        self.assertIn('Style.police("label")', text)
        self.assertIn('Style.hauteur_panneau("compact")', text)
        self.assertNotIn("wx.Font(8,", text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)


if __name__ == "__main__":
    unittest.main()
