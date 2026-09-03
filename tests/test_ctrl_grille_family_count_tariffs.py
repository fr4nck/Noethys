import ast
import copy
import datetime
import functools
import types
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps as audit

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
SOURCE = NOETHYS / "Ctrl" / "CTRL_Grille.py"


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
    }
    exec(compile(module, str(SOURCE), "exec"), namespace)
    return namespace["Facturation"]


class CtrlGrilleFamilyCountTariffTests(unittest.TestCase):
    def test_zero_family_count_tariff_recalculates_remaining_sibling_to_zero(self):
        facturation = _load_facturation()
        date = datetime.date(2026, 9, 3)

        conso = types.SimpleNamespace(
            IDactivite=1,
            forfait=None,
            etat="reservation",
            quantite=None,
            IDprestation=100,
            IDevenement=None,
            case=None,
        )
        family_tariff = {
            "IDtarif": 200,
            "methode": "montant_unique_nbre_ind",
            "lignes_calcul": [{
                "montant_enfant_1": 0.0,
                "montant_enfant_2": 0.0,
                "montant_enfant_3": 0.0,
                "montant_enfant_4": 0.0,
                "montant_enfant_5": 0.0,
                "montant_enfant_6": 0.0,
            }],
        }
        state = types.SimpleNamespace(
            dictConsoIndividus={1: {date: {10: [conso]}}},
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
                    "montant_initial": 5.0,
                    "montant": 5.0,
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

        self.assertEqual(state.dictPrestations[101]["montant_initial"], 0.0)
        self.assertEqual(state.dictPrestations[101]["montant"], 0.0)
        self.assertIn(101, state.listePrestationsModifiees)
        self.assertNotIn(100, state.dictPrestations)
        self.assertIn(100, state.listePrestationsSupprimees)

    def test_zero_default_is_defined_before_degressive_branch(self):
        source = SOURCE.read_text(encoding="utf-8")
        anchor = "nbreIndividus = len(listeIndividusPresents)"
        branch = 'if "degr" in methode_calcul :'
        after_anchor = source.split(anchor, 1)[1]
        before_branch = after_anchor.split(branch, 1)[0]
        self.assertIn("montant_tarif_tmp = 0.0", before_branch)

    def test_montant_tarif_tmp_branch_gap_disappears(self):
        findings = audit.scan_file(SOURCE, NOETHYS)
        targeted = [
            item for item in findings
            if item["function"] == "Facturation"
            and item["name"] == "montant_tarif_tmp"
        ]
        self.assertEqual(targeted, [])


if __name__ == "__main__":
    unittest.main()
