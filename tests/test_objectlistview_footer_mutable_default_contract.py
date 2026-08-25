# -*- coding: utf-8 -*-
import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FICHIER = ROOT / "noethys" / "Ctrl" / "CTRL_ObjectListView.py"


def _constructeur_panel_avec_footer():
    arbre = ast.parse(FICHIER.read_text(encoding="utf-8"), filename=str(FICHIER))
    classe = next(
        noeud
        for noeud in arbre.body
        if isinstance(noeud, ast.ClassDef) and noeud.name == "PanelAvecFooter"
    )
    return next(
        noeud
        for noeud in classe.body
        if isinstance(noeud, ast.FunctionDef) and noeud.name == "__init__"
    )


class ObjectListViewFooterMutableDefaultTests(unittest.TestCase):
    def test_les_dictionnaires_optionnels_ne_sont_pas_partages(self):
        constructeur = _constructeur_panel_avec_footer()
        parametres = [argument.arg for argument in constructeur.args.args]
        defauts = [None] * (len(parametres) - len(constructeur.args.defaults)) + list(constructeur.args.defaults)
        defauts_par_nom = dict(zip(parametres, defauts))

        for nom in ("kwargs", "dictColonnes"):
            with self.subTest(parametre=nom):
                self.assertIsInstance(defauts_par_nom[nom], ast.Constant)
                self.assertIsNone(defauts_par_nom[nom].value)

    def test_les_dictionnaires_manquants_sont_crees_dans_l_appel(self):
        constructeur = _constructeur_panel_avec_footer()
        initialisations = set()

        for noeud in constructeur.body:
            if not isinstance(noeud, ast.If) or not isinstance(noeud.test, ast.Compare):
                continue
            if not isinstance(noeud.test.left, ast.Name):
                continue
            if not isinstance(noeud.test.ops[0], ast.Is):
                continue
            if not isinstance(noeud.test.comparators[0], ast.Constant):
                continue
            if noeud.test.comparators[0].value is not None:
                continue
            affectation = noeud.body[0]
            if not isinstance(affectation, ast.Assign) or not isinstance(affectation.value, ast.Dict):
                continue
            if isinstance(affectation.targets[0], ast.Name) and affectation.targets[0].id == noeud.test.left.id:
                initialisations.add(noeud.test.left.id)

        self.assertEqual(initialisations, {"kwargs", "dictColonnes"})

    def test_kwargs_recoit_toujours_le_panel_courant_comme_parent(self):
        constructeur = _constructeur_panel_avec_footer()
        affectations_parent = [
            noeud
            for noeud in ast.walk(constructeur)
            if isinstance(noeud, ast.Assign)
            and isinstance(noeud.targets[0], ast.Subscript)
            and isinstance(noeud.targets[0].value, ast.Name)
            and noeud.targets[0].value.id == "kwargs"
            and isinstance(noeud.value, ast.Name)
            and noeud.value.id == "self"
        ]

        self.assertTrue(affectations_parent)


if __name__ == "__main__":
    unittest.main()
