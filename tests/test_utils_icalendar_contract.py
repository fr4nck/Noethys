# -*- coding: utf-8 -*-
import ast
import datetime
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FICHIER = ROOT / "noethys" / "Utils" / "UTILS_Icalendar.py"


def _charger_get_vacances():
    arbre = ast.parse(FICHIER.read_text(encoding="utf-8"), filename=str(FICHIER))
    classe = next(
        noeud
        for noeud in arbre.body
        if isinstance(noeud, ast.ClassDef) and noeud.name == "Calendrier"
    )
    fonction = next(
        noeud
        for noeud in classe.body
        if isinstance(noeud, ast.FunctionDef) and noeud.name == "GetVacances"
    )
    module = ast.Module(body=[fonction], type_ignores=[])
    ast.fix_missing_locations(module)
    espace = {
        "_": lambda texte: texte,
        "datetime": datetime,
        "six": types.SimpleNamespace(PY2=False),
    }
    exec(compile(module, str(FICHIER), "exec"), espace)
    return espace["GetVacances"]


class FauxCalendrier:
    def __init__(self, evenements):
        self.evenements = evenements

    def GetEvents(self):
        return self.evenements


class UtilsIcalendarTests(unittest.TestCase):
    def test_un_evenement_sans_rapport_est_ignore(self):
        get_vacances = _charger_get_vacances()
        calendrier = FauxCalendrier([
            {
                "description": "Réunion pédagogique",
                "date_debut": None,
                "date_fin": None,
            },
        ])

        self.assertEqual(get_vacances(calendrier), [])

    def test_un_evenement_incomplet_est_ignore(self):
        get_vacances = _charger_get_vacances()
        calendrier = FauxCalendrier([
            {"description": None, "date_debut": None, "date_fin": None},
            {"description": "Vacances d'été", "date_debut": None, "date_fin": None},
        ])

        self.assertEqual(get_vacances(calendrier), [])

    def test_les_bornes_des_grandes_vacances_restent_extraites(self):
        get_vacances = _charger_get_vacances()
        calendrier = FauxCalendrier([
            {
                "description": "Vacances d'été",
                "date_debut": datetime.date(2026, 7, 4),
                "date_fin": datetime.date(2026, 7, 5),
            },
            {
                "description": "Rentrée des élèves",
                "date_debut": datetime.date(2026, 9, 1),
                "date_fin": datetime.date(2026, 9, 2),
            },
        ])

        self.assertEqual(
            get_vacances(calendrier),
            [{
                "annee": 2026,
                "nom": "Eté",
                "date_debut": datetime.date(2026, 7, 5),
                "date_fin": datetime.date(2026, 8, 31),
            }],
        )


if __name__ == "__main__":
    unittest.main()
