#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Ctrl" / "CTRL_Identification.py"


def _method_source(text, tree, class_name, method_name):
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return ast.get_source_segment(text, child) or ""
    raise AssertionError("%s.%s introuvable" % (class_name, method_name))


class IdentificationControllerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text)

    def test_shell_uses_top_level_instead_of_fixed_visual_depth(self):
        resolver = _method_source(
            self.text, self.tree, "CTRL", "_GetBusinessController"
        )
        recherche = _method_source(self.text, self.tree, "CTRL", "Recherche")
        self.assertIn("wx.GetTopLevelParent(self)", resolver)
        self.assertNotIn("GetGrandParent()", resolver)
        self.assertNotIn("GetGrandParent()", recherche)

    def test_shell_keeps_reading_current_user_list_from_main_frame(self):
        recherche = _method_source(self.text, self.tree, "CTRL", "Recherche")
        self.assertIn('getattr(controller, "listeUtilisateurs", [])', recherche)
        self.assertIn("controller.ChargeUtilisateur(dictUtilisateur)", recherche)

    def test_dialog_keeps_using_explicit_user_list(self):
        recherche = _method_source(self.text, self.tree, "CTRL", "Recherche")
        self.assertIn("if self.modeDLG:", recherche)
        self.assertIn("listeUtilisateurs = self.listeUtilisateurs", recherche)


if __name__ == "__main__":
    unittest.main()
