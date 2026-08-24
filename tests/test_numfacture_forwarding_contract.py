#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Ctrl" / "CTRL_Numfacture.py"


def _method_source(text, tree, class_name, method_name):
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return ast.get_source_segment(text, child) or ""
    raise AssertionError("%s.%s introuvable" % (class_name, method_name))


class NumfactureForwardingContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text)

    def test_family_invoice_forwards_exact_invoice_id(self):
        method = _method_source(self.text, self.tree, "CTRL", "ReglerFacture")
        self.assertIn("self.controller.ReglerFacture(IDfacture)", method)
        self.assertNotIn("self.GetGrandParent().ReglerFacture()", method)

    def test_dialog_wires_family_controller_explicitly(self):
        init = _method_source(self.text, self.tree, "Dialog", "__init__")
        self.assertIn("CTRL(self, IDfamille=self.IDfamille, controller=parent)", init)

    def test_non_family_path_also_forwards_exact_invoice_id(self):
        method = _method_source(self.text, self.tree, "CTRL", "ReglerFacture")
        self.assertIn("dlg.ReglerFacture(IDfacture)", method)


if __name__ == "__main__":
    unittest.main()
