#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

replacements = {
    "noethys/Dlg/DLG_Traduction_importer.py": [
        ('open(cheminFichier, "w")', 'open(cheminFichier, "w", encoding="utf-8")'),
        ('open(fichier_original, "r")', 'open(fichier_original, "r", encoding="utf-8")'),
        ('open(fichier_traduction, "r")', 'open(fichier_traduction, "r", encoding="utf-8")'),
    ],
    "noethys/Utils/UTILS_Json.py": [
        ('with open(nom_fichier) as json_file:', 'with open(nom_fichier, encoding="utf-8") as json_file:'),
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
    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"corrigé: {rel}")
        changed += 1

print(f"{changed} fichier(s) modifié(s)")
