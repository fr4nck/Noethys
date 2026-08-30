import ast
import pathlib
import unittest

from scripts import audit_branch_assignment_gaps

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Utils" / "UTILS_Export.py"
SOURCE_ROOT = ROOT / "noethys"


class UtilsExportBranchContractTests(unittest.TestCase):
    def test_targeted_gaps_are_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE, SOURCE_ROOT)
        targeted_names = {"listeSelections", "cheminFichier", "heures", "minutes"}
        targeted = [x for x in findings if x.get("name") in targeted_names and x.get("function") in {"ExportTexte", "ExportExcel", "RechercheFormat"}]
        self.assertEqual(targeted, [], targeted)

    def test_module_parses(self):
        ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))

    def test_time_parser_uses_first_two_fields_only_for_supported_shapes(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        export_excel = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "ExportExcel")
        recherche = next(n for n in ast.walk(export_excel) if isinstance(n, ast.FunctionDef) and n.name == "RechercheFormat")

        length_guard = next(
            n for n in ast.walk(recherche)
            if isinstance(n, ast.If)
            and isinstance(n.test, ast.Compare)
            and len(n.test.ops) == 1
            and isinstance(n.test.ops[0], ast.In)
            and isinstance(n.test.left, ast.Call)
            and isinstance(n.test.left.func, ast.Name)
            and n.test.left.func.id == "len"
            and ast.literal_eval(n.test.comparators[0]) == (2, 3)
        )
        self.assertEqual(ast.literal_eval(length_guard.test.comparators[0]), (2, 3))

        unpack = next(
            n for n in ast.walk(length_guard)
            if isinstance(n, ast.Assign)
            and len(n.targets) == 1
            and isinstance(n.targets[0], (ast.Tuple, ast.List))
            and all(isinstance(elt, ast.Name) for elt in n.targets[0].elts)
            and [elt.id for elt in n.targets[0].elts] == ["heures", "minutes"]
        )
        self.assertIsInstance(unpack.value, ast.Subscript)
        self.assertIsInstance(unpack.value.value, ast.Name)
        self.assertEqual(unpack.value.value.id, "donnees")
        self.assertIsInstance(unpack.value.slice, ast.Slice)
        self.assertIsNone(unpack.value.slice.lower)
        self.assertEqual(ast.literal_eval(unpack.value.slice.upper), 2)


if __name__ == "__main__":
    unittest.main()
