from pathlib import Path

path = Path('noethys/Utils/UTILS_Archivage.py')
text = path.read_text(encoding='utf-8')
old = '''    def Effacer_individus(self, liste_individus=None):
        """ Effacer les individus """
        if liste_individus == None :
'''
new = '''    def Effacer_individus(self, liste_individus=None):
        """ Effacer les individus """
        dlgAttente = None
        if liste_individus == None :
'''
if old not in text:
    raise SystemExit('function start not found')
text = text.replace(old, new, 1)
old = '''        # Fin de procédure
        if self.liste_individus != []:
            # Détruit dlgAttente
            del dlgAttente

            # Succès
'''
new = '''        # Fin de procédure
        if self.liste_individus != []:
            # Détruit dlgAttente uniquement si cette méthode l'a créé
            if dlgAttente != None:
                del dlgAttente

            # Succès
'''
if old not in text:
    raise SystemExit('cleanup block not found')
path.write_text(text.replace(old, new, 1), encoding='utf-8')

test = Path('tests/test_branch_contracts_batch_17.py')
test.write_text('''import importlib.util\nimport unittest\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nNOETHYS = ROOT / "noethys"\nAUDIT = ROOT / "scripts" / "audit_branch_assignment_gaps.py"\nspec = importlib.util.spec_from_file_location("audit_branch_assignment_gaps", AUDIT)\naudit = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(audit)\n\nTARGET = ("Utils/UTILS_Archivage.py", "Effacer_individus", "dlgAttente")\n\nclass TestBatch17Archivage(unittest.TestCase):\n    def test_targeted_finding_disappears(self):\n        path = NOETHYS / "Utils/UTILS_Archivage.py"\n        remaining = {\n            (item["file"], item["function"], item["name"])\n            for item in audit.scan_file(path, NOETHYS)\n            if (item["file"], item["function"], item["name"]) == TARGET\n        }\n        self.assertEqual(remaining, set())\n\n    def test_busy_info_is_optional_for_explicit_individual_list(self):\n        source = (NOETHYS / "Utils/UTILS_Archivage.py").read_text(encoding="utf-8")\n        self.assertIn("dlgAttente = None", source)\n        self.assertIn("if dlgAttente != None:", source)\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding='utf-8')
