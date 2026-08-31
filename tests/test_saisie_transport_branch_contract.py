import ast
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SOURCE = SOURCE_ROOT / "Ctrl" / "CTRL_Saisie_transport.py"


class SaisieTransportBranchContractTests(unittest.TestCase):
    def test_targeted_transport_gaps_are_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE, SOURCE_ROOT)
        targeted_names = {"nomTemp", "date_min", "date_max", "liste_dates", "listeDatesPresences"}
        targeted = [item for item in findings if item.get("function") in {"Validation", "Sauvegarde"} and item.get("name") in targeted_names]
        self.assertEqual(targeted, [], targeted)

    def test_validation_has_explicit_unknown_rubrique_contract(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('raise ValueError("Rubrique de transport inconnue : %r" % self.rubrique)', source)

    def test_multiple_mode_has_explicit_unknown_type_contract(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('raise ValueError("Mode de saisie multiple inconnu : %r" % type)', source)


if __name__ == "__main__":
    unittest.main()
