import ast
import pathlib
import unittest

from scripts import audit_branch_assignment_gaps

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SOURCES = (
    SOURCE_ROOT / "Dlg" / "DLG_Saisie_typesVaccins.py",
    SOURCE_ROOT / "Dlg" / "DLG_Envoi_sms.py",
    SOURCE_ROOT / "Dlg" / "DLG_Selection_mails.py",
)


class SmallUiBranchContractsTests(unittest.TestCase):
    def test_targeted_gaps_are_gone(self):
        names = {"jours", "mois", "annees", "xRond", "yRond"}
        targeted = []
        for source in SOURCES:
            targeted.extend(
                item
                for item in audit_branch_assignment_gaps.scan_file(source, SOURCE_ROOT)
                if item["name"] in names
                and item["function"] in {"SetValidite", "AjouteTexteImage"}
            )
        self.assertEqual(targeted, [], targeted)

    def test_modules_parse(self):
        for source in SOURCES:
            ast.parse(source.read_text(encoding="utf-8"), filename=str(source))

    def test_vaccine_defaults_are_explicit(self):
        text = SOURCES[0].read_text(encoding="utf-8")
        self.assertIn("jours = 0\n        mois = 0\n        annees = 0", text)

    def test_alignment_helpers_reject_incomplete_alignment(self):
        for source in SOURCES[1:]:
            tree = ast.parse(source.read_text(encoding="utf-8"))
            helper = next(
                n
                for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and n.name == "AjouteTexteImage"
            )
            self.assertGreaterEqual(
                sum(isinstance(n, ast.Raise) for n in ast.walk(helper)), 2
            )

    def test_alignment_helpers_keep_historical_right_bottom_precedence(self):
        for source in SOURCES[1:]:
            text = source.read_text(encoding="utf-8")
            self.assertLess(text.index('if "droite" in alignement'), text.index('elif "gauche" in alignement'))
            self.assertLess(text.index('if "bas" in alignement'), text.index('elif "haut" in alignement'))


if __name__ == "__main__":
    unittest.main()
