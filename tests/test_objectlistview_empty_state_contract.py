# -*- coding: utf-8 -*-
"""Contrats de l'état vide commun des ObjectListView Repens."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ObjectListViewEmptyStateContractTests(unittest.TestCase):
    def _read(self, relative_path):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        ast.parse(text)
        return text

    def test_wrapper_restores_empty_state_after_legacy_phoenix_resize(self):
        text = self._read("noethys/ObjectListView/__init__.py")
        self.assertIn("def _synchroniser_etat_vide(ctrl):", text)
        self.assertIn('message.Show(vide)', text)
        self.assertIn("wx.CallAfter(_synchroniser_etat_vide, ctrl)", text)
        self.assertIn("ctrl.Bind(wx.EVT_SIZE, _apres_resize)", text)
        self.assertNotIn("'phoenix' in wx.PlatformInfo", text)

    def test_empty_state_waits_for_real_list_columns_before_becoming_visible(self):
        text = self._read("noethys/ObjectListView/__init__.py")
        self.assertIn("if ctrl.GetColumnCount() <= 0:", text)
        self.assertIn("message.Hide()", text)
        # Un contrôle tout juste construit ne doit pas afficher fugitivement
        # « Aucun élément » avant que l'écran métier ait installé ses colonnes.
        self.assertNotIn("_synchroniser_etat_vide(self)", text)

    def test_vendor_default_message_is_localized_without_overwriting_business_text(self):
        text = self._read("noethys/ObjectListView/__init__.py")
        self.assertIn('_MESSAGE_VIDE_VENDOR = "This list is empty"', text)
        self.assertIn('if message.GetLabel() != _MESSAGE_VIDE_VENDOR:', text)
        self.assertIn('message.SetLabel(_(u"Aucun élément"))', text)

    def test_repens_replaces_vendor_fixed_24pt_empty_font(self):
        text = self._read("noethys/Utils/UTILS_StyleRepens.py")
        self.assertIn('message_vide.SetFont(police("body_small"))', text)
        self.assertNotIn("wx.Font(24", text)


if __name__ == "__main__":
    unittest.main()
