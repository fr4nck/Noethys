import ast
import unittest
from pathlib import Path
from scripts import audit_branch_assignment_gaps

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SOURCE_PATH = SOURCE_ROOT / "Ctrl" / "CTRL_Assistant_base.py"

class AssistantBaseLineIdContractTests(unittest.TestCase):
    def test_line_identifier_has_explicit_neutral_default(self):
        source = SOURCE_PATH.read_text(encoding="utf-8")
        expected = (
            'prochainIDtarif = DB.GetProchainID("tarifs")\n'
            '        prochainIDligne = None\n'
            '        if DB.isNetwork == False:'
        )
        self.assertIn(expected, source)

    def test_line_identifier_is_consumed_only_in_local_database_branch(self):
        tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
        methods = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "Sauvegarde_tarifs"]
        self.assertEqual(len(methods), 1)
        method = methods[0]
        local_if_nodes = [
            n for n in ast.walk(method)
            if isinstance(n, ast.If) and "DB.isNetwork == False" in ast.unparse(n.test)
        ]
        self.assertGreaterEqual(len(local_if_nodes), 2)
        loads = [n for n in ast.walk(method) if isinstance(n, ast.Name) and n.id == "prochainIDligne" and isinstance(n.ctx, ast.Load)]
        self.assertEqual(len(loads), 1)
        self.assertTrue(any(loads[0] in list(ast.walk(node)) for node in local_if_nodes))

    def test_branch_assignment_gap_is_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE_PATH, SOURCE_ROOT)
        targeted = [item for item in findings if item.get("function") == "Sauvegarde_tarifs" and item.get("name") == "prochainIDligne"]
        self.assertEqual(targeted, [], targeted)

if __name__ == "__main__":
    unittest.main()
