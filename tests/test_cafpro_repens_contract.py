#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Dlg" / "DLG_Consultation_cafpro.py"


def _method_source(text, tree, class_name, method_name):
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return ast.get_source_segment(text, child) or ""
    raise AssertionError("%s.%s introuvable" % (class_name, method_name))


class CafproRepensContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text)

    def test_drop_uses_explicit_business_controller(self):
        init = _method_source(self.text, self.tree, "CTRL_Drop", "__init__")
        setter = _method_source(self.text, self.tree, "CTRL_Drop", "SetTexte")
        self.assertIn("controller", init)
        self.assertIn("self.controller = controller", init)
        self.assertIn("self.controller.bouton_ok.Enable(True)", setter)
        self.assertNotIn("GetGrandParent()", setter)
        self.assertIn("CTRL_Drop(self.panel, controller=self", self.text)

    def test_drop_bitmap_uses_semantic_surfaces(self):
        creation = _method_source(self.text, self.tree, "CTRL_Drop", "CreationImageDrop")
        for role in (
            'Style.couleur("on_surface_variant")',
            'Style.couleur("surface_container_low")',
            'Style.couleur("on_surface")',
            'Style.couleur("surface_container_lowest")',
        ):
            self.assertIn(role, creation)
        self.assertNotIn("wx.Colour(248, 248, 248)", creation)
        self.assertNotIn("wx.Colour(255, 255, 255)", creation)
        self.assertEqual(creation.count("dc.DrawLabel("), 1)

    def test_secondary_label_uses_semantic_text_role(self):
        self.assertIn(
            'Style.appliquer_texte(self.label_dernier_qf, role="caption", role_texte="on_surface_variant")',
            self.text,
        )
        self.assertNotIn("self.label_dernier_qf.SetForegroundColour(wx.Colour(150, 150, 150))", self.text)


if __name__ == "__main__":
    unittest.main()
