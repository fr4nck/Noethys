#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
replacements = {
    "noethys/Utils/UTILS_Export.py": [
        ('f = open(cheminFichier, "w")', 'f = open(cheminFichier, "w", encoding="utf-8")'),
    ],
    "noethys/Utils/UTILS_Export_noethysweb.py": [
        ("with open(nom_fichier_json, 'w') as outfile:", "with open(nom_fichier_json, 'w', encoding='utf-8') as outfile:"),
    ],
    "noethys/Utils/UTILS_Export_familles.py": [
        ('        if six.PY2:\n            flag = "w"\n        else:\n            flag = "wb"\n        f = open(nomFichier, flag)', '        f = open(nomFichier, "wb")'),
    ],
}
changed = 0
for rel, pairs in replacements.items():
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in pairs:
        if old in text:
            text = text.replace(old, new)
        else:
            print(f"motif absent: {rel}: {old!r}")
    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"corrigé: {rel}")
        changed += 1
print(f"{changed} fichier(s) modifié(s)")
