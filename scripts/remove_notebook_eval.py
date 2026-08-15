#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "noethys/Dlg/DLG_Famille.py",
    ROOT / "noethys/Dlg/DLG_Individu.py",
]

pattern = re.compile(r', u"(DLG_[^"]+)"(?=, ")')

for path in FILES:
    text = path.read_text(encoding="utf-8")
    start = text.index("self.listePages = [")
    end = text.index("            ]", start) + len("            ]")
    block = text[start:end]
    new_block, count = pattern.subn(r", lambda: \1", block)
    if count == 0:
        raise SystemExit(f"aucun constructeur converti dans {path}")
    text = text[:start] + new_block + text[end:]
    old = 'setattr(self, "page%s" % index, eval(ctrlPage))'
    new = 'setattr(self, "page%s" % index, ctrlPage())'
    if old not in text:
        raise SystemExit(f"appel eval absent dans {path}")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print(f"{path.name}: {count} constructeur(s) converti(s)")
