#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import types
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Utils" / "UTILS_Stats_modeles.py"
SOURCE_ROOT = ROOT / "noethys"


def load_get_html():
    """ Extrait GetHTML par AST et l'exécute isolément, sans dépendre de wx/matplotlib. """
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    classe = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "HTML"
    )
    fonction = next(
        node for node in classe.body
        if isinstance(node, ast.FunctionDef) and node.name == "GetHTML"
    )
    module = ast.Module(body=[fonction], type_ignores=[])
    ast.fix_missing_locations(module)

    def DateEngFr(textDate):
        text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
        return text

    def ConvertitCouleur(couleur=(255, 255, 255)):
        return "#%02X%02X%02X" % couleur

    namespace = {
        "DateEngFr": DateEngFr,
        "ConvertitCouleur": ConvertitCouleur,
        "_": lambda texte: texte,
    }
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace["GetHTML"]


class FakeObjet:
    def __init__(self, code, visible=True, texte="contenu"):
        self.code = code
        self.visible = visible
        self.texte = texte

    def GetObjetHTML(self):
        return self.texte


class StatsModelesGetHTMLContractTests(unittest.TestCase):
    def setUp(self):
        self.GetHTML = load_get_html()
        objet = FakeObjet("obj1")
        self.fake_self = types.SimpleNamespace(
            dictParametres={
                "listeActivites": [1],
                "dictActivites": {1: "Activité 1"},
                "mode": "inscrits",
                "periode": {"date_debut": "2024-01-01", "date_fin": "2024-01-31"},
            },
            liste_objets=[{
                "code": "rub1",
                "nom": "Rubrique 1",
                "pages": [{
                    "code": "page1",
                    "nom": "Page 1",
                    "objets": [objet],
                }],
            }],
            MAJ=lambda page=None: None,
        )

    def test_targeted_gap_is_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE, SOURCE_ROOT)
        targeted = [
            item for item in findings
            if item.get("function") == "GetHTML" and item.get("name") == "html"
        ]
        self.assertEqual(targeted, [], targeted)

    def test_mode_affichage_est_preserve(self):
        resultat = self.GetHTML(self.fake_self, mode="affichage")
        self.assertIn("<HTML><BODY><FONT SIZE=-1>", resultat)
        self.assertIn("contenu", resultat)

    def test_mode_impression_est_preserve(self):
        resultat = self.GetHTML(self.fake_self, mode="impression", selectionsCodes=["rub1", "page1", "obj1"])
        self.assertIn("<HTML><BODY>", resultat)
        self.assertIn("contenu", resultat)

    def test_mode_inconnu_leve_une_erreur_explicite_plutot_qu_une_unboundlocalerror(self):
        with self.assertRaises(ValueError):
            self.GetHTML(self.fake_self, mode="mode_inexistant")

    def test_mode_par_defaut_reste_affichage(self):
        resultat = self.GetHTML(self.fake_self)
        self.assertIn("<HTML><BODY><FONT SIZE=-1>", resultat)


if __name__ == "__main__":
    unittest.main()
