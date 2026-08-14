#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

replacements = {
    "noethys/Dlg/DLG_Saisie_piece.py": [
        (
            '            dateJour = int(dateDebut[:2])\n            dateMois = int(dateDebut[3:5])\n            dateAnnee = int(dateDebut[6:10])\n            dateDebut = datetime.date(dateAnnee, dateMois, dateJour)',
            '            dateDebut = datetime.datetime.strptime(dateDebut, "%d/%m/%Y").date()',
        ),
    ],
    "noethys/Ol/OL_Feries.py": [
        (
            '        jour = int(dateTxt[8:10])\n        mois = int(dateTxt[5:7])-1\n        annee = int(dateTxt[:4])\n        date = wx.DateTime()\n        date.Set(jour, mois, annee)',
            '        dateDD = datetime.date.fromisoformat(dateTxt[:10])\n        date = wx.DateTime()\n        date.Set(dateDD.day, dateDD.month - 1, dateDD.year)',
        ),
    ],
    "noethys/Ol/OL_Vacances.py": [
        (
            '            jour = int(texteDate[8:10])\n            mois = int(texteDate[5:7])\n            annee = int(texteDate[:4])\n            jourSemaine = int(datetime.date(annee, mois, jour).strftime("%w"))\n            texte = listeJours[jourSemaine-1] + " " + str(jour) + " " + listeMois[mois-1] + " " + str(annee)',
            '            dateDD = datetime.date.fromisoformat(texteDate[:10])\n            texte = listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month-1] + " " + str(dateDD.year)',
        ),
        (
            '        jour = int(dateTxt[8:10])\n        mois = int(dateTxt[5:7])-1\n        annee = int(dateTxt[:4])\n        date = wx.DateTime()\n        date.Set(jour, mois, annee)',
            '        dateDD = datetime.date.fromisoformat(dateTxt[:10])\n        date = wx.DateTime()\n        date.Set(dateDD.day, dateDD.month - 1, dateDD.year)',
        ),
    ],
}

changed = 0
for rel, pairs in replacements.items():
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in pairs:
        if old not in text:
            raise SystemExit(f"motif attendu absent: {rel}")
        text = text.replace(old, new, 1)
    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"corrigé: {rel}")
        changed += 1

print(f"{changed} fichier(s) modifié(s)")
