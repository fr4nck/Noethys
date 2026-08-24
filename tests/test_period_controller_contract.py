#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Ctrl" / "CTRL_Grille_periode.py"


class PeriodControllerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text)

    def test_nested_pages_receive_explicit_controller(self):
        classes = {
            node.name: node
            for node in self.tree.body
            if isinstance(node, ast.ClassDef)
        }
        for name in ("Mois", "Annee", "Vacances", "Dates"):
            init = next(
                node
                for node in classes[name].body
                if isinstance(node, ast.FunctionDef) and node.name == "__init__"
            )
            args = [arg.arg for arg in init.args.args]
            self.assertIn("controller", args, name)
            self.assertIn("self.controller = controller", ast.get_source_segment(self.text, init))

    def test_pages_do_not_walk_visual_ancestry_for_business_callback(self):
        self.assertNotIn("GetGrandParent().OnSelection()", self.text)
        self.assertIn("self.controller.OnSelection()", self.text)

    def test_period_control_wires_itself_as_controller(self):
        for page in ("Dates", "Annee", "Vacances", "Mois"):
            self.assertIn(
                "%s(self.notebook, controller=self)" % page,
                self.text,
            )


if __name__ == "__main__":
    unittest.main()
