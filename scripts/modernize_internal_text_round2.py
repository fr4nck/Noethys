#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

replacements = {
    "noethys/Utils/UTILS_Sauvegarde.py": [
        ('fichier = open(nomFichier, "w")', 'fichier = open(nomFichier, "w", encoding="utf-8")'),
    ],
    "noethys/Utils/UTILS_Portail_installation.py": [
        ('fichier = open(os.path.join(source_repertoire, "versions.txt"), "r")', 'fichier = open(os.path.join(source_repertoire, "versions.txt"), "r", encoding="utf-8")'),
    ],
    "noethys/Utils/UTILS_Traduction.py": [
        ('fichier = open(UTILS_Fichiers.GetRepTemp(fichier="Textes.txt"), "w")', 'fichier = open(UTILS_Fichiers.GetRepTemp(fichier="Textes.txt"), "w", encoding="utf-8")'),
    ],
    "noethys/Utils/UTILS_Infos_individus.py": [
        ('fichier = open(nomFichier, "w")\n        fichier.write(chaine)', 'fichier = open(nomFichier, "wb")\n        fichier.write(chaine)'),
        ('fichier = open(nomFichier, "r")\n        chaine = fichier.read()', 'fichier = open(nomFichier, "rb")\n        chaine = fichier.read()'),
    ],
}

changed = 0
for rel, pairs in replacements.items():
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in pairs:
        if old not in text:
            print(f"motif absent dans {rel}: {old!r}")
            continue
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"corrigé: {rel}")
        changed += 1

print(f"{changed} fichier(s) modifié(s)")
