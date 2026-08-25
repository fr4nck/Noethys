#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Utils" / "UTILS_Procedures.py"


def _function_source(name):
    text = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(text, node) or ""
    raise AssertionError(f"Fonction {name} introuvable")


class ProcedureA9068HardeningTests(unittest.TestCase):
    def test_empty_selection_cannot_turn_into_global_update(self):
        source = _function_source("A9068")
        self.assertNotIn('condition = "IDinscription > 0"', source)
        self.assertIn("if not listeIDinscription:", source)
        guard = source.index("if not listeIDinscription:")
        close = source.index("DB.Close()", guard)
        stop = source.index("return", close)
        update = source.index("UPDATE inscriptions", stop)
        self.assertLess(guard, close)
        self.assertLess(close, stop)
        self.assertLess(stop, update)

    def test_update_remains_restricted_to_selected_ids(self):
        source = _function_source("A9068")
        self.assertIn('condition = "IDinscription IN (%d)" % listeIDinscription[0]', source)
        self.assertIn('condition = "IDinscription IN %s" % str(tuple(listeIDinscription))', source)


if __name__ == "__main__":
    unittest.main()
