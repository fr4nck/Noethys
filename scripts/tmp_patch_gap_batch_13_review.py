from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace(path, old, new):
    file = ROOT / path
    text = file.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Pattern absent: {path}")
    file.write_text(text.replace(old, new, 1), encoding="utf-8")

replace(
    "noethys/Ctrl/CTRL_Evenements.py",
    '''        conditionPeriode = ""\n        if self.periode != None :\n            if self.periode[0] == "periode" :\n                conditionPeriode = "AND date>='%s' AND date<='%s' " % (self.periode[1][0], self.periode[1][1])\n            if self.periode[0] == "dates" :\n                listeDates = [str(date) for date in self.periode[1]]\n                if len(listeDates) == 0: conditionPeriode = "AND date=''"\n                elif len(listeDates) == 1: conditionPeriode = "AND date='%s'" % listeDates[0]\n                else: conditionPeriode = "AND date IN %s" % str(tuple(listeDates))\n''',
    '''        if self.periode == None :\n            conditionPeriode = ""\n        elif self.periode[0] == "periode" :\n            conditionPeriode = "AND date>='%s' AND date<='%s' " % (self.periode[1][0], self.periode[1][1])\n        elif self.periode[0] == "dates" :\n            listeDates = [str(date) for date in self.periode[1]]\n            if len(listeDates) == 0: conditionPeriode = "AND date=''"\n            elif len(listeDates) == 1: conditionPeriode = "AND date='%s'" % listeDates[0]\n            else: conditionPeriode = "AND date IN %s" % str(tuple(listeDates))\n        else :\n            raise ValueError("Type de période inconnu : %s" % self.periode[0])\n'''
)

replace(
    "noethys/Ctrl/CTRL_Grille_renderers.py",
    '''        gc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL), couleur)\n        x = rectBarre.x + 3\n        if position == "gauche" : x = rectBarre.x + 3\n        if position == "droite" : x = rectBarre.width + rectBarre.x - largeurTexte - 3\n''',
    '''        gc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL), couleur)\n        if position == "gauche" :\n            x = rectBarre.x + 3\n        elif position == "droite" :\n            x = rectBarre.width + rectBarre.x - largeurTexte - 3\n        else :\n            raise ValueError("Position de texte inconnue : %s" % position)\n'''
)

path = ROOT / "tests/test_small_ui_branch_contracts_batch_13.py"
text = path.read_text(encoding="utf-8")
old = '''    def test_event_period_defaults_to_no_filter(self):\n        source = (NOETHYS / "Ctrl/CTRL_Evenements.py").read_text(encoding="utf-8")\n        self.assertIn('conditionPeriode = ""', source)\n        self.assertIn('WHERE evenements.IDactivite IN %s %s', source)\n\n    def test_render_defaults_are_neutral(self):\n'''
new = '''    def test_event_period_contract_is_explicit(self):\n        source = (NOETHYS / "Ctrl/CTRL_Evenements.py").read_text(encoding="utf-8")\n        self.assertIn('if self.periode == None', source)\n        self.assertIn('conditionPeriode = ""', source)\n        self.assertIn('raise ValueError("Type de période inconnu', source)\n        self.assertIn('WHERE evenements.IDactivite IN %s %s', source)\n\n    def test_text_position_contract_is_explicit(self):\n        source = (NOETHYS / "Ctrl/CTRL_Grille_renderers.py").read_text(encoding="utf-8")\n        self.assertIn('if position == "gauche"', source)\n        self.assertIn('elif position == "droite"', source)\n        self.assertIn('raise ValueError("Position de texte inconnue', source)\n\n    def test_render_defaults_are_neutral(self):\n'''
if old not in text:
    raise SystemExit("Pattern absent: tests/test_small_ui_branch_contracts_batch_13.py")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
