import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps as base
from scripts import qualify_branch_assignment_gaps as qualified


class OuverturesBranchAssignmentContractTests(unittest.TestCase):
    def setUp(self):
        self.path = qualified.ROOT / "Dlg" / "DLG_Ouvertures.py"

    def test_graphic_helpers_no_longer_leave_unbound_locals(self):
        findings = base.scan_file(self.path)
        helper_findings = [
            item for item in findings
            if item["function"] in {"CreationImage", "GetImageEvement"}
        ]
        self.assertEqual(helper_findings, [])

        source = Path(self.path).read_text(encoding="utf-8")
        self.assertIn("if couleur is None:", source)
        self.assertIn('raise ValueError("couleur doit être une chaîne HEXA ou un tuple RGB")', source)
        self.assertIn('raise ValueError("alignement horizontal invalide : %s" % alignement)', source)
        self.assertIn('raise ValueError("alignement vertical invalide : %s" % alignement)', source)

    def test_remaining_ouvertures_candidates_are_explicitly_proven_safe(self):
        findings = base.scan_file(self.path)
        actual = {
            (item["function"], item["name"], item["detail"])
            for item in findings
        }
        expected = {
            ("Sauvegarde", "prochainIDligne", "body_only"),
            ("TraitementLot", "etat", "partial_branches"),
            ("TraitementLot", "liste_temp", "body_only"),
            ("TraitementLot", "nbrePlaces", "partial_branches"),
        }
        self.assertEqual(actual, expected)

        for item in findings:
            key = qualified.qualification_key(item)
            self.assertIn(key, qualified.EXPLICIT_SAFE)
            self.assertTrue(qualified.EXPLICIT_SAFE[key])


if __name__ == "__main__":
    unittest.main()
