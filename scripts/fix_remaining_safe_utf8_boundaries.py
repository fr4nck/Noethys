#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
replacements = {
    "noethys/Dlg/DLG_Saisie_lot_tresor_public_jvs.py": [
        ('f = open(cheminFichier, "w")\n        try:\n            if six.PY2:\n                f.write(doc.toxml(encoding="UTF-8"))\n            else:\n                #f.write(doc.toprettyxml(indent="  "))\n                f.write(doc.toxml())',
         'f = open(cheminFichier, "wb")\n        try:\n            f.write(doc.toxml(encoding="UTF-8"))'),
    ],
    "noethys/Utils/UTILS_Prelevements.py": [
        ('f = open(nomFichier, "w")\n    try:\n        f.write(doc.toprettyxml(indent="  "))',
         'f = open(nomFichier, "wb")\n    try:\n        f.write(doc.toprettyxml(indent="  ", encoding="UTF-8"))'),
    ],
    "noethys/Dlg/DLG_Traductions.py": [
        ('fp = open(fichier)\n                # Note : we should handle calculating the charset\n                part = MIMEText(fp.read(), _subtype=subtype)',
         'fp = open(fichier, encoding="utf-8")\n                part = MIMEText(fp.read(), _subtype=subtype, _charset="utf-8")'),
    ],
}

changed = 0
for rel, pairs in replacements.items():
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in pairs:
        if old not in text:
            raise SystemExit(f"motif absent: {rel}: {old[:100]!r}")
        text = text.replace(old, new, 1)
    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"corrigé: {rel}")
        changed += 1
print(f"{changed} fichier(s) modifié(s)")
