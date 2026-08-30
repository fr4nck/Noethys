import ast
import unittest
from pathlib import Path
from scripts import audit_branch_assignment_gaps

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SOURCE_PATH = SOURCE_ROOT / "Ctrl" / "CTRL_Composition.py"

class CompositionCategoryLabelContractTests(unittest.TestCase):
    def test_historical_category_labels_are_preserved(self):
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn('1: _(u"Représentants")', source)
        self.assertIn('2: _(u"Enfants")', source)
        self.assertIn('3: _(u"Contacts")', source)
        self.assertIn('label = labelsCategories[IDcategorie]', source)

    def test_creation_branches_label_gap_is_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE_PATH, SOURCE_ROOT)
        targeted = [item for item in findings if item.get("function") == "CreationBranches" and item.get("name") == "label"]
        self.assertEqual(targeted, [], targeted)

    def test_category_iteration_stays_historical(self):
        tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
        funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "CreationBranches"]
        self.assertEqual(len(funcs), 1)
        text = ast.unparse(funcs[0])
        self.assertIn('for IDcategorie in (1, 2, 3):', text)

if __name__ == "__main__":
    unittest.main()
