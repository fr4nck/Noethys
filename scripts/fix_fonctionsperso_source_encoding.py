#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "noethys/FonctionsPerso.py"
text = path.read_text(encoding="utf-8")
replacements = [
    ('fichier = open(nomFichier, "r")', 'fichier = open(nomFichier, "r", encoding="utf-8")'),
    ('nouveauFichier = open("New/%s" % nomFichier, "w")', 'nouveauFichier = open("New/%s" % nomFichier, "w", encoding="utf-8")'),
]
for old, new in replacements:
    count = text.count(old)
    if count == 0:
        raise SystemExit(f"motif absent: {old}")
    text = text.replace(old, new)
    print(f"{old!r}: {count} remplacement(s)")
path.write_text(text, encoding="utf-8")
