from pathlib import Path

FILES = [
    Path("noethys/Dlg/DLG_Saisie_lot_forfaits_credits.py"),
    Path("noethys/Dlg/DLG_Saisie_modele_prestation.py"),
    Path("noethys/Dlg/DLG_Saisie_prestation.py"),
]

for path in FILES:
    text = path.read_text(encoding="utf-8")
    old = '''            if date_debut == None and date_fin == None : label = _(u"%s (Sans période de validité)") % nom\n            if date_debut == None and date_fin != None : label = _(u"%s (Jusqu'au %s)") % (nom, '''
    if old not in text:
        raise SystemExit(f"pattern start not found in {path}")

    # The four historical conditions cover the complete None/non-None cartesian product.
    # Turn them into one exhaustive chain without changing any supported output.
    text = text.replace(
        '            if date_debut == None and date_fin == None : label = _(u"%s (Sans période de validité)") % nom\n'
        '            if date_debut == None and date_fin != None : label = _(u"%s (Jusqu\'au %s)")',
        '            if date_debut == None and date_fin == None : label = _(u"%s (Sans période de validité)") % nom\n'
        '            elif date_debut == None and date_fin != None : label = _(u"%s (Jusqu\'au %s)")',
        1,
    )
    text = text.replace(
        '            if date_debut != None and date_fin == None : label = _(u"%s (A partir du %s)")',
        '            elif date_debut != None and date_fin == None : label = _(u"%s (A partir du %s)")',
        1,
    )
    text = text.replace(
        '            if date_debut != None and date_fin != None : label = _(u"%s (Du %s au %s)")',
        '            else : label = _(u"%s (Du %s au %s)")',
        1,
    )
    path.write_text(text, encoding="utf-8")
