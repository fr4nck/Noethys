#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "noethys" / "FonctionsPerso.py"
text = path.read_text(encoding="utf-8")
original = text

replacements = [
    ("sqlite3.connect(nomFichier.encode('utf-8'))", "sqlite3.connect(nomFichier)"),
    ("open(rep + \"/\" + nomFichier, 'r')", "open(rep + \"/\" + nomFichier, 'r', encoding=\"utf-8\")"),
    ("open(nomFichier, 'r')", "open(nomFichier, 'r', encoding=\"utf-8\")"),
    ("open(\"New/%s\" % nomFichier, 'w')", "open(\"New/%s\" % nomFichier, 'w', encoding=\"utf-8\")"),
    ("open(os.path.join(repertoire, nomFichier), \"r\")", "open(os.path.join(repertoire, nomFichier), \"r\", encoding=\"utf-8\")"),
    ("open(os.path.join(repertoire, \"New\", nomFichier), \"w\")", "open(os.path.join(repertoire, \"New\", nomFichier), \"w\", encoding=\"utf-8\")"),
    ("open(UTILS_Fichiers.GetRepTemp(fichier=\"resultats.txt\"), 'w')", "open(UTILS_Fichiers.GetRepTemp(fichier=\"resultats.txt\"), 'w', encoding=\"utf-8\")"),
]

for old, new in replacements:
    text = text.replace(old, new)

if text == original:
    print("Aucun changement")
else:
    path.write_text(text, encoding="utf-8")
    print("FonctionsPerso.py modernisé")
