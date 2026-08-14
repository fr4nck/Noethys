#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPLACEMENTS = {
    "noethys/Dlg/DLG_Export_helios.py": [
        ('f = open(cheminFichier, "w")\n        f.write(texte.encode("utf8"))\n        f.close()', 'with open(cheminFichier, "w", encoding="utf-8") as f:\n            f.write(texte)'),
    ],
    "noethys/Dlg/DLG_Envoi_sms.py": [
        ("fichier = open(cheminFichier, 'w')\n            fichier.write(texte.encode(\"utf8\"))\n            fichier.close()", "with open(cheminFichier, 'w', encoding='utf-8') as fichier:\n                fichier.write(texte)"),
    ],
    "noethys/Dlg/DLG_Saisie_prelevement_lot.py": [
        ('f = open(cheminFichier, "w")\n        f.write(texte.encode("utf8"))\n        f.close()', 'with open(cheminFichier, "w", encoding="utf-8") as f:\n            f.write(texte)'),
    ],
    "noethys/Ol/OL_Destinataires_emails.py": [
        ('f = open(cheminFichier, "w")\n        f.write(texte.encode("utf8"))\n        f.close()', 'with open(cheminFichier, "w", encoding="utf-8") as f:\n            f.write(texte)'),
    ],
    "noethys/Utils/UTILS_Internet.py": [
        ('f = open("temp\\calendrier.txt", "w")\n    f.write(texteFichier.encode("utf8"))\n    f.close()', 'with open("temp\\calendrier.txt", "w", encoding="utf-8") as f:\n        f.write(texteFichier)'),
        ('f = open("temp\\identites.txt", "w")\n    f.write(texteFichier.encode("utf8"))\n    f.close()', 'with open("temp\\identites.txt", "w", encoding="utf-8") as f:\n        f.write(texteFichier)'),
    ],
    "noethys/Ctrl/CTRL_Portail_serveur.py": [
        ('file_log = open(UTILS_Fichiers.GetRepUtilisateur(CUSTOMIZE.GetValeur("connecthys_log", "file_name", "connecthys_synchro.log")), "a")', 'file_log = open(UTILS_Fichiers.GetRepUtilisateur(CUSTOMIZE.GetValeur("connecthys_log", "file_name", "connecthys_synchro.log")), "a", encoding="utf-8")'),
        ("file_log.write(six.text_type(texte).encode('UTF-8'))", "file_log.write(six.text_type(texte))"),
    ],
    "noethys/Utils/UTILS_Sauvegarde.py": [
        ("fichierZip.write(fichierSave.encode('utf8'), u\"%s.sql\" % nomFichier)", 'fichierZip.write(fichierSave, u"%s.sql" % nomFichier)'),
    ],
}

changed = 0
for rel, replacements in REPLACEMENTS.items():
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in replacements:
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"corrigé: {rel}")
        changed += 1
    else:
        print(f"inchangé: {rel}")

print(f"{changed} fichier(s) modifié(s)")
