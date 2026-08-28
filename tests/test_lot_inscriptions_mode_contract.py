#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import types
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SOURCE_PATH = SOURCE_ROOT / "Dlg" / "DLG_Saisie_lot_inscriptions.py"


def load_maj(db_factory):
    source = SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    method = next(
        item
        for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "CTRL_Choix"
        for item in node.body
        if isinstance(item, ast.FunctionDef) and item.name == "MAJ"
    )
    module = ast.Module(body=[method], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "GestionDB": types.SimpleNamespace(DB=db_factory),
        "_": lambda text: text,
    }
    exec(compile(module, str(SOURCE_PATH), "exec"), namespace)
    return namespace["MAJ"]


class FakeDB:
    def __init__(self):
        self.req = None
        self.closed = False

    def ExecuterReq(self, req):
        self.req = req

    def ResultatReq(self):
        return [(7, "Valeur")]

    def Close(self):
        self.closed = True


class DBFactory:
    def __init__(self):
        self.instances = []

    def __call__(self):
        db = FakeDB()
        self.instances.append(db)
        return db


class FakeChoice:
    def __init__(self, mode):
        self.mode = mode
        self.listeID = None
        self.items = None
        self.enabled = None

    def SetItems(self, items):
        self.items = items

    def Enable(self, enabled):
        self.enabled = enabled


class LotInscriptionsModeContractTests(unittest.TestCase):
    def test_three_historical_modes_keep_their_queries(self):
        cases = (
            ("activites", "FROM activites"),
            ("groupes", "FROM groupes"),
            ("categories", "FROM categories_tarifs"),
        )
        for mode, fragment in cases:
            with self.subTest(mode=mode):
                factory = DBFactory()
                choice = FakeChoice(mode)
                load_maj(factory)(choice, IDactivite=12)
                self.assertEqual(len(factory.instances), 1)
                self.assertIn(fragment, factory.instances[0].req)
                self.assertTrue(factory.instances[0].closed)
                self.assertEqual(choice.listeID, [7])
                self.assertEqual(choice.items, ["Valeur"])
                self.assertTrue(choice.enabled)

    def test_unknown_mode_fails_before_opening_database(self):
        factory = DBFactory()
        choice = FakeChoice("inconnu")
        with self.assertRaisesRegex(ValueError, "mode"):
            load_maj(factory)(choice, IDactivite=12)
        self.assertEqual(factory.instances, [])

    def test_req_branch_assignment_gap_is_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE_PATH, SOURCE_ROOT)
        targeted = [
            finding for finding in findings
            if finding.get("function") == "MAJ" and finding.get("name") == "req"
        ]
        self.assertEqual(targeted, [], targeted)


if __name__ == "__main__":
    unittest.main()
