#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Dlg" / "DLG_Saisie_location_demande.py"


def _method_source(text, tree, class_name, method_name):
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return ast.get_source_segment(text, child) or ""
    raise AssertionError("%s.%s introuvable" % (class_name, method_name))


class LocationRequestWxLifecycleContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text)

    def test_nested_pages_use_explicit_business_controller(self):
        self.assertNotIn("GetGrandParent()", self.text)
        self.assertIn("PAGE_Criteres(self, IDdemande=IDdemande, controller=controller)", self.text)
        self.assertIn("PAGE_Statut_attente(self, controller=controller)", self.text)
        self.assertIn("Notebook(self, IDdemande=IDdemande, controller=self)", self.text)
        self.assertIn("CTRL_Statut(self, controller=self)", self.text)

    def test_distance_choice_is_read_before_dialog_is_destroyed(self):
        method = _method_source(self.text, self.tree, "Dialog", "Mesurer_distance")
        selection = method.index("selection = dlg.GetSelection()")
        destroy = method.index("dlg.Destroy()", selection)
        consume = method.index("liste_donnees[selection]", destroy)
        self.assertLess(selection, destroy)
        self.assertLess(destroy, consume)
        self.assertNotIn("liste_donnees[dlg.GetSelection()]", method)


if __name__ == "__main__":
    unittest.main()
