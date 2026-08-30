from pathlib import Path

path = Path('noethys/Ctrl/CTRL_Saisie_transport.py')
text = path.read_text(encoding='utf-8')

old = '''    def Validation(self):\n        if self.rubrique == "depart" : nomTemp = _(u"de départ")\n        if self.rubrique == "arrivee" : nomTemp = _(u"d'arrivée")\n'''
new = '''    def Validation(self):\n        if self.rubrique == "depart" :\n            nomTemp = _(u"de départ")\n        elif self.rubrique == "arrivee" :\n            nomTemp = _(u"d'arrivée")\n        else :\n            raise ValueError("Rubrique de transport inconnue : %r" % self.rubrique)\n'''
assert old in text
text = text.replace(old, new, 1)

old = '''            if type == "CALENDRIER" :\n                date_min = min(parametres["dates"])\n                date_max = max(parametres["dates"])\n            \n            if type == "PLANNING" :\n                date_min = parametres["date_debut"]\n                date_max = parametres["date_fin"]\n            \n            # Récupération des jours de présence sur l'activité donnée\n            if parametres["activite"] != None :\n'''
new = '''            if type == "CALENDRIER" :\n                date_min = min(parametres["dates"])\n                date_max = max(parametres["dates"])\n            elif type == "PLANNING" :\n                date_min = parametres["date_debut"]\n                date_max = parametres["date_fin"]\n            else :\n                raise ValueError("Mode de saisie multiple inconnu : %r" % type)\n            \n            # Récupération des jours de présence sur l'activité donnée\n            listeDatesPresences = []\n            if parametres["activite"] != None :\n'''
assert old in text
text = text.replace(old, new, 1)

old = '''            # Création de la liste de jours initiale\n            if type == "CALENDRIER" :\n                liste_dates = parametres["dates"]\n                \n            if type == "PLANNING" :\n                liste_dates = [date_min,]\n                date = date_min\n                for x in range((date_max - date_min).days) :\n                    date = date + datetime.timedelta(days=1) \n                    liste_dates.append(date)\n'''
new = '''            # Création de la liste de jours initiale\n            if type == "CALENDRIER" :\n                liste_dates = parametres["dates"]\n            else :  # PLANNING, validé ci-dessus\n                liste_dates = [date_min,]\n                date = date_min\n                for x in range((date_max - date_min).days) :\n                    date = date + datetime.timedelta(days=1) \n                    liste_dates.append(date)\n'''
assert old in text
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')

Path('tests/test_saisie_transport_branch_contract.py').write_text(r'''import ast
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
SOURCE = SOURCE_ROOT / "Ctrl" / "CTRL_Saisie_transport.py"


class SaisieTransportBranchContractTests(unittest.TestCase):
    def test_targeted_transport_gaps_are_gone(self):
        findings = audit_branch_assignment_gaps.scan_file(SOURCE, SOURCE_ROOT)
        targeted_names = {"nomTemp", "date_min", "date_max", "liste_dates", "listeDatesPresences"}
        targeted = [
            item for item in findings
            if item.get("function") in {"Validation", "Sauvegarde"}
            and item.get("name") in targeted_names
        ]
        self.assertEqual(targeted, [], targeted)

    def test_validation_rejects_unknown_transport_rubrique(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        validation = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "Validation")
        raises = [node for node in ast.walk(validation) if isinstance(node, ast.Raise)]
        self.assertTrue(raises)

    def test_multiple_mode_has_explicit_unknown_type_contract(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('raise ValueError("Mode de saisie multiple inconnu : %r" % type)', source)


if __name__ == "__main__":
    unittest.main()
''', encoding='utf-8')
