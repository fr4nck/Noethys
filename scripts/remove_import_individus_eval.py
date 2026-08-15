#!/usr/bin/env python3
from pathlib import Path

path = Path("noethys/Dlg/DLG_Importation_individus.py")
text = path.read_text(encoding="utf-8")

old_pages = '''        self.listePages = (\n            "Page_intro", \n            "Page_fichier",\n            "Page_colonnes",\n            "Page_analyse",\n            )'''
new_pages = '''        self.listePages = (\n            Page_intro,\n            Page_fichier,\n            Page_colonnes,\n            Page_analyse,\n            )'''
if old_pages not in text:
    raise SystemExit("listePages attendue absente")
text = text.replace(old_pages, new_pages, 1)

old_create = 'setattr(self, "page%s" % numPage, eval(self.listePages[numPage-1] + "(self)"))'
new_create = 'setattr(self, "page%s" % numPage, self.listePages[numPage-1](self))'
if old_create not in text:
    raise SystemExit("eval constructeur absent")
text = text.replace(old_create, new_create, 1)

old_access = 'eval("self.page"+str(self.pageVisible))'
count = text.count(old_access)
if count != 4:
    raise SystemExit(f"4 accès page attendus, trouvé {count}")
text = text.replace(old_access, 'getattr(self, "page%s" % self.pageVisible)')

path.write_text(text, encoding="utf-8")
print("DLG_Importation_individus.py: 5 eval supprimés")
