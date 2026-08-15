#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "noethys/Dlg/DLG_Factures_generation.py",
    ROOT / "noethys/Dlg/DLG_Rappels_generation.py",
    ROOT / "noethys/Dlg/DLG_Attestations_fiscales_generation.py",
]

for path in FILES:
    text = path.read_text(encoding="utf-8")

    # Les pages sont déjà importées statiquement sous les noms Page1, Page2, Page3.
    if path.name == "DLG_Attestations_fiscales_generation.py":
        old_pages = 'self.listePages = ("Page1", "Page2")'
        new_pages = 'self.listePages = (Page1, Page2)'
    else:
        old_pages = 'self.listePages = ("Page1", "Page2", "Page3")'
        new_pages = 'self.listePages = (Page1, Page2, Page3)'
    if old_pages not in text:
        raise SystemExit(f"listePages attendue absente: {path}")
    text = text.replace(old_pages, new_pages, 1)

    old_ctor = 'eval(self.listePages[numPage-1] + "(self)")'
    if old_ctor not in text:
        raise SystemExit(f"constructeur eval absent: {path}")
    text = text.replace(old_ctor, 'self.listePages[numPage-1](self)', 1)

    old_access = 'eval("self.page"+str(self.pageVisible))'
    count = text.count(old_access)
    if count != 4:
        raise SystemExit(f"4 accès page eval attendus dans {path}, trouvé {count}")
    text = text.replace(old_access, 'getattr(self, "page%s" % self.pageVisible)')

    path.write_text(text, encoding="utf-8")
    print(f"{path.name}: 5 eval supprimés")
