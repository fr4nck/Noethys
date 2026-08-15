#!/usr/bin/env python3
from pathlib import Path

# 1) PES : préserver explicitement l'encodage historique ISO-8859-1.
p = Path('noethys/Dlg/DLG_Saisie_lot_tresor_public_pes.py')
t = p.read_text(encoding='utf-8')
old = '''        # Création du fichier texte\n        f = open(cheminFichier, "w")\n        try:\n            if six.PY2:\n                f.write(doc.toxml(encoding="ISO-8859-1"))\n            else:\n                #f.write(doc.toprettyxml(indent="  "))\n                f.write(doc.toxml())\n        finally:\n            f.close()\n'''
new = '''        # Création du fichier PES. Le format historique Noethys est\n        # explicitement ISO-8859-1 ; en Python 3, toxml(encoding=...) renvoie\n        # des octets, donc on écrit en binaire pour conserver ce contrat.\n        with open(cheminFichier, "wb") as f:\n            f.write(doc.toxml(encoding="ISO-8859-1"))\n'''
if t.count(old) != 1:
    raise SystemExit('bloc PES attendu absent ou ambigu')
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')

# 2) Utilitaire BIC : le fichier d'entrée n'est pas sous contrôle de Noethys,
# donc détecter l'encodage au lieu de dépendre de la locale système.
p = Path('noethys/FonctionsPerso.py')
t = p.read_text(encoding='utf-8')
old = '''def PrepareFichierBIC():\n    fichier = open("liste_bic_france.txt", 'r')\n    nouveauFichier = open(UTILS_Fichiers.GetRepTemp(fichier="liste_bic_france_new.txt"), 'w')\n    for ligne in fichier :\n        ID, nom, ville, divers, bic = ligne.split("\\t")\n        nouvelleLigne = """("%s", "%s", "%s")\\n""" % (nom, ville, bic[:-1])\n        nouveauFichier.write(nouvelleLigne)\n    nouveauFichier.close()\n    fichier.close()\n'''
new = '''def PrepareFichierBIC():\n    import chardet\n\n    with open("liste_bic_france.txt", "rb") as fichier:\n        contenu = fichier.read()\n    detection = chardet.detect(contenu)\n    encoding = detection.get("encoding") or "utf-8"\n    texte = contenu.decode(encoding, errors="replace")\n\n    with open(UTILS_Fichiers.GetRepTemp(fichier="liste_bic_france_new.txt"), "w", encoding="utf-8", newline="") as nouveauFichier:\n        for ligne in texte.splitlines():\n            ID, nom, ville, divers, bic = ligne.split("\\t")\n            nouvelleLigne = """("%s", "%s", "%s")\\n""" % (nom, ville, bic)\n            nouveauFichier.write(nouvelleLigne)\n'''
if t.count(old) != 1:
    raise SystemExit('bloc BIC attendu absent ou ambigu')
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')

# 3) Pièces jointes texte : lire les octets, détecter le charset et le déclarer
# explicitement dans MIMEText.
p = Path('noethys/Utils/UTILS_Envoi_email.py')
t = p.read_text(encoding='utf-8')
if 'import chardet\n' not in t:
    t = t.replace('import mimetypes\n', 'import mimetypes\nimport chardet\n', 1)
old = '''            if maintype == 'text':\n                fp = open(fichier)\n                # Note : we should handle calculating the charset\n                part = MIMEText(fp.read(), _subtype=subtype)\n                fp.close()\n'''
new = '''            if maintype == 'text':\n                with open(fichier, 'rb') as fp:\n                    contenu = fp.read()\n                detection = chardet.detect(contenu)\n                charset = detection.get('encoding') or 'utf-8'\n                texte = contenu.decode(charset, errors='replace')\n                part = MIMEText(texte, _subtype=subtype, _charset=charset)\n'''
if t.count(old) != 1:
    raise SystemExit('bloc pièce jointe texte attendu absent ou ambigu')
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')

print('Dernières frontières texte corrigées')
