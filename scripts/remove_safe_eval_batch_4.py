#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "noethys/Dlg/DLG_Badgeage_importation.py",
    ROOT / "noethys/Dlg/DLG_Synchronisation.py",
]

for path in FILES:
    text = path.read_text(encoding="utf-8")
    if path.name == "DLG_Badgeage_importation.py":
        replacements = {
            '_(u"Page_scanner(self)")': 'lambda: Page_scanner(self)',
            '_(u"Page_excel(self)")': 'lambda: Page_excel(self)',
            '_(u"Page_csv(self)")': 'lambda: Page_csv(self)',
            '_(u"Page_archives(self)")': 'lambda: Page_archives(self)',
        }
    else:
        replacements = {
            '_(u"Page_serveur(self)")': 'lambda: Page_serveur(self)',
            '_(u"Page_ftp(self)")': 'lambda: Page_ftp(self)',
            '_(u"Page_cryptage(self)")': 'lambda: Page_cryptage(self)',
            '_(u"Page_archivage(self)")': 'lambda: Page_archivage(self)',
        }
    for old, new in replacements.items():
        if old not in text:
            raise SystemExit(f"constructeur absent dans {path.name}: {old}")
        text = text.replace(old, new, 1)
    old = 'setattr(self, "page%s" % index, eval(ctrlPage))'
    if old not in text:
        raise SystemExit(f"eval absent dans {path.name}")
    text = text.replace(old, 'setattr(self, "page%s" % index, ctrlPage())', 1)
    path.write_text(text, encoding="utf-8")
    print(f"{path.name}: eval supprimé")
