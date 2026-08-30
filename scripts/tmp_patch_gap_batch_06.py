from pathlib import Path


def replace(path, old, new):
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit("bloc introuvable: %s" % path)
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


vaccine = Path("noethys/Dlg/DLG_Saisie_typesVaccins.py")
replace(
    vaccine,
    '    def SetValidite(self, validite=None):\n        if validite != None :\n',
    '    def SetValidite(self, validite=None):\n        jours = 0\n        mois = 0\n        annees = 0\n        if validite != None :\n',
)

replace(
    Path("noethys/Dlg/DLG_Envoi_sms.py"),
    '    if "gauche" in alignement:\n        xRond = 1\n    if "droite" in alignement:\n        xRond = largeurImage - largeurRond - 1\n    if "haut" in alignement:\n        yRond = 1\n    if "bas" in alignement:\n        yRond = hauteurImage - hauteurRond - 1\n',
    '    if "gauche" in alignement:\n        xRond = 1\n    elif "droite" in alignement:\n        xRond = largeurImage - largeurRond - 1\n    else:\n        raise ValueError("Alignement horizontal non supporte : %s" % alignement)\n    if "haut" in alignement:\n        yRond = 1\n    elif "bas" in alignement:\n        yRond = hauteurImage - hauteurRond - 1\n    else:\n        raise ValueError("Alignement vertical non supporte : %s" % alignement)\n',
)

replace(
    Path("noethys/Dlg/DLG_Selection_mails.py"),
    '    if "gauche" in alignement : xRond = 1\n    if "droite" in alignement : xRond = largeurImage - largeurRond - 1\n    if "haut" in alignement : yRond = 1\n    if "bas" in alignement : yRond = hauteurImage - hauteurRond - 1\n',
    '    if "gauche" in alignement :\n        xRond = 1\n    elif "droite" in alignement :\n        xRond = largeurImage - largeurRond - 1\n    else:\n        raise ValueError("Alignement horizontal non supporte : %s" % alignement)\n    if "haut" in alignement :\n        yRond = 1\n    elif "bas" in alignement :\n        yRond = hauteurImage - hauteurRond - 1\n    else:\n        raise ValueError("Alignement vertical non supporte : %s" % alignement)\n',
)

test = '''import ast\nimport pathlib\nimport unittest\n\nfrom scripts import audit_branch_assignment_gaps\n\nROOT = pathlib.Path(__file__).resolve().parents[1]\nSOURCE_ROOT = ROOT / "noethys"\nSOURCES = (\n    SOURCE_ROOT / "Dlg" / "DLG_Saisie_typesVaccins.py",\n    SOURCE_ROOT / "Dlg" / "DLG_Envoi_sms.py",\n    SOURCE_ROOT / "Dlg" / "DLG_Selection_mails.py",\n)\n\nclass SmallUiBranchContractsTests(unittest.TestCase):\n    def test_targeted_gaps_are_gone(self):\n        names = {"jours", "mois", "annees", "xRond", "yRond"}\n        targeted = []\n        for source in SOURCES:\n            targeted.extend(item for item in audit_branch_assignment_gaps.scan_file(source, SOURCE_ROOT) if item["name"] in names and item["function"] in {"SetValidite", "AjouteTexteImage"})\n        self.assertEqual(targeted, [], targeted)\n\n    def test_modules_parse(self):\n        for source in SOURCES:\n            ast.parse(source.read_text(encoding="utf-8"), filename=str(source))\n\n    def test_vaccine_defaults_are_explicit(self):\n        text = SOURCES[0].read_text(encoding="utf-8")\n        self.assertIn("jours = 0\\n        mois = 0\\n        annees = 0", text)\n\n    def test_alignment_helpers_reject_incomplete_alignment(self):\n        for source in SOURCES[1:]:\n            tree = ast.parse(source.read_text(encoding="utf-8"))\n            helper = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "AjouteTexteImage")\n            self.assertGreaterEqual(sum(isinstance(n, ast.Raise) for n in ast.walk(helper)), 2)\n\nif __name__ == "__main__":\n    unittest.main()\n'''
Path("tests/test_small_ui_branch_contracts.py").write_text(test, encoding="utf-8")
