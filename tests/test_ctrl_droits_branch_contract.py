import unittest
from pathlib import Path
from scripts import audit_branch_assignment_gaps

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SOURCE_PATH = SOURCE_ROOT / "Ctrl" / "CTRL_Droits.py"

TARGETS = {
    ("InitGrid", "typeLigne"),
    ("InitGrid", "etat"),
    ("OnRightClick", "case"),
    ("OnActionMenuContextuel", "etat"),
    ("OnActionMenuContextuel", "IDcommande"),
}

class CtrlDroitsBranchContractTests(unittest.TestCase):
    def test_targeted_branch_assignment_gaps_are_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE_PATH, SOURCE_ROOT)
        targeted = [
            item for item in findings
            if (item.get("function"), item.get("name")) in TARGETS
        ]
        self.assertEqual(targeted, [], targeted)

    def test_source_compiles(self):
        compile(SOURCE_PATH.read_text(encoding="utf-8"), str(SOURCE_PATH), "exec")

if __name__ == "__main__":
    unittest.main()
