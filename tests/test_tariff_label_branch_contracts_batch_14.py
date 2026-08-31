import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
AUDIT = ROOT / "scripts" / "audit_branch_assignment_gaps.py"
spec = importlib.util.spec_from_file_location("audit_branch_assignment_gaps", AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

TARGETS = {
    ("Dlg/DLG_Saisie_lot_forfaits_credits.py", "MAJ", "label"),
    ("Dlg/DLG_Saisie_modele_prestation.py", "SetListeDonnees", "label"),
    ("Dlg/DLG_Saisie_prestation.py", "SetListeDonnees", "label"),
}

class TestBatch14TariffLabels(unittest.TestCase):
    def test_targeted_findings_disappear(self):
        remaining = set()
        for relpath, function, name in TARGETS:
            path = NOETHYS / relpath
            for item in audit.scan_file(path, NOETHYS):
                key = (item["file"], item["function"], item["name"])
                if key in TARGETS:
                    remaining.add(key)
        self.assertEqual(remaining, set())

    def test_four_historical_labels_are_preserved(self):
        for relpath, _, _ in TARGETS:
            source = (NOETHYS / relpath).read_text(encoding="utf-8")
            self.assertIn("Sans période de validité", source)
            self.assertIn("Jusqu'au %s", source)
            self.assertIn("A partir du %s", source)
            self.assertIn("Du %s au %s", source)
            self.assertIn("elif date_debut == None and date_fin != None", source)
            self.assertIn("elif date_debut != None and date_fin == None", source)
            self.assertIn('else : label = _(u"%s (Du %s au %s)")', source)

if __name__ == "__main__":
    unittest.main()
