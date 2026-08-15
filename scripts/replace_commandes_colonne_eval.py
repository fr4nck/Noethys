#!/usr/bin/env python3
from pathlib import Path

path = Path("noethys/Dlg/DLG_Saisie_commandes_colonne.py")
text = path.read_text(encoding="utf-8")

if "import ast\n" not in text:
    marker = "import six\n"
    if marker not in text:
        raise SystemExit("point d'insertion ast absent")
    text = text.replace(marker, marker + "import ast\n", 1)

patterns = [
    "eval(dictParametres)",
    "eval(self.dictDonnees[\"parametres\"])",
]
count = text.count(patterns[0]) + text.count(patterns[1])
if count != 5:
    raise SystemExit(f"5 eval attendus, trouvé {count}")
text = text.replace(patterns[0], "ast.literal_eval(dictParametres)")
text = text.replace(patterns[1], "ast.literal_eval(self.dictDonnees[\"parametres\"])")
path.write_text(text, encoding="utf-8")
print("DLG_Saisie_commandes_colonne.py: 5 eval remplacés")
