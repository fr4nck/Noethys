# -*- coding: utf-8 -*-
import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FICHIER = ROOT / "noethys" / "Utils" / "UTILS_Stats_modeles.py"


def _charger_get_html():
    arbre = ast.parse(FICHIER.read_text(encoding="utf-8"), filename=str(FICHIER))
    classe = next(
        noeud
        for noeud in arbre.body
        if isinstance(noeud, ast.ClassDef) and noeud.name == "HTML"
    )
    fonction = next(
        noeud
        for noeud in classe.body
        if isinstance(noeud, ast.FunctionDef) and noeud.name == "GetHTML"
    )
    module = ast.Module(body=[fonction], type_ignores=[])
    ast.fix_missing_locations(module)
    espace = {
        "_": lambda texte: texte,
        "DateEngFr": lambda texte: texte,
        "ConvertitCouleur": lambda couleur: "#000000",
    }
    exec(compile(module, str(FICHIER), "exec"), espace)
    return espace["GetHTML"]


class FauxHTML:
    def __init__(self):
        self.liste_objets = []
        self.dictParametres = {
            "listeActivites": [1],
            "mode": "inscrits",
            "dictActivites": {1: "Activité 1"},
        }

    def MAJ(self, page=None):
        pass


class UtilsStatsModelesGetHTMLTests(unittest.TestCase):
    def test_mode_affichage_reste_inchange(self):
        get_html = _charger_get_html()
        instance = FauxHTML()

        resultat = get_html(instance, mode="affichage")

        self.assertEqual(resultat, "<HTML><BODY><FONT SIZE=-1></FONT></BODY></HTML>")

    def test_mode_impression_reste_inchange(self):
        get_html = _charger_get_html()
        instance = FauxHTML()

        resultat = get_html(instance, mode="impression", selectionsCodes=[])

        self.assertTrue(resultat.startswith("<HTML><BODY>"))
        self.assertTrue(resultat.endswith("</FONT></BODY></HTML>"))

    def test_mode_non_supporte_leve_une_erreur_explicite(self):
        get_html = _charger_get_html()
        instance = FauxHTML()

        with self.assertRaises(ValueError):
            get_html(instance, mode="autre")

    def test_liste_activites_vide_retourne_chaine_vide_quel_que_soit_le_mode(self):
        get_html = _charger_get_html()
        instance = FauxHTML()
        instance.dictParametres["listeActivites"] = []

        self.assertEqual(get_html(instance, mode="autre"), "")


if __name__ == "__main__":
    unittest.main()
