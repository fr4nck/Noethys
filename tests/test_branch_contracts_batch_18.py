import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
AUDIT = ROOT / "scripts" / "audit_branch_assignment_gaps.py"
spec = importlib.util.spec_from_file_location("audit_branch_assignment_gaps", AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

TARGET = ("Ctrl/CTRL_Questionnaire.py", "Remplissage", "ctrl")

class TestBatch18Questionnaire(unittest.TestCase):
    def test_targeted_finding_disappears(self):
        path = NOETHYS / "Ctrl/CTRL_Questionnaire.py"
        remaining = [
            (item["file"], item["function"], item["name"])
            for item in audit.scan_file(path, NOETHYS)
            if (item["file"], item["function"], item["name"]) == TARGET
        ]
        self.assertEqual(remaining, [])

    def test_unknown_non_null_control_is_rejected_explicitly(self):
        source = (NOETHYS / "Ctrl/CTRL_Questionnaire.py").read_text(encoding="utf-8")
        self.assertIn("ctrl = None", source)
        self.assertIn("if ctrl == None :", source)
        self.assertIn("Type de contrôle de questionnaire inconnu", source)

if __name__ == "__main__":
    unittest.main()
