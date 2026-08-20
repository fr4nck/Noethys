# -*- coding: utf-8 -*-
"""Contrats statiques de la modernisation UI progressive des contrôles communs."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CommonUIModernizationContractTests(unittest.TestCase):
    def _read(self, relative_path):
        path = ROOT / relative_path
        text = path.read_text(encoding="utf-8")
        ast.parse(text)
        return text

    def test_common_toolbar_is_native_responsive_and_opt_in_fluent(self):
        text = self._read("noethys/Utils/UTILS_Adaptations.py")
        self.assertIn("class ToolBar(wx.ToolBar)", text)
        self.assertIn("def AddFluentTool", text)
        self.assertIn("wx.TB_FLAT | wx.TB_NODIVIDER", text)
        self.assertIn("UTILS_UIMetrics.toolbar_height", text)
        self.assertNotIn("setattr(wx.ToolBar", text)

    def test_common_banner_reflows_with_box_sizer(self):
        text = self._read("noethys/Ctrl/CTRL_Bandeau.py")
        self.assertIn("wx.BoxSizer(wx.HORIZONTAL)", text)
        self.assertIn("wx.BoxSizer(wx.VERTICAL)", text)
        self.assertIn("UTILS_UIMetrics", text)
        self.assertNotIn("FlexGridSizer", text)
        self.assertNotIn("GridSizer", text)

    def test_messages_no_longer_use_tiny_vertical_bitmap_buttons(self):
        text = self._read("noethys/Ctrl/CTRL_Messages.py")
        self.assertIn("AddFluentTool", text)
        self.assertIn('"add"', text)
        self.assertIn('"edit"', text)
        self.assertIn('"delete"', text)
        self.assertNotIn("wx.BitmapButton", text)
        self.assertNotIn("FlexGridSizer", text)

    def test_footer_tracks_real_responsive_column_widths(self):
        text = self._read("noethys/Ctrl/CTRL_Footer.py")
        self.assertIn("GetColumnWidth(index)", text)
        self.assertIn("GetScrollPos(wx.HORIZONTAL)", text)
        self.assertIn("UTILS_UIMetrics.row_height", text)

    def test_assistant_list_uses_available_width_without_recursive_resize(self):
        text = self._read("noethys/Ctrl/CTRL_Assistants_liste.py")
        self.assertIn("wx.EVT_SIZE", text)
        self.assertIn("GetClientSize().GetWidth()", text)
        self.assertNotIn("SendSizeEvent", text)
        self.assertNotIn("SetSize((400", text)

    def test_common_image_button_supports_explicit_fluent_and_safe_phoenix(self):
        text = self._read("noethys/Ctrl/CTRL_Bouton_image.py")
        self.assertIn("iconeFluent", text)
        self.assertIn("SetIconeFluent", text)
        self.assertIn("action_target", text)
        self.assertNotIn("EVT_ENABLE", text)

    def test_small_dialogs_are_resizable_and_not_grid_locked(self):
        for relative_path in (
            "noethys/Ctrl/CTRL_Numfacture.py",
            "noethys/Ctrl/CTRL_Identification.py",
        ):
            text = self._read(relative_path)
            self.assertIn("wx.RESIZE_BORDER", text)
            self.assertNotIn("FlexGridSizer", text)
            self.assertNotIn("GridSizer", text)

    def test_common_entry_controls_follow_theme_text_and_dpi_metrics(self):
        for relative_path in (
            "noethys/Ctrl/CTRL_Saisie_heure.py",
            "noethys/Ctrl/CTRL_Saisie_mail.py",
            "noethys/Ctrl/CTRL_Saisie_tel.py",
            "noethys/Ctrl/CTRL_Saisie_euros.py",
            "noethys/Ctrl/CTRL_Saisie_compte.py",
        ):
            text = self._read(relative_path)
            self.assertIn("UTILS_Interface", text)
            self.assertIn("UTILS_UIMetrics", text)
            self.assertIn('action_target("compact")', text)
            self.assertIn('GetCouleurRole("on_surface")', text)

    def test_modern_entry_controls_drop_unused_historical_image_dependencies(self):
        for relative_path in (
            "noethys/Ctrl/CTRL_Saisie_mail.py",
            "noethys/Ctrl/CTRL_Saisie_tel.py",
            "noethys/Ctrl/CTRL_Saisie_euros.py",
            "noethys/Ctrl/CTRL_Saisie_compte.py",
        ):
            text = self._read(relative_path)
            self.assertNotIn("CTRL_Bouton_image", text)
            self.assertNotIn("import Chemins", text)


if __name__ == "__main__":
    unittest.main()
