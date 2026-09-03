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
    """ Objet minimal reproduisant les attributs utilisés par GetHTML """
    def __init__(self, listeActivites):
        self.liste_objets = []
        self.dictParametres = {"listeActivites": listeActivites}


class UtilsStatsModelesGetHTMLTests(unittest.TestCase):
    def test_mode_affichage_retourne_un_html(self):
        get_html = _charger_get_html()
        objet = FauxHTML(listeActivites=[1])

        resultat = get_html(objet, mode="affichage")

        self.assertIn("<HTML>", resultat)

    def test_mode_impression_retourne_un_html(self):
        get_html = _charger_get_html()
        objet = FauxHTML(listeActivites=[1])
        objet.dictParametres.update({
            "mode": "inscrits",
            "dictActivites": {1: "Activité"},
        })

        resultat = get_html(objet, mode="impression", selectionsCodes=[])

        self.assertIn("<HTML>", resultat)

    def test_liste_activites_vide_retourne_chaine_vide_quel_que_soit_le_mode(self):
        get_html = _charger_get_html()
        objet = FauxHTML(listeActivites=[])

        self.assertEqual(get_html(objet, mode="affichage"), "")
        self.assertEqual(get_html(objet, mode="mode_inconnu"), "")

    def test_mode_non_supporte_leve_une_erreur_explicite(self):
        """ Avant ce contrat, un mode hors 'affichage'/'impression' provoquait un
        UnboundLocalError silencieux sur 'html' plutôt qu'une erreur explicite. """
        get_html = _charger_get_html()
        objet = FauxHTML(listeActivites=[1])

        with self.assertRaises(ValueError):
            get_html(objet, mode="mode_inconnu")


if __name__ == "__main__":
    unittest.main()
