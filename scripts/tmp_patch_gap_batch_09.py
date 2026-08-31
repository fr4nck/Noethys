from pathlib import Path

files = [
    Path('noethys/Ol/OL_PES_pieces.py'),
    Path('noethys/Ol/OL_Prelevements.py'),
    Path('noethys/Ol/OL_Prelevements_national.py'),
    Path('noethys/Ol/OL_Prelevements_sepa.py'),
]

for path in files:
    text = path.read_text(encoding='utf-8')
    old = '''                if dictDetail["nbre"] == 1 :\n                    if key == "attente" : label = _(u"en attente")\n                    if key == "valide" : label = _(u"validé")\n                    if key == "refus" : label = _(u"refusé")\n                    if key == "regle" : label = _(u"réglé")\n                    if key == "pasregle" : label = _(u"non réglé")\n                else :\n                    if key == "attente" : label = _(u"en attente")\n                    if key == "valide" : label = _(u"validés")\n                    if key == "refus" : label = _(u"refusés")\n                    if key == "regle" : label = _(u"réglés")\n                    if key == "pasregle" : label = _(u"non réglés")\n'''
    new = '''                if dictDetail["nbre"] == 1 :\n                    dictLabels = {\n                        "attente" : _(u"en attente"),\n                        "valide" : _(u"validé"),\n                        "refus" : _(u"refusé"),\n                        "regle" : _(u"réglé"),\n                        "pasregle" : _(u"non réglé"),\n                    }\n                else :\n                    dictLabels = {\n                        "attente" : _(u"en attente"),\n                        "valide" : _(u"validés"),\n                        "refus" : _(u"refusés"),\n                        "regle" : _(u"réglés"),\n                        "pasregle" : _(u"non réglés"),\n                    }\n                label = dictLabels[key]\n'''
    assert old in text, path
    path.write_text(text.replace(old, new, 1), encoding='utf-8')

path = Path('noethys/Ol/OL_Types_vaccins.py')
text = path.read_text(encoding='utf-8')
old = '''    if nbreItems == 0:\n        resultat = _(u"Validité illimitée")\n    else:\n        if nbreItems == 1:\n            resultat = listItems[0]\n        if nbreItems == 2:\n            resultat = listItems[0] + " et " + listItems[1]\n        if nbreItems == 3:\n            resultat = listItems[0] + ", " + listItems[1] + " et " + listItems[2]\n'''
new = '''    if nbreItems == 0:\n        resultat = _(u"Validité illimitée")\n    elif nbreItems == 1:\n        resultat = listItems[0]\n    elif nbreItems == 2:\n        resultat = listItems[0] + " et " + listItems[1]\n    else :\n        resultat = listItems[0] + ", " + listItems[1] + " et " + listItems[2]\n'''
assert old in text
path.write_text(text.replace(old, new, 1), encoding='utf-8')

Path('tests/test_ol_label_branch_contracts.py').write_text(r'''import ast
import unittest
from pathlib import Path

from scripts import audit_branch_assignment_gaps

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "noethys"
LABEL_FILES = [
    SOURCE_ROOT / "Ol" / "OL_PES_pieces.py",
    SOURCE_ROOT / "Ol" / "OL_Prelevements.py",
    SOURCE_ROOT / "Ol" / "OL_Prelevements_national.py",
    SOURCE_ROOT / "Ol" / "OL_Prelevements_sepa.py",
]
VACCINS = SOURCE_ROOT / "Ol" / "OL_Types_vaccins.py"


class OlLabelBranchContractTests(unittest.TestCase):
    def test_targeted_label_gaps_are_gone(self):
        leftovers = []
        for source in LABEL_FILES:
            for item in audit_branch_assignment_gaps.scan_file(source, SOURCE_ROOT):
                if item.get("function") == "GetTexteTotaux" and item.get("name") == "label":
                    leftovers.append(item)
        for item in audit_branch_assignment_gaps.scan_file(VACCINS, SOURCE_ROOT):
            if item.get("function") == "FormatDuree" and item.get("name") == "resultat":
                leftovers.append(item)
        self.assertEqual(leftovers, [], leftovers)

    def test_total_label_domains_stay_complete(self):
        expected = {"attente", "valide", "refus", "regle", "pasregle"}
        for source in LABEL_FILES:
            tree = ast.parse(source.read_text(encoding="utf-8"))
            func = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "GetTexteTotaux")
            key_sets = []
            for node in ast.walk(func):
                if isinstance(node, ast.Dict):
                    keys = {k.value for k in node.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)}
                    if expected <= keys:
                        key_sets.append(keys)
            self.assertGreaterEqual(len(key_sets), 2, source)

    def test_format_duree_keeps_all_four_output_shapes(self):
        tree = ast.parse(VACCINS.read_text(encoding="utf-8"))
        func = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "FormatDuree")
        source = ast.get_source_segment(VACCINS.read_text(encoding="utf-8"), func)
        namespace = {"_": lambda value: value}
        exec(source, namespace)
        format_duree = namespace["FormatDuree"]
        self.assertEqual(format_duree("j0-m0-a0"), "Validité illimitée")
        self.assertEqual(format_duree("j1-m0-a0"), "1 jour")
        self.assertEqual(format_duree("j1-m1-a0"), "1 jour et 1 mois")
        self.assertEqual(format_duree("j1-m1-a1"), "1 jour, 1 mois et 1 année")


if __name__ == "__main__":
    unittest.main()
''', encoding='utf-8')
