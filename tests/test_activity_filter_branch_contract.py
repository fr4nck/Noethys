#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import datetime
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
TARGETS = (
    SOURCE_ROOT / "Dlg" / "DLG_Archivage.py",
    SOURCE_ROOT / "Dlg" / "DLG_Comptes_internet.py",
)


class FakeDelta:
    @staticmethod
    def relativedelta(months=0, years=0):
        return datetime.timedelta(days=months * 30 + years * 365)


class Toggle:
    def __init__(self, value):
        self.value = value

    def GetValue(self):
        return self.value

    def Enable(self, value):
        pass


class Choice:
    def __init__(self, selection):
        self.selection = selection

    def GetSelection(self):
        return self.selection

    def Enable(self, value):
        pass


class ListView:
    def __init__(self):
        self.filters = []

    def SetFiltre(self, value):
        self.filters.append(value)


class FakePage:
    def __init__(self, tous=False, sans=False, avec=False, selection=0):
        self.radio_tous = Toggle(tous)
        self.radio_sans_activite = Toggle(sans)
        self.radio_avec_activite = Toggle(avec)
        self.ctrl_date_sans_activite = Choice(selection)
        self.ctrl_date_avec_activite = Choice(selection)
        self.ctrl_listview = ListView()


def load_method(path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    method = next(
        item
        for node in tree.body if isinstance(node, ast.ClassDef)
        for item in node.body
        if isinstance(item, ast.FunctionDef) and item.name == "OnRadioSelection"
    )
    module = ast.Module(body=[method], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "datetime": datetime,
        "relativedelta": FakeDelta,
        "CHOIX_DELAIS": [("mois", 1, "1 mois"), ("annees", 2, "2 ans")],
    }
    exec(compile(module, str(path), "exec"), namespace)
    return namespace["OnRadioSelection"]


class ActivityFilterBranchContractTests(unittest.TestCase):
    def test_all_mode_keeps_no_filter(self):
        for path in TARGETS:
            with self.subTest(path=path.name):
                page = FakePage(tous=True)
                load_method(path)(page)
                self.assertEqual(page.ctrl_listview.filters, [None])

    def test_without_activity_month_filter_is_preserved(self):
        for path in TARGETS:
            with self.subTest(path=path.name):
                page = FakePage(sans=True, selection=0)
                load_method(path)(page)
                self.assertEqual(page.ctrl_listview.filters[-1][0], "sans")

    def test_with_activity_year_filter_is_preserved(self):
        for path in TARGETS:
            with self.subTest(path=path.name):
                page = FakePage(avec=True, selection=1)
                load_method(path)(page)
                self.assertEqual(page.ctrl_listview.filters[-1][0], "avec")

    def test_no_selected_radio_falls_back_to_no_filter(self):
        for path in TARGETS:
            with self.subTest(path=path.name):
                page = FakePage()
                load_method(path)(page)
                self.assertEqual(page.ctrl_listview.filters, [None])

    def test_unknown_delay_type_fails_explicitly(self):
        for path in TARGETS:
            with self.subTest(path=path.name):
                method = load_method(path)
                method.__globals__["CHOIX_DELAIS"] = [("semaines", 2, "2 semaines")]
                with self.assertRaises(ValueError):
                    method(FakePage(sans=True))

    def test_targeted_branch_assignment_gaps_are_gone(self):
        targeted_names = {"index", "type_filtre", "date_limite"}
        for path in TARGETS:
            with self.subTest(path=path.name):
                findings = audit_branch_assignment_gaps.scan_file(path, SOURCE_ROOT)
                targeted = [
                    item for item in findings
                    if item.get("function") == "OnRadioSelection" and item.get("name") in targeted_names
                ]
                self.assertEqual(targeted, [], targeted)


if __name__ == "__main__":
    unittest.main()
