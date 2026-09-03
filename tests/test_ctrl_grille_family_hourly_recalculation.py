import ast
import copy
import datetime
import functools
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Ctrl" / "CTRL_Grille.py"


def _load_facturation():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    function = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "Facturation"
    )
    module = ast.Module(body=[copy.deepcopy(function)], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {
        "copy": copy,
        "functools": functools,
        "six": types.SimpleNamespace(PY2=False),
        "HeureStrEnTime": lambda value: datetime.datetime.strptime(value, "%H:%M").time(),
    }
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace["Facturation"]


def _conso(IDprestation, heure_debut=None, heure_fin=None):
    return types.SimpleNamespace(
        IDactivite=1,
        forfait=None,
        etat="reservation",
        quantite=None,
        IDprestation=IDprestation,
        IDevenement=None,
        case=None,
        heure_debut=heure_debut,
        heure_fin=heure_fin,
        IDunite=10,
    )


class CtrlGrilleFamilyHourlyRecalculationTests(unittest.TestCase):
    def test_deleting_family_member_keeps_remaining_sibling_hourly_bracket(self):
        facturation = _load_facturation()
        date = datetime.date(2026, 9, 3)

        family_tariff = {
            "IDtarif": 200,
            "methode": "horaire_montant_unique_nbre_ind",
            "lignes_calcul": [
                {
                    "heure_debut_min": "08:00",
                    "heure_debut_max": "09:59",
                    "heure_fin_min": "08:01",
                    "heure_fin_max": "10:00",
                    "montant_enfant_1": 10.0,
                    "montant_enfant_2": 20.0,
                    "montant_enfant_3": None,
                    "montant_enfant_4": None,
                    "montant_enfant_5": None,
                    "montant_enfant_6": None,
                },
                {
                    "heure_debut_min": "10:00",
                    "heure_debut_max": "10:30",
                    "heure_fin_min": "11:30",
                    "heure_fin_max": "12:30",
                    "montant_enfant_1": 30.0,
                    "montant_enfant_2": 40.0,
                    "montant_enfant_3": None,
                    "montant_enfant_4": None,
                    "montant_enfant_5": None,
                    "montant_enfant_6": None,
                },
            ],
        }

        state = types.SimpleNamespace(
            dictConsoIndividus={
                1: {date: {10: [_conso(100)]}},
                2: {date: {10: [_conso(101, "10:00", "12:00")] }},
            },
            dictActivites={1: {"tarifs": {50: [], 99: [family_tariff]}}},
            dictForfaits={},
            dictPrestations={
                100: {
                    "date": date,
                    "IDfamille": 10,
                    "IDtarif": 200,
                    "IDindividu": 1,
                },
                101: {
                    "date": date,
                    "IDfamille": 10,
                    "IDtarif": 200,
                    "IDindividu": 2,
                    "montant_initial": 30.0,
                    "montant": 30.0,
                },
            },
            listePrestationsSupprimees=[],
            listePrestationsModifiees=[],
            dictDeductions={},
            mode="date",
            TriTarifs2=lambda left, right: 0,
            TriTarifs=lambda left, right: 0,
        )

        facturation(
            state,
            IDactivite=1,
            IDindividu=1,
            IDfamille=10,
            date=date,
            IDcategorie_tarif=50,
        )

        # Le membre restant est toujours dans la seconde tranche horaire :
        # seul le rang familial change, pas sa tranche horaire.
        self.assertEqual(state.dictPrestations[101]["montant_initial"], 30.0)
        self.assertEqual(state.dictPrestations[101]["montant"], 30.0)

    def test_degressive_siblings_keep_their_own_hourly_brackets(self):
        facturation = _load_facturation()
        date = datetime.date(2026, 9, 3)

        family_tariff = {
            "IDtarif": 200,
            "methode": "horaire_montant_unique_nbre_ind_degr",
            "lignes_calcul": [
                {
                    "heure_debut_min": "08:00",
                    "heure_debut_max": "09:59",
                    "heure_fin_min": "08:01",
                    "heure_fin_max": "10:00",
                    "montant_enfant_1": 10.0,
                    "montant_enfant_2": 20.0,
                    "montant_enfant_3": None,
                    "montant_enfant_4": None,
                    "montant_enfant_5": None,
                    "montant_enfant_6": None,
                },
                {
                    "heure_debut_min": "10:00",
                    "heure_debut_max": "10:30",
                    "heure_fin_min": "11:30",
                    "heure_fin_max": "12:30",
                    "montant_enfant_1": 30.0,
                    "montant_enfant_2": 40.0,
                    "montant_enfant_3": None,
                    "montant_enfant_4": None,
                    "montant_enfant_5": None,
                    "montant_enfant_6": None,
                },
            ],
        }

        state = types.SimpleNamespace(
            dictConsoIndividus={
                1: {date: {10: [_conso(100)]}},
                2: {date: {10: [_conso(101, "08:30", "09:30")] }},
                3: {date: {10: [_conso(102, "10:00", "12:00")] }},
            },
            dictActivites={1: {"tarifs": {50: [], 99: [family_tariff]}}},
            dictForfaits={},
            dictPrestations={
                100: {
                    "date": date,
                    "IDfamille": 10,
                    "IDtarif": 200,
                    "IDindividu": 1,
                },
                101: {
                    "date": date,
                    "IDfamille": 10,
                    "IDtarif": 200,
                    "IDindividu": 2,
                    "montant_initial": 10.0,
                    "montant": 10.0,
                },
                102: {
                    "date": date,
                    "IDfamille": 10,
                    "IDtarif": 200,
                    "IDindividu": 3,
                    "montant_initial": 40.0,
                    "montant": 40.0,
                },
            },
            listePrestationsSupprimees=[],
            listePrestationsModifiees=[],
            dictDeductions={},
            mode="date",
            TriTarifs2=lambda left, right: 0,
            TriTarifs=lambda left, right: 0,
        )

        facturation(
            state,
            IDactivite=1,
            IDindividu=1,
            IDfamille=10,
            date=date,
            IDcategorie_tarif=50,
        )

        self.assertEqual(state.dictPrestations[101]["montant_initial"], 10.0)
        self.assertEqual(state.dictPrestations[102]["montant_initial"], 40.0)


if __name__ == "__main__":
    unittest.main()
