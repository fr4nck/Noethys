import ast
import pathlib
import unittest

from scripts import audit_branch_assignment_gaps

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
PIECE = SOURCE_ROOT / "Dlg" / "DLG_Saisie_piece.py"
FILTERS = SOURCE_ROOT / "Dlg" / "DLG_Saisie_filtre_listes.py"


class DialogSelectionBranchContractsTests(unittest.TestCase):
    def test_targeted_gaps_are_gone(self):
        targeted = []
        for source, function, names in ((PIECE, "GetSelectionPiece", {"IDfamille", "IDindividu", "IDtype_piece", "nomPiece"}), (FILTERS, "GetValeur", {"choix", "criteres"})):
            targeted.extend(item for item in audit_branch_assignment_gaps.scan_file(source, SOURCE_ROOT) if item["function"] == function and item["name"] in names)
        self.assertEqual(targeted, [], targeted)

    def test_modules_parse(self):
        ast.parse(PIECE.read_text(encoding="utf-8"), filename=str(PIECE))
        ast.parse(FILTERS.read_text(encoding="utf-8"), filename=str(FILTERS))

    def test_piece_selection_has_explicit_unselected_fallback(self):
        text = PIECE.read_text(encoding="utf-8")
        self.assertIn('        else:\n            return None\n        return { "IDfamille":IDfamille', text)
        self.assertIn('            if donnees["type"] != "piece" :\n                return None', text)

    def test_disabled_filter_returns_neutral_pair(self):
        text = FILTERS.read_text(encoding="utf-8")
        self.assertIn('    def GetValeur(self):\n        choix = None\n        criteres = None', text)


if __name__ == "__main__":
    unittest.main()
