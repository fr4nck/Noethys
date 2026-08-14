#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
replacements = {
    "noethys/Dlg/DLG_Export_compta.py": [
        ('''        if six.PY2:\n            f = open(cheminFichier, "w")\n            texte = texte.encode("utf8")\n        else:\n            f = codecs.open(cheminFichier, encoding='utf-8', mode='w')''',
         '''        f = open(cheminFichier, "w", encoding="utf-8")'''),
    ],
    "noethys/Dlg/DLG_Saisie_prelevement_lot.py": [
        ('''        if six.PY2:\n            flag = "w"\n        else:\n            flag = "wb"\n        f = open(cheminFichier, flag)''',
         '''        f = open(cheminFichier, "wb")'''),
    ],
}
changed = 0
for rel, pairs in replacements.items():
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in pairs:
        if old not in text:
            print(f"motif absent: {rel}")
            continue
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"corrigé: {rel}")
        changed += 1
print(f"{changed} fichier(s) modifié(s)")
