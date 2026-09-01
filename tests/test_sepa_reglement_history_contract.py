#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import decimal
import unittest
from pathlib import Path
from types import SimpleNamespace

from scripts import audit_branch_assignment_gaps


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
TARGET = SOURCE_ROOT / "Ol" / "OL_Prelevements_sepa.py"


class FakeDB:
    def __init__(self):
        self.result_sets = [[], []]
        self.deletes = []

    def ExecuterReq(self, req):
        pass

    def ResultatReq(self):
        return self.result_sets.pop(0)

    def ReqDEL(self, table, key, value, commit=False):
        self.deletes.append((table, key, value, commit))
        return True


class FakeHistorique:
    actions = []

    @classmethod
    def InsertActions(cls, actions, DB=None, commit=False):
        cls.actions = list(actions)
        return True


class FakeView:
    def __init__(self, track):
        self.track = track

    def GetObjects(self):
        return [self.track]

    def MemoriseReglementHistorique(self, mode="saisie", IDfamille=None, IDreglement=None, montant=0.0):
        return {
            "mode": mode,
            "IDfamille": IDfamille,
            "IDreglement": IDreglement,
            "montant": montant,
        }

    def RefreshObject(self, track):
        pass


def load_method():
    source = TARGET.read_text(encoding="utf-8")
    tree = ast.parse(source)
    method = next(
        item
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "ListView"
        for item in node.body
        if isinstance(item, ast.FunctionDef) and item.name == "SauvegardeReglements"
    )
    module = ast.Module(body=[method], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "decimal": decimal,
        "UTILS_Historique": FakeHistorique,
    }
    exec(compile(module, str(TARGET), "exec"), namespace)
    return namespace["SauvegardeReglements"]


class SepaReglementHistoryContractTests(unittest.TestCase):
    def setUp(self):
        FakeHistorique.actions = []

    def test_first_deleted_payment_uses_its_own_id_in_history(self):
        track = SimpleNamespace(
            IDfacture=None,
            reglement=False,
            IDreglement=123,
            IDfamille=45,
            montant=12.5,
        )
        db = FakeDB()

        result = load_method()(FakeView(track), DB=db, commit=False)

        self.assertTrue(result)
        self.assertEqual(
            db.deletes,
            [
                ("ventilation", "IDreglement", 123, False),
                ("reglements", "IDreglement", 123, False),
            ],
        )
        self.assertEqual(len(FakeHistorique.actions), 1)
        self.assertEqual(FakeHistorique.actions[0]["IDreglement"], 123)
        self.assertEqual(FakeHistorique.actions[0]["mode"], "suppression")

    def test_targeted_branch_assignment_gap_is_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(TARGET, SOURCE_ROOT)
        targeted = [
            item
            for item in findings
            if item.get("function") == "SauvegardeReglements"
            and item.get("name") == "IDreglement"
        ]
        self.assertEqual(targeted, [], targeted)


if __name__ == "__main__":
    unittest.main()
