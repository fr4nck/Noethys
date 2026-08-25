# -*- coding: utf-8 -*-
import ast
import datetime
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps


ROOT = Path(__file__).resolve().parents[1]
FICHIER = ROOT / "noethys" / "Utils" / "UTILS_Dates.py"


def _charger_heure_str_en_delta():
    arbre = ast.parse(FICHIER.read_text(encoding="utf-8"), filename=str(FICHIER))
    fonction = next(
        noeud
        for noeud in arbre.body
        if isinstance(noeud, ast.FunctionDef) and noeud.name == "HeureStrEnDelta"
    )
    module = ast.Module(body=[fonction], type_ignores=[])
    ast.fix_missing_locations(module)
    espace = {"datetime": datetime}
    exec(compile(module, str(FICHIER), "exec"), espace)
    return espace["HeureStrEnDelta"]


def _charger_calculer_arrondi():
    arbre = ast.parse(FICHIER.read_text(encoding="utf-8"), filename=str(FICHIER))
    fonction = next(
        noeud
        for noeud in arbre.body
        if isinstance(noeud, ast.FunctionDef) and noeud.name == "CalculerArrondi"
    )
    module = ast.Module(body=[fonction], type_ignores=[])
    ast.fix_missing_locations(module)
    espace = {
        "SoustractionHeures": lambda heure_fin, heure_debut: datetime.timedelta(minutes=90),
        "ArrondirTime": lambda **kwargs: kwargs["heure"],
        "ArrondirDelta": lambda **kwargs: kwargs["duree"],
    }
    exec(compile(module, str(FICHIER), "exec"), espace)
    return espace["CalculerArrondi"]


class UtilsDatesDurationTests(unittest.TestCase):
    def test_les_formats_historiques_restent_acceptes(self):
        convertir = _charger_heure_str_en_delta()

        self.assertEqual(convertir(None), datetime.timedelta(0))
        self.assertEqual(convertir(""), datetime.timedelta(0))
        self.assertEqual(convertir("2"), datetime.timedelta(hours=2))
        self.assertEqual(convertir("2h30"), datetime.timedelta(hours=2, minutes=30))
        self.assertEqual(convertir("2:30"), datetime.timedelta(hours=2, minutes=30))
        self.assertEqual(convertir("2:30:45"), datetime.timedelta(hours=2, minutes=30))

    def test_un_format_avec_trop_de_segments_ne_leve_plus_unboundlocalerror(self):
        convertir = _charger_heure_str_en_delta()

        self.assertEqual(convertir("01:30:00:00"), datetime.timedelta(0))

    def test_l_audit_ne_signale_plus_heures_ou_minutes_non_definies(self):
        signaux = [
            signal
            for signal in audit_branch_assignment_gaps.scan_file(FICHIER)
            if signal["function"] == "HeureStrEnDelta"
            and signal["name"] in {"heures", "minutes"}
        ]

        self.assertEqual(signaux, [])

    def test_un_type_arrondi_inconnu_conserve_la_duree_reelle(self):
        calculer = _charger_calculer_arrondi()

        resultat = calculer(
            arrondi_type="type_inconnu",
            arrondi_delta=5,
            heure_debut=datetime.time(8, 0),
            heure_fin=datetime.time(9, 30),
        )

        self.assertEqual(resultat, datetime.timedelta(minutes=90))

    def test_l_audit_ne_signale_plus_duree_arrondie_non_definie(self):
        signaux = [
            signal
            for signal in audit_branch_assignment_gaps.scan_file(FICHIER)
            if signal["function"] == "CalculerArrondi"
            and signal["name"] == "duree_arrondie"
        ]

        self.assertEqual(signaux, [])


if __name__ == "__main__":
    unittest.main()
