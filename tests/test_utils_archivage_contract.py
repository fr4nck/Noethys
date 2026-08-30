import ast
import pathlib
import unittest

from scripts import audit_branch_assignment_gaps

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SOURCE = SOURCE_ROOT / "Utils" / "UTILS_Archivage.py"


def load_helper():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_GetArchivageEtat")
    module = ast.Module(body=[node], type_ignores=[])
    ns = {"_": lambda value: value}
    exec(compile(module, str(SOURCE), "exec"), ns)
    return ns["_GetArchivageEtat"]


class ArchivageContractTests(unittest.TestCase):
    def test_supported_states_preserve_historical_values(self):
        helper = load_helper()
        self.assertEqual(helper("archiver"), ("archive", "archiver"))
        self.assertEqual(helper("desarchiver"), (None, "désarchiver"))

    def test_unsupported_state_is_explicit(self):
        with self.assertRaises(ValueError):
            load_helper()("inconnu")

    def test_targeted_gaps_disappear(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE, SOURCE_ROOT)
        targeted = [
            item for item in findings
            if (item.get("function"), item.get("name")) in {
                ("Archiver_familles", "label"),
                ("Archiver_familles", "valeur"),
                ("Archiver_individus", "label"),
                ("Archiver_individus", "valeur"),
                ("GetCoches", "nom_complet"),
            }
        ]
        self.assertEqual(targeted, [], targeted)

    def test_module_parses(self):
        ast.parse(SOURCE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
