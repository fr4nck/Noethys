# -*- coding: utf-8 -*-
"""Contrats statiques des contrôles scolaires communs."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SchoolControlsModernizationContractTests(unittest.TestCase):
    def _read(self, relative_path):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        ast.parse(text)
        return text

    def test_classes_tree_uses_semantic_surface_and_responsive_columns(self):
        text = self._read("noethys/Ctrl/CTRL_Classes.py")
        self.assertIn("UTILS_Interface", text)
        self.assertIn("UTILS_UIMetrics", text)
        self.assertIn('GetCouleurRole("surface_container_lowest")', text)
        self.assertIn("GetClientSize().GetWidth()", text)
        self.assertIn("wx.EVT_SIZE", text)
        self.assertIn("GetStaticIconPath", text)
        self.assertNotIn("SetBackgroundColour(wx.WHITE)", text)
        self.assertNotIn("SetColumnWidth(0, 370)", text)
        self.assertNotIn("SetColumnWidth(1, 120)", text)

    def test_classes_business_permissions_and_delete_guard_are_preserved(self):
        text = self._read("noethys/Ctrl/CTRL_Classes.py")
        for token in (
            'VerificationDroitsUtilisateurActuel("parametrage_classes", "creer")',
            'VerificationDroitsUtilisateurActuel("parametrage_classes", "modifier")',
            'VerificationDroitsUtilisateurActuel("parametrage_classes", "supprimer")',
            "SELECT COUNT(IDclasse)",
            'ReqDEL("classes"',
        ):
            self.assertIn(token, text)
        self.assertIn("return None", text)

    def test_school_grid_uses_repens_facade_and_tracks_available_width(self):
        text = self._read("noethys/Ctrl/CTRL_Grille_ecoles.py")
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn("Style.appliquer_liste(self)", text)
        self.assertIn("GetClientSize().GetWidth()", text)
        self.assertIn("GetStaticIconPath", text)
        self.assertIn("wx.EVT_SIZE", text)
        self.assertNotIn("SetBackgroundColour(wx.WHITE)", text)
        self.assertNotIn("SetColumnWidth(0, 420)", text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)

    def test_school_grid_preserves_selection_contract(self):
        text = self._read("noethys/Ctrl/CTRL_Grille_ecoles.py")
        for token in (
            "def CocheListeTout",
            "def CocheListeRien",
            "def GetListeEcoles",
            "def GetListeClasses",
            "def GetScolariteInconnue",
            "self.parent.MAJecoles()",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
