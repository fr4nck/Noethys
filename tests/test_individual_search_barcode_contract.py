#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "noethys" / "Ol" / "OL_Individus.py"


class IndividualSearchBarcodeContractTests(unittest.TestCase):
    def test_barre_recherche_does_not_call_an_undefined_maj_after_family_barcode(self):
        source = PATH.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)

        method = None
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "BarreRecherche":
                method = next(
                    (item for item in node.body if isinstance(item, ast.FunctionDef) and item.name == "OnText"),
                    None,
                )
                break
        self.assertIsNotNone(method)

        calls = [node for node in ast.walk(method) if isinstance(node, ast.Call)]
        undefined_self_maj = [
            node for node in calls
            if isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "self"
            and node.func.attr == "MAJ"
        ]
        self.assertEqual(undefined_self_maj, [])

        segment = ast.get_source_segment(source, method) or ""
        self.assertIn('getattr(self.parent, "MAJ", None)', segment)
        self.assertIn("self.listView.MAJ(forceActualisation=True)", segment)


if __name__ == "__main__":
    unittest.main()
