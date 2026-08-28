# -*- coding: utf-8 -*-
import ast
import datetime
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Utils" / "UTILS_Dates.py"


def extract_function(name):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    node = next(
        item
        for item in tree.body
        if isinstance(item, ast.FunctionDef) and item.name == name
    )
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"datetime": datetime}
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace[name]


class UtilsDatesBranchAssignmentContractTests(unittest.TestCase):
    def test_heure_str_en_time_preserves_historical_formats(self):
        convertir = extract_function("HeureStrEnTime")

        self.assertEqual(datetime.time(0, 0), convertir(None))
        self.assertEqual(datetime.time(0, 0), convertir(""))
        self.assertEqual(datetime.time(7, 30), convertir("07:30"))
        self.assertEqual(datetime.time(7, 30), convertir("07:30:45"))

    def test_heure_str_en_time_rejects_malformed_input_without_unbound_local(self):
        convertir = extract_function("HeureStrEnTime")

        self.assertEqual(datetime.time(0, 0), convertir("07"))
        self.assertEqual(datetime.time(0, 0), convertir("07:30:00:00"))
        self.assertEqual(datetime.time(0, 0), convertir("xx:30"))
        self.assertEqual(datetime.time(0, 0), convertir("25:00"))
        self.assertEqual(datetime.time(0, 0), convertir("99999999999999999999:00"))

    def test_arrondir_time_preserves_existing_rounding_and_unknown_direction(self):
        arrondir = extract_function("ArrondirTime")
        heure = datetime.time(10, 25)

        self.assertEqual(datetime.time(10, 15), arrondir(heure, 15, "inf"))
        self.assertEqual(datetime.time(10, 30), arrondir(heure, 15, "sup"))
        self.assertEqual(heure, arrondir(heure, 15, "inconnu"))
        self.assertEqual(datetime.time(10, 30), arrondir(datetime.time(10, 30), 15, "inconnu"))

    def test_arrondir_delta_preserves_existing_rounding_and_unknown_direction(self):
        arrondir = extract_function("ArrondirDelta")
        duree = datetime.timedelta(hours=1, minutes=25)

        self.assertEqual(datetime.timedelta(hours=1, minutes=15), arrondir(duree, 15, "inf"))
        self.assertEqual(datetime.timedelta(hours=1, minutes=30), arrondir(duree, 15, "sup"))
        self.assertEqual(duree, arrondir(duree, 15, "inconnu"))
        self.assertEqual(
            datetime.timedelta(hours=1, minutes=30),
            arrondir(datetime.timedelta(hours=1, minutes=30), 15, "inconnu"),
        )

    def test_targeted_utils_dates_branch_assignment_gaps_are_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE.resolve())
        targeted = {
            "HeureStrEnTime": {"heures", "minutes"},
            "ArrondirTime": {"resultat"},
            "ArrondirDelta": {"resultat"},
        }
        remaining = [
            item
            for item in findings
            if item["function"] in targeted
            and item["name"] in targeted[item["function"]]
        ]
        self.assertEqual([], remaining)


if __name__ == "__main__":
    unittest.main()
