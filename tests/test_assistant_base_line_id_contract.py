import ast
import unittest
from pathlib import Path
from scripts import audit_branch_assignment_gaps

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SOURCE_PATH = SOURCE_ROOT / "Ctrl" / "CTRL_Assistant_base.py"


def is_exact_local_guard(test):
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Attribute)
        and isinstance(test.left.value, ast.Name)
        and test.left.value.id == "DB"
        and test.left.attr == "isNetwork"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value is False
    )


def nodes_in_body(if_node):
    nodes = set()
    for statement in if_node.body:
        nodes.update(ast.walk(statement))
    return nodes


def assigns_name(node, name):
    return (
        isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)
    )


class AssistantBaseLineIdContractTests(unittest.TestCase):
    def test_line_identifier_has_explicit_neutral_default(self):
        source = SOURCE_PATH.read_text(encoding="utf-8")
        expected = (
            'prochainIDtarif = DB.GetProchainID("tarifs")\n'
            '        prochainIDligne = None\n'
            '        if DB.isNetwork == False:'
        )
        self.assertIn(expected, source)

    def test_line_identifier_state_is_confined_to_exact_local_branch_bodies(self):
        tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
        methods = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "Sauvegarde_tarifs"]
        self.assertEqual(len(methods), 1)
        method = methods[0]
        local_if_nodes = [n for n in ast.walk(method) if isinstance(n, ast.If) and is_exact_local_guard(n.test)]
        self.assertGreaterEqual(len(local_if_nodes), 2)
        protected_nodes = set().union(*(nodes_in_body(node) for node in local_if_nodes))

        assignments = [n for n in ast.walk(method) if assigns_name(n, "prochainIDligne")]
        increments = [
            n for n in ast.walk(method)
            if isinstance(n, ast.AugAssign)
            and isinstance(n.target, ast.Name)
            and n.target.id == "prochainIDligne"
        ]
        loads = [
            n for n in ast.walk(method)
            if isinstance(n, ast.Name) and n.id == "prochainIDligne" and isinstance(n.ctx, ast.Load)
        ]

        neutral_defaults = [
            node
            for node in assignments
            if isinstance(node.value, ast.Constant) and node.value.value is None
        ]
        self.assertEqual(len(neutral_defaults), 1)
        self.assertNotIn(neutral_defaults[0], protected_nodes)

        local_assignments = [node for node in assignments if node is not neutral_defaults[0]]
        self.assertEqual(len(local_assignments), 2)
        self.assertEqual(len(increments), 1)
        self.assertEqual(len(loads), 1)

        for node in local_assignments + increments + loads:
            self.assertIn(node, protected_nodes, ast.dump(node))

    def test_branch_assignment_gap_is_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE_PATH, SOURCE_ROOT)
        targeted = [
            item
            for item in findings
            if item.get("function") == "Sauvegarde_tarifs" and item.get("name") == "prochainIDligne"
        ]
        self.assertEqual(targeted, [], targeted)


if __name__ == "__main__":
    unittest.main()
