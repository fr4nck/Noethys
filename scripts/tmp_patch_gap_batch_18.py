from pathlib import Path

source_path = Path('noethys/Ctrl/CTRL_Questionnaire.py')
text = source_path.read_text(encoding='utf-8')
old = '''                        # CTRL du type de calcul\n                        if track.controle == "ligne_texte" : ctrl = CTRL_ligne_texte(self.GetMainWindow(), item=brancheQuestion, track=track) # size=(largeurControle, -1) )\n'''
new = '''                        # CTRL du type de calcul\n                        ctrl = None\n                        if track.controle == "ligne_texte" : ctrl = CTRL_ligne_texte(self.GetMainWindow(), item=brancheQuestion, track=track) # size=(largeurControle, -1) )\n'''
if old not in text:
    raise SystemExit('anchor 1 not found')
text = text.replace(old, new, 1)
old2 = '''                        if track.controle == "rfid" : ctrl = CTRL_rfid(self.GetMainWindow(), item=brancheQuestion, track=track) # size=(largeurControle, 20) )\n\n                        if track.controle != None :\n                            self.SetItemWindow(brancheQuestion, ctrl, 1)\n                            track.ctrl = ctrl\n'''
new2 = '''                        if track.controle == "rfid" : ctrl = CTRL_rfid(self.GetMainWindow(), item=brancheQuestion, track=track) # size=(largeurControle, 20) )\n\n                        if track.controle != None :\n                            if ctrl == None :\n                                raise ValueError("Type de contrôle de questionnaire inconnu : %s" % track.controle)\n                            self.SetItemWindow(brancheQuestion, ctrl, 1)\n                            track.ctrl = ctrl\n'''
if old2 not in text:
    raise SystemExit('anchor 2 not found')
text = text.replace(old2, new2, 1)
source_path.write_text(text, encoding='utf-8')

test_path = Path('tests/test_branch_contracts_batch_18.py')
test_path.write_text('''import importlib.util\nimport unittest\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nNOETHYS = ROOT / "noethys"\nAUDIT = ROOT / "scripts" / "audit_branch_assignment_gaps.py"\nspec = importlib.util.spec_from_file_location("audit_branch_assignment_gaps", AUDIT)\naudit = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(audit)\n\nTARGET = ("Ctrl/CTRL_Questionnaire.py", "Remplissage", "ctrl")\n\nclass TestBatch18Questionnaire(unittest.TestCase):\n    def test_targeted_finding_disappears(self):\n        path = NOETHYS / "Ctrl/CTRL_Questionnaire.py"\n        remaining = [\n            (item["file"], item["function"], item["name"])\n            for item in audit.scan_file(path, NOETHYS)\n            if (item["file"], item["function"], item["name"]) == TARGET\n        ]\n        self.assertEqual(remaining, [])\n\n    def test_unknown_non_null_control_is_rejected_explicitly(self):\n        source = (NOETHYS / "Ctrl/CTRL_Questionnaire.py").read_text(encoding="utf-8")\n        self.assertIn("ctrl = None", source)\n        self.assertIn("if ctrl == None :", source)\n        self.assertIn("Type de contrôle de questionnaire inconnu", source)\n\nif __name__ == "__main__":\n    unittest.main()\n''', encoding='utf-8')
