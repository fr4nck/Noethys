#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
replacements = {
    "noethys/Ctrl/CTRL_Bouton_image.py": [
        ('fichier = open(nomFichier, "r")', 'fichier = open(nomFichier, "r", encoding="utf-8")'),
        ('nouveauFichier = open("New/%s" % nomFichier, "w")', 'nouveauFichier = open("New/%s" % nomFichier, "w", encoding="utf-8")'),
    ],
    "noethys/Ol/OL_Traductions.py": [
        ('fichier = open(nomFichier, "r")', 'fichier = open(nomFichier, "r", encoding="utf-8")'),
        ('nouveauFichier = open("New/%s" % nomFichier, "w")', 'nouveauFichier = open("New/%s" % nomFichier, "w", encoding="utf-8")'),
        ('fichier = open("New/" + nomFichier, "r")', 'fichier = open("New/" + nomFichier, "r", encoding="utf-8")'),
        ('nouveauFichier = open("New/New/%s" % nomFichier, "w")', 'nouveauFichier = open("New/New/%s" % nomFichier, "w", encoding="utf-8")'),
    ],
    "noethys/Noethys.py": [
        ('self.filename = open(nomJournal, "a")', 'self.filename = open(nomJournal, "a", encoding="utf-8")'),
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
            print(f"motif absent: {rel}: {old}")
    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"corrigé: {rel}")
        changed += 1
print(f"{changed} fichier(s) modifié(s)")
