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
        text = ast.unparse(recherche)
        self.assertIn("len(donnees) in (2, 3)", text)
        self.assertIn("heures, minutes = donnees[:2]", text)


if __name__ == "__main__":
    unittest.main()
