#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import types
import unittest
from pathlib import Path

from scripts.audit_branch_assignment_gaps import scan_file


ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
TARGET = NOETHYS / "Dlg" / "DLG_Saisie_location_prestation.py"


def load_init_model(globals_dict):
    tree = ast.parse(TARGET.read_text(encoding="utf-8"))
    class_node = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "OL_Tarifs"
    )
    function_node = next(
        node for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == "InitModel"
    )
    module = ast.Module(body=[function_node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = dict(globals_dict)
    exec(compile(module, str(TARGET), "exec"), namespace)
    return namespace["InitModel"]


class FakeDB:
    def __init__(self):
        self.queries = []
        self.closed = False

    def ExecuterReq(self, req):
        self.queries.append(req)

    def ResultatReq(self):
        return []

    def Close(self):
        self.closed = True


class LocationProductBranchContractTests(unittest.TestCase):
    def test_missing_product_stops_before_orphan_tariffs(self):
        db = FakeDB()
        init_model = load_init_model({
            "GestionDB": types.SimpleNamespace(DB=lambda: db),
        })
        owner = types.SimpleNamespace(
            dictInfosLocation={"IDproduit": 42},
            donnees=["stale"],
        )

        init_model(owner)

        self.assertTrue(db.closed)
        self.assertEqual(owner.donnees, [])
        self.assertEqual(len(db.queries), 1)
        self.assertIn("FROM produits", db.queries[0])
        self.assertIn("IDproduit=42", db.queries[0])

    def test_nom_produit_gap_is_gone(self):
        findings = scan_file(TARGET, NOETHYS)
        self.assertFalse(any(
            item["function"] == "InitModel" and item["name"] == "nom_produit"
            for item in findings
        ))


if __name__ == "__main__":
    unittest.main()
