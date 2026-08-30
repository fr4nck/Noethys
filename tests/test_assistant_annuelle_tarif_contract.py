import unittest
from pathlib import Path
from scripts import audit_branch_assignment_gaps

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SOURCE_PATH = SOURCE_ROOT / "Ctrl" / "CTRL_Assistant_annuelle.py"

class AssistantAnnuelleTarifContractTests(unittest.TestCase):
    def test_paid_tariff_identifier_has_explicit_neutral_default(self):
        source = SOURCE_PATH.read_text(encoding="utf-8")
        expected = (
            'if self.parent.dict_valeurs["recopier_tarifs"] == None :\n'
            '            # Nom de tarif\n'
            '            IDnom_tarif = None\n'
            '            if self.parent.dict_valeurs["gratuit"] == False:'
        )
        self.assertIn(expected, source)
        self.assertIn('"IDnom_tarif": IDnom_tarif', source)

    def test_branch_assignment_gap_is_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE_PATH, SOURCE_ROOT)
        targeted = [item for item in findings if item.get("function") == "Suite" and item.get("name") == "IDnom_tarif"]
        self.assertEqual(targeted, [], targeted)

if __name__ == "__main__":
    unittest.main()
