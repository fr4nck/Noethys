#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
replacements = {
    "noethys/Dlg/DLG_Saisie_lot_tresor_public_corail.py": [
        ('f = open(os.path.join(rep_temp, nom_fichier + ".xml"), "w")',
         'f = open(os.path.join(rep_temp, nom_fichier + ".xml"), "wb")'),
    ],
    "noethys/Utils/UTILS_Corail.py": [
        ('f = open(nomFichier, "w")', 'f = open(nomFichier, "wb")'),
    ],
    "noethys/Utils/UTILS_Jvs.py": [
        ('f = open(nomFichier, "w")', 'f = open(nomFichier, "wb")'),
    ],
    "noethys/Utils/UTILS_Pes.py": [
        ('f = open(nomFichier, "w")', 'f = open(nomFichier, "wb")'),
    ],
    "noethys/Dlg/DLG_Saisie_lot_tresor_public_magnus.py": [
        ("with open(os.path.join(repertoire, \"WTAMC001.txt\"), 'w') as fichier:\n                if six.PY2:\n                    contenu_lignes = contenu_lignes.encode(\"utf8\")",
         "with open(os.path.join(repertoire, \"WTAMC001.txt\"), 'w', encoding=\"utf-8\") as fichier:"),
        ("with open(os.path.join(repertoire, \"WTAMC001AS.txt\"), 'w') as fichier:\n                if six.PY2:\n                    contenu_lignes_detail = contenu_lignes_detail.encode(\n                        \"utf8\")",
         "with open(os.path.join(repertoire, \"WTAMC001AS.txt\"), 'w', encoding=\"utf-8\") as fichier:"),
        ("with open(os.path.join(repertoire, \"WTAMC001PJ.txt\"), 'w') as fichier:\n                if six.PY2:\n                    contenu_lignes_pj = contenu_lignes_pj.encode(\"utf8\")",
         "with open(os.path.join(repertoire, \"WTAMC001PJ.txt\"), 'w', encoding=\"utf-8\") as fichier:"),
    ],
}
changed = 0
for rel, pairs in replacements.items():
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in pairs:
        if old not in text:
            print(f"motif absent: {rel}: {old[:80]!r}")
            continue
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"corrigé: {rel}")
        changed += 1
print(f"{changed} fichier(s) modifié(s)")
