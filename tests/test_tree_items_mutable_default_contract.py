# -*- coding: utf-8 -*-
import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FICHIERS = (
    ROOT / "noethys" / "Ctrl" / "CTRL_Evenements.py",
    ROOT / "noethys" / "Ctrl" / "CTRL_Etiquettes.py",
    ROOT / "noethys" / "Ctrl" / "CTRL_Portail_pages.py",
)


def _get_items_enfants(path):
    arbre = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    fonctions = [
        noeud
        for noeud in ast.walk(arbre)
        if isinstance(noeud, ast.FunctionDef) and noeud.name == "GetItemsEnfants"
    ]
    assert len(fonctions) == 1
    return fonctions[0]


class TreeItemsMutableDefaultTests(unittest.TestCase):
    def test_get_items_enfants_ne_conserve_pas_de_liste_dans_sa_signature(self):
        for path in FICHIERS:
            with self.subTest(path=path):
                fonction = _get_items_enfants(path)
                parametres = [argument.arg for argument in fonction.args.args]
                defauts = [None] * (len(parametres) - len(fonction.args.defaults)) + list(fonction.args.defaults)
                defaut_liste = dict(zip(parametres, defauts))["liste"]

                self.assertIsInstance(defaut_liste, ast.Constant)
                self.assertIsNone(defaut_liste.value)

    def test_get_items_enfants_cree_une_liste_locale_si_elle_manque(self):
        for path in FICHIERS:
            with self.subTest(path=path):
                fonction = _get_items_enfants(path)
                premiere_instruction = fonction.body[0]

                self.assertIsInstance(premiere_instruction, ast.If)
                self.assertIsInstance(premiere_instruction.test, ast.Compare)
                self.assertIsInstance(premiere_instruction.test.left, ast.Name)
                self.assertEqual(premiere_instruction.test.left.id, "liste")
                self.assertIsInstance(premiere_instruction.test.ops[0], ast.Is)
                self.assertIsInstance(premiere_instruction.test.comparators[0], ast.Constant)
                self.assertIsNone(premiere_instruction.test.comparators[0].value)

                affectation = premiere_instruction.body[0]
                self.assertIsInstance(affectation, ast.Assign)
                self.assertIsInstance(affectation.targets[0], ast.Name)
                self.assertEqual(affectation.targets[0].id, "liste")
                self.assertIsInstance(affectation.value, ast.List)

    def test_get_items_enfants_continue_de_muter_la_liste_fournie(self):
        for path in FICHIERS:
            with self.subTest(path=path):
                fonction = _get_items_enfants(path)
                appels_append = [
                    noeud
                    for noeud in ast.walk(fonction)
                    if isinstance(noeud, ast.Call)
                    and isinstance(noeud.func, ast.Attribute)
                    and isinstance(noeud.func.value, ast.Name)
                    and noeud.func.value.id == "liste"
                    and noeud.func.attr == "append"
                ]

                self.assertTrue(appels_append)


if __name__ == "__main__":
    unittest.main()
