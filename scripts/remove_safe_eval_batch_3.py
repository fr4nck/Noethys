#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# CTRL_Profil.py : paramètres non texte sérialisés par str()
path = ROOT / "noethys/Ctrl/CTRL_Profil.py"
text = path.read_text(encoding="utf-8")
if "import ast\n" not in text:
    marker = "import six\n"
    if marker not in text:
        raise SystemExit("point d'insertion ast absent dans CTRL_Profil.py")
    text = text.replace(marker, marker + "import ast\n", 1)
old = "parametre = eval(six.text_type(parametre))"
if old not in text:
    raise SystemExit("eval profil absent")
text = text.replace(old, "parametre = ast.literal_eval(six.text_type(parametre))", 1)
path.write_text(text, encoding="utf-8")
print("CTRL_Profil.py: eval remplacé")

# CTRL_Composition.py : constructeurs d'onglets codés en dur
path = ROOT / "noethys/Ctrl/CTRL_Composition.py"
text = path.read_text(encoding="utf-8")
old_pages = '''        self.listePages = [\n            (_(u"graphique"), _(u"  Graphique  "), u"CTRL_Graphique(self, IDfamille=IDfamille)", None),\n            (_(u"liste"), _(u"  Liste  "), u"CTRL_Liste(self, IDfamille=IDfamille)", None),'''
new_pages = '''        self.listePages = [\n            (_(u"graphique"), _(u"  Graphique  "), lambda: CTRL_Graphique(self, IDfamille=IDfamille), None),\n            (_(u"liste"), _(u"  Liste  "), lambda: CTRL_Liste(self, IDfamille=IDfamille), None),'''
if old_pages not in text:
    raise SystemExit("listePages composition absente")
text = text.replace(old_pages, new_pages, 1)
old = 'setattr(self, "page%s" % index, eval(ctrlPage))'
if old not in text:
    raise SystemExit("eval composition absent")
text = text.replace(old, 'setattr(self, "page%s" % index, ctrlPage())', 1)
path.write_text(text, encoding="utf-8")
print("CTRL_Composition.py: eval supprimé")
