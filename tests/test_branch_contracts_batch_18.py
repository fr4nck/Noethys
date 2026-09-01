#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ast
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
AUDIT = ROOT / "scripts" / "audit_branch_assignment_gaps.py"
spec = importlib.util.spec_from_file_location("audit_branch_assignment_gaps", AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

NOMIN_RESULTATS = NOETHYS / "Ol/OL_Etat_nomin_resultats.py"
STATS_MODELES = NOETHYS / "Utils/UTILS_Stats_modeles.py"


def load_questionnaire_assignment(traduction):
    """ Extrait la boucle d'affectation des réponses de questionnaire de
    Track.__init__ (Ol/OL_Etat_nomin_resultats.py) et l'exécute isolément,
    avec une fonction de traduction fournie par le test. """
    tree = ast.parse(NOMIN_RESULTATS.read_text(encoding="utf-8"))
    track_class = next(
        n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Track"
    )
    init_method = next(
        n for n in track_class.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"
    )
    boucle = next(
        n for n in init_method.body
        if isinstance(n, ast.For) and getattr(n.target, "id", None) == "champ"
    )

    fonction = ast.FunctionDef(
        name="assigner_reponses",
        args=ast.arguments(
            posonlyargs=[], args=[
                ast.arg(arg="self"), ast.arg(arg="listeChamps"),
                ast.arg(arg="IDindividu"), ast.arg(arg="IDfamille"),
            ],
            vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[],
        ),
        body=[boucle],
        decorator_list=[],
    )
    module = ast.Module(body=[fonction], type_ignores=[])
    ast.fix_missing_locations(module)

    reponses = {}

    def GetReponse(IDquestion=None, ID=None):
        return reponses.get((IDquestion, ID), u"")

    class FakeSelf(object):
        pass

    namespace = {"GetReponse": GetReponse, "_": traduction}
    exec(compile(module, str(NOMIN_RESULTATS), "exec"), namespace)

    def executer(listeChamps, IDindividu, IDfamille, reponses_disponibles):
        reponses.clear()
        reponses.update(reponses_disponibles)
        target = FakeSelf()
        namespace["assigner_reponses"](target, listeChamps, IDindividu, IDfamille)
        return target

    return executer


class FakeChamp(object):
    def __init__(self, type, categorie, code):
        self.type = type
        self.categorie = categorie
        self.code = code


class TestBatch18NominResultatsQuestionnaireCategorie(unittest.TestCase):
    def test_targeted_finding_disappears(self):
        remaining = {
            (item["file"], item["function"], item["name"])
            for item in audit.scan_file(NOMIN_RESULTATS, NOETHYS)
            if item["function"] == "__init__" and item["name"] == "IDtemp"
        }
        self.assertEqual(remaining, set())

    def test_french_default_behaviour_is_preserved(self):
        # Sans traduction chargée, _() renvoie la chaîne telle quelle : le
        # comportement historique (locale française) ne doit pas changer.
        executer = load_questionnaire_assignment(lambda texte: texte)
        champ = FakeChamp("QUESTION", u"Individu", "QUESTION42")
        resultat = executer([champ], IDindividu=7, IDfamille=99, reponses_disponibles={(42, 7): u"Oui"})
        self.assertEqual(resultat.QUESTION42, u"Oui")

        champ_famille = FakeChamp("QUESTION", u"Famille", "QUESTION42")
        resultat = executer([champ_famille], IDindividu=7, IDfamille=99, reponses_disponibles={(42, 99): u"Non"})
        self.assertEqual(resultat.QUESTION42, u"Non")

    def test_translated_categorie_no_longer_raises_unbound_local_error(self):
        # Avec un pack de langue (ex. en_GB.lang), OL_Etat_nomin_champs.py
        # affecte categorie = _(u"Individu") / _(u"Famille"), donc une
        # valeur traduite. Avant le correctif, la comparaison figée sur les
        # libellés français provoquait un UnboundLocalError sur IDtemp.
        traductions = {u"Individu": u"Individual", u"Famille": u"Family"}
        executer = load_questionnaire_assignment(lambda texte: traductions.get(texte, texte))

        champ = FakeChamp("QUESTION", u"Individual", "QUESTION42")
        resultat = executer([champ], IDindividu=7, IDfamille=99, reponses_disponibles={(42, 7): u"Yes"})
        self.assertEqual(resultat.QUESTION42, u"Yes")

        champ_famille = FakeChamp("QUESTION", u"Family", "QUESTION42")
        resultat = executer([champ_famille], IDindividu=7, IDfamille=99, reponses_disponibles={(42, 99): u"No"})
        self.assertEqual(resultat.QUESTION42, u"No")

    def test_unknown_categorie_raises_explicit_error_instead_of_unbound_local(self):
        # Hors contrat (catégorie ni Individu ni Famille) : une erreur
        # explicite est levée plutôt qu'un UnboundLocalError silencieux.
        executer = load_questionnaire_assignment(lambda texte: texte)
        champ = FakeChamp("QUESTION", u"Autre", "QUESTION42")
        with self.assertRaises(ValueError):
            executer([champ], IDindividu=7, IDfamille=99, reponses_disponibles={})


class TestBatch18StatsModelesGetHTMLContract(unittest.TestCase):
    def test_targeted_finding_disappears(self):
        remaining = {
            (item["file"], item["function"], item["name"])
            for item in audit.scan_file(STATS_MODELES, NOETHYS)
            if item["function"] == "GetHTML" and item["name"] == "html"
        }
        self.assertEqual(remaining, set())

    def test_only_affichage_and_impression_modes_are_supported(self):
        source = STATS_MODELES.read_text(encoding="utf-8")
        self.assertIn(
            'else :\n            raise ValueError',
            source,
        )

    def test_unsupported_mode_raises_explicit_error_instead_of_unbound_local(self):
        tree = ast.parse(STATS_MODELES.read_text(encoding="utf-8"))

        get_html = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "GetHTML":
                get_html = node
                break
        self.assertIsNotNone(get_html)

        fonction = ast.FunctionDef(
            name="get_html_standalone",
            args=get_html.args,
            body=get_html.body,
            decorator_list=[],
        )
        module = ast.Module(body=[fonction], type_ignores=[])
        ast.fix_missing_locations(module)

        namespace = {"_": lambda texte: texte, "u": str}
        exec(compile(module, str(STATS_MODELES), "exec"), namespace)

        class FakeSelf(object):
            dictParametres = {"listeActivites": [1]}
            liste_objets = []

        with self.assertRaises(ValueError):
            namespace["get_html_standalone"](FakeSelf(), mode="inconnu")


if __name__ == "__main__":
    unittest.main()
