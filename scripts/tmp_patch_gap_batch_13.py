from pathlib import Path

replacements = {
    Path('noethys/Ctrl/CTRL_Evenements.py'): [
        (
            '        if self.periode != None :\n',
            '        conditionPeriode = ""\n        if self.periode != None :\n',
        ),
        (
            '        else :\n            conditionPeriode = ""\n\n        DB = GestionDB.DB()\n',
            '        DB = GestionDB.DB()\n',
        ),
    ],
    Path('noethys/Ctrl/CTRL_Grille_renderers.py'): [
        (
            '        gc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL), couleur)\n        if position == "gauche" : x = rectBarre.x + 3\n',
            '        gc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL), couleur)\n        x = rectBarre.x + 3\n        if position == "gauche" : x = rectBarre.x + 3\n',
        ),
        (
            '        marge = 2\n        if len(self.case.liste_evenements) :\n            largeur_bouton = (1.0 * (rectCase.width - marge -1) / nbre_evenements) - marge*2\n',
            '        marge = 2\n        largeur_bouton = 0\n        if len(self.case.liste_evenements) :\n            largeur_bouton = (1.0 * (rectCase.width - marge -1) / nbre_evenements) - marge*2\n',
        ),
    ],
    Path('noethys/Ctrl/CTRL_Informations.py'): [
        (
            '                label = u"?"\n                for ID, label in Renseignements.LISTE_TYPES_RENSEIGNEMENTS :\n',
            '                labelRenseignement = u"?"\n                for ID, label in Renseignements.LISTE_TYPES_RENSEIGNEMENTS :\n',
        ),
    ],
    Path('noethys/Ctrl/CTRL_Remplissage.py'): [
        (
            '        # Dessin de la case\n        self.renderer = RendererCaseActivite(self)\n        if self.IDactivite != None :\n',
            '        # Dessin de la case\n        self.renderer = RendererCaseActivite(self)\n        labelActivite = u""\n        if self.IDactivite != None :\n',
        ),
        (
            '        marge = 2\n        if len(self.case.liste_evenements) :\n            largeur_bouton = (1.0 * (rectCase.width - marge -1) / nbre_evenements) - marge*2\n',
            '        marge = 2\n        largeur_bouton = 0\n        if len(self.case.liste_evenements) :\n            largeur_bouton = (1.0 * (rectCase.width - marge -1) / nbre_evenements) - marge*2\n',
        ),
    ],
}

for path, items in replacements.items():
    text = path.read_text(encoding='utf-8')
    for old, new in items:
        if old not in text:
            raise SystemExit('Pattern not found in %s: %r' % (path, old[:80]))
        text = text.replace(old, new, 1)
    path.write_text(text, encoding='utf-8')

Path('tests/test_small_ui_branch_contracts_batch_13.py').write_text(r'''import ast
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
AUDIT = ROOT / "scripts" / "audit_branch_assignment_gaps.py"
spec = importlib.util.spec_from_file_location("audit_branch_assignment_gaps", AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

TARGETS = {
    ("Ctrl/CTRL_Evenements.py", "Importation", "conditionPeriode"),
    ("Ctrl/CTRL_Grille_renderers.py", "DrawTexte", "x"),
    ("Ctrl/CTRL_Grille_renderers.py", "Draw", "largeur_bouton"),
    ("Ctrl/CTRL_Informations.py", "Branches_renseignements", "labelRenseignement"),
    ("Ctrl/CTRL_Remplissage.py", "__init__", "labelActivite"),
    ("Ctrl/CTRL_Remplissage.py", "Draw", "largeur_bouton"),
}

class TestBatch13Contracts(unittest.TestCase):
    def test_targeted_findings_disappear(self):
        remaining = set()
        for relpath, function, name in TARGETS:
            path = NOETHYS / relpath
            for item in audit.scan_file(path, NOETHYS):
                key = (item["file"], item["function"], item["name"])
                if key in TARGETS:
                    remaining.add(key)
        self.assertEqual(remaining, set())

    def test_event_period_defaults_to_no_filter(self):
        source = (NOETHYS / "Ctrl/CTRL_Evenements.py").read_text(encoding="utf-8")
        self.assertIn('conditionPeriode = ""', source)
        self.assertIn('WHERE evenements.IDactivite IN %s %s', source)

    def test_render_defaults_are_neutral(self):
        source = (NOETHYS / "Ctrl/CTRL_Grille_renderers.py").read_text(encoding="utf-8")
        self.assertIn('largeur_bouton = 0', source)
        source2 = (NOETHYS / "Ctrl/CTRL_Remplissage.py").read_text(encoding="utf-8")
        self.assertIn('labelActivite = u""', source2)
        self.assertIn('largeur_bouton = 0', source2)

if __name__ == "__main__":
    unittest.main()
''', encoding='utf-8')
