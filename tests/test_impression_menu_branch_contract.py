import ast
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SOURCE = SOURCE_ROOT / "Utils" / "UTILS_Impression_menu.py"


class ImpressionMenuBranchContractTests(unittest.TestCase):
    def test_seven_targeted_gaps_are_gone(self):
        targeted_names = {
            ("Dessine_titre", "largeur_box"),
            ("Dessine_texte", "separateur_image"),
            ("__init__", "liste_pages"),
            ("__init__", "nbre_colonnes"),
            ("__init__", "texte_titre"),
            ("__init__", "nbre_lignes"),
            ("__init__", "calendrier"),
        }
        leftovers = []
        for item in audit_branch_assignment_gaps.scan_file(SOURCE, SOURCE_ROOT):
            if (item.get("function"), item.get("name")) in targeted_names:
                leftovers.append(item)
        self.assertEqual(leftovers, [], leftovers)

    def test_print_type_contract_is_exhaustive(self):
        source = SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        impression = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "Impression"
        )
        init = next(
            node for node in impression.body
            if isinstance(node, ast.FunctionDef) and node.name == "__init__"
        )
        segment = ast.get_source_segment(source, init)
        self.assertIn('elif dictDonnees["type"] == "hebdomadaire"', segment)
        self.assertIn('elif dictDonnees["type"] == "quotidien"', segment)
        self.assertIn("raise ValueError", segment)
        self.assertIn("Type d'impression de menu inconnu", segment)

    def test_missing_separator_image_is_explicitly_neutral(self):
        source = SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        case = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "Case"
        )
        draw = next(
            node for node in case.body
            if isinstance(node, ast.FunctionDef) and node.name == "Dessine_texte"
        )
        segment = ast.get_source_segment(source, draw)
        self.assertIn("separateur_image = None", segment)
        self.assertIn("separateur_image is not None", segment)


if __name__ == "__main__":
    unittest.main()
