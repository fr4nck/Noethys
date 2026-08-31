from pathlib import Path

path = Path('noethys/Utils/UTILS_Utilisateurs.py')
text = path.read_text(encoding='utf-8')
old = '''            if mode == "groupes" :
                if len(listeID) == 1 : condition = "IDtype_groupe_activite=%d" % listeID[0]
                if len(listeID) >1 : condition = "IDtype_groupe_activite IN %s" % str(tuple(listeID))
                DB = GestionDB.DB()
                req = """SELECT IDgroupe_activite, activites 
                FROM groupes_activites
                WHERE %s;""" % condition
                DB.ExecuterReq(req)
                listeDonnees = DB.ResultatReq()
                listeActivites = []
                for IDgroupe_activite, IDactivite_temp in listeDonnees :
                    listeActivites.append(IDactivite_temp)
                DB.Close()
                
            if mode == "activites" :
                listeActivites = listeID
'''
new = '''            listeActivites = []
            if mode == "groupes" :
                if len(listeID) == 1 : condition = "IDtype_groupe_activite=%d" % listeID[0]
                elif len(listeID) > 1 : condition = "IDtype_groupe_activite IN %s" % str(tuple(listeID))
                else : condition = None
                if condition != None :
                    DB = GestionDB.DB()
                    req = """SELECT IDgroupe_activite, activites 
                    FROM groupes_activites
                    WHERE %s;""" % condition
                    DB.ExecuterReq(req)
                    listeDonnees = DB.ResultatReq()
                    for IDgroupe_activite, IDactivite_temp in listeDonnees :
                        listeActivites.append(IDactivite_temp)
                    DB.Close()
                
            elif mode == "activites" :
                listeActivites = listeID
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new, 1), encoding='utf-8')

test = Path('tests/test_branch_contracts_batch_16.py')
test.write_text('''import importlib.util\nimport unittest\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nNOETHYS = ROOT / "noethys"\nAUDIT = ROOT / "scripts" / "audit_branch_assignment_gaps.py"\nspec = importlib.util.spec_from_file_location("audit_branch_assignment_gaps", AUDIT)\naudit = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(audit)\n\nTARGETS = {\n    ("Utils/UTILS_Utilisateurs.py", "VerificationDroits", "condition"),\n    ("Utils/UTILS_Utilisateurs.py", "VerificationDroits", "listeActivites"),\n}\n\nclass TestBatch16Permissions(unittest.TestCase):\n    def test_targeted_findings_disappear(self):\n        path = NOETHYS / "Utils/UTILS_Utilisateurs.py"\n        remaining = {\n            (item["file"], item["function"], item["name"])\n            for item in audit.scan_file(path, NOETHYS)\n            if (item["file"], item["function"], item["name"]) in TARGETS\n        }\n        self.assertEqual(remaining, set())\n\n    def test_restrictions_fail_closed_for_empty_or_unknown_modes(self):\n        source = (NOETHYS / "Utils/UTILS_Utilisateurs.py").read_text(encoding="utf-8")\n        self.assertIn("listeActivites = []", source)\n        self.assertIn("else : condition = None", source)\n        self.assertIn("if condition != None", source)\n        self.assertIn('elif mode == "activites"', source)\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding='utf-8')
