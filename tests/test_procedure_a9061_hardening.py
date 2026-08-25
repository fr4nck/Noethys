#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "noethys" / "Utils" / "UTILS_Procedures.py"


class ProcedureA9061HardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text)
        cls.function = next(
            node for node in cls.tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "A9061"
        )

    def test_documents_update_is_not_hidden_by_exception_handler(self):
        mutation_try = next(
            node for node in self.function.body
            if isinstance(node, ast.Try)
            and "UPDATE documents SET last_update" in (ast.get_source_segment(self.text, node) or "")
        )
        self.assertEqual(mutation_try.handlers, [])
        self.assertTrue(mutation_try.finalbody)

    def test_documents_connection_is_closed_even_when_update_fails(self):
        mutation_try = next(
            node for node in self.function.body
            if isinstance(node, ast.Try)
            and "UPDATE documents SET last_update" in (ast.get_source_segment(self.text, node) or "")
        )
        finally_source = "\n".join(
            ast.get_source_segment(self.text, node) or "" for node in mutation_try.finalbody
        )
        self.assertIn("DB.Close()", finally_source)


if __name__ == "__main__":
    unittest.main()
