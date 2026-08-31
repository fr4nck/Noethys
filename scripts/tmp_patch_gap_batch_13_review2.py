from pathlib import Path

render = Path('noethys/Ctrl/CTRL_Grille_renderers.py')
text = render.read_text(encoding='utf-8')
old = '''    def DrawTexte(self, gc, rectBarre, texte="07h30", couleur=(0, 0, 0), position="gauche"):\n        largeurTexte, hauteurTexte = gc.GetTextExtent(texte)\n        if (largeurTexte*2.5) > rectBarre.width :\n            return 0, 0, 0, 0\n        gc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL), couleur)\n        if position == "gauche" :\n            x = rectBarre.x + 3\n        elif position == "droite" :\n            x = rectBarre.width + rectBarre.x - largeurTexte - 3\n        else :\n            raise ValueError("Position de texte inconnue : %s" % position)\n'''
new = '''    def DrawTexte(self, gc, rectBarre, texte="07h30", couleur=(0, 0, 0), position="gauche"):\n        if position not in ("gauche", "droite") :\n            raise ValueError("Position de texte inconnue : %s" % position)\n        largeurTexte, hauteurTexte = gc.GetTextExtent(texte)\n        if (largeurTexte*2.5) > rectBarre.width :\n            return 0, 0, 0, 0\n        gc.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL), couleur)\n        if position == "gauche" :\n            x = rectBarre.x + 3\n        else :\n            x = rectBarre.width + rectBarre.x - largeurTexte - 3\n'''
if old not in text:
    raise SystemExit('DrawTexte block not found')
render.write_text(text.replace(old, new), encoding='utf-8')

test = Path('tests/test_small_ui_branch_contracts_batch_13.py')
t = test.read_text(encoding='utf-8')
t = t.replace("        self.assertIn('elif position == \"droite\"', source)\n", "        self.assertIn('if position not in (\"gauche\", \"droite\")', source)\n        self.assertIn('else :', source)\n")
needle = '''    def test_render_defaults_are_neutral(self):\n'''
insert = '''    def test_invalid_text_position_is_checked_before_width_shortcut(self):\n        source = (NOETHYS / "Ctrl/CTRL_Grille_renderers.py").read_text(encoding="utf-8")\n        tree = ast.parse(source)\n        draw = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "DrawTexte")\n        first_if = next(node for node in draw.body if isinstance(node, ast.If))\n        self.assertIn("position", ast.unparse(first_if.test))\n        self.assertTrue(any(isinstance(node, ast.Raise) for node in ast.walk(first_if)))\n\n'''
if insert not in t:
    t = t.replace(needle, insert + needle)
test.write_text(t, encoding='utf-8')
