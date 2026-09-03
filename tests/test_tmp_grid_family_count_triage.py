#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import unittest

from scripts import qualify_branch_assignment_gaps as audit


TARGET_NAMES = {
    "montant_tarif_tmp",
    "montant_enfant_1",
    "montant_enfant_2",
    "montant_enfant_3",
    "montant_enfant_4",
    "montant_enfant_5",
    "montant_enfant_6",
    "tarifsDegr",
}


class GridFamilyCountTriageDiagnostic(unittest.TestCase):
    def test_print_target_qualification_keys(self):
        report = audit.build_report()
        targets = []
        for item in report["findings"]:
            if item["file"] != "Ctrl/CTRL_Grille.py":
                continue
            if item["function"] not in {"Facturation", "CalculeTarif"}:
                continue
            if item["name"] not in TARGET_NAMES:
                continue
            targets.append({
                "file": item["file"],
                "function": item["function"],
                "line": item["line"],
                "name": item["name"],
                "detail": item["detail"],
                "key": audit.qualification_key(item),
            })
        print("GRID_FAMILY_COUNT_TRIAGE=" + json.dumps(targets, ensure_ascii=False, separators=(",", ":")))
        self.assertGreaterEqual(len(targets), 1)


if __name__ == "__main__":
    unittest.main()
