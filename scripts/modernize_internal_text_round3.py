#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
replacements = {
    "noethys/GestionDB.py": [
        ("open(\"prenoms.txt\", 'r').readlines()", "open(\"prenoms.txt\", 'r', encoding=\"utf-8\").readlines()"),
    ],
    "noethys/Dlg/DLG_Synchronisation_donnees.py": [
        ('fichier = open(nomFichier, "w")', 'fichier = open(nomFichier, "w", encoding="utf-8")'),
    ],
    "noethys/Utils/UTILS_Portail_synchro.py": [
        ('fichier_online = open(os.path.join(resultat[0], resultat[1]), "r")', 'fichier_online = open(os.path.join(resultat[0], resultat[1]), "r", encoding="utf-8")'),
        ('fichier_wsgi = open(os.path.join(resultat[0], resultat[1]), "r")', 'fichier_wsgi = open(os.path.join(resultat[0], resultat[1]), "r", encoding="utf-8")'),
        ("fichier_wsgi = codecs.open(nomFichierComplet, 'w')", "fichier_wsgi = codecs.open(nomFichierComplet, 'w', encoding='utf-8')"),
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
