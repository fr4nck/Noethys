#!/usr/bin/env python3
from pathlib import Path

path = Path("noethys/Dlg/DLG_Saisie_modele_commandes.py")
text = path.read_text(encoding="utf-8")

if "import ast\n" not in text:
    marker = "import copy\n"
    if marker not in text:
        raise SystemExit("point d'insertion ast absent")
    text = text.replace(marker, marker + "import ast\n", 1)

count = text.count("eval(dictParametres)") + text.count("eval(parametres)")
if count != 2:
    raise SystemExit(f"2 eval attendus, trouvé {count}")
text = text.replace("eval(dictParametres)", "ast.literal_eval(dictParametres)", 1)
text = text.replace("eval(parametres)", "ast.literal_eval(parametres)", 1)

path.write_text(text, encoding="utf-8")
print("DLG_Saisie_modele_commandes.py: 2 eval remplacés")
