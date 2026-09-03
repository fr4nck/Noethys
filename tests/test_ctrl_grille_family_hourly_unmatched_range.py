import ast
import copy
import datetime
import decimal
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Ctrl" / "CTRL_Grille.py"


def _load_calcule_tarif():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
    function = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "CalculeTarif"
    )
    module = ast.Module(body=[copy.deepcopy(function)], type_ignores=[])
    ast.fix_missing_locations(module)

    def heure_str_en_time(value):
        if value in (None, ""):
            return None
        return datetime.datetime.strptime(value, "%H:%M").time()

    namespace = {
        "datetime": datetime,
        "decimal": decimal,
        "HeureStrEnTime": heure_str_en_time,
        "SoustractionHeures": lambda fin, debut: (
            datetime.timedelta(hours=fin.hour, minutes=fin.minute)
            - datetime.timedelta(hours=debut.hour, minutes=debut.minute)
        ),
        "FloatToDecimal": lambda value, plusProche=True: decimal.Decimal(str(value)),
    }
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace["CalculeTarif"]


class CtrlGrilleFamilyHourlyUnmatchedRangeTests(unittest.TestCase):
    def test_hourly_family_tariff_without_matching_range_stays_neutral(self):
        calcule_tarif = _load_calcule_tarif()
        date = datetime.date(2026, 9, 3)
        conso = types.SimpleNamespace(heure_debut="14:00", heure_fin="15:00")

        state = types.SimpleNamespace(
            dictConsoIndividus={1: {date: {10: [conso]}}},
            dictPrestations={},
            RechercheQF=lambda *args, **kwargs: None,
            GetQuestionnaire=lambda *args, **kwargs: None,
        )
        tarif = {
            "IDtarif": 200,
            "IDactivite": 1,
            "nom_tarif": "Tarif famille horaire",
            "description_tarif": "Tarif famille horaire",
            "label_prestation": None,
            "methode": "horaire_montant_unique_nbre_ind",
            "lignes_calcul": [
                {
                    "heure_debut_min": "08:00",
                    "heure_debut_max": "09:00",
                    "heure_fin_min": "09:00",
                    "heure_fin_max": "10:00",
                    "montant_unique": 0.0,
                    "montant_questionnaire": None,
                    "montant_enfant_1": 10.0,
                    "montant_enfant_2": 20.0,
                    "montant_enfant_3": None,
                    "montant_enfant_4": None,
                    "montant_enfant_5": None,
                    "montant_enfant_6": None,
                    "temps_facture": None,
                    "label": None,
                }
            ],
        }

        montant, _label, _temps = calcule_tarif(
            state,
            dictTarif=tarif,
            combinaisons_unites=[10],
            date=date,
            temps_facture=None,
            IDfamille=10,
            IDindividu=1,
            quantite=None,
            case=None,
            modeSilencieux=True,
            evenement=None,
            action="saisie",
        )

        # Une consommation hors de toutes les plages horaires ne doit pas hériter
        # des montants de la première ligne de calcul.
        self.assertEqual(montant, 0.0)

    def test_hourly_branch_resets_all_family_rank_amounts_before_matching(self):
        source = SOURCE.read_text(encoding="utf-8")
        start = source.index('            if "horaire" in methode_calcul  :')
        end = source.index("                # Recherche des heures debut et fin des unités cochées", start)
        hourly_prologue = source[start:end]

        for rank in range(1, 7):
            self.assertIn(f"montant_enfant_{rank} = None", hourly_prologue)


if __name__ == "__main__":
    unittest.main()
