#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# DLG_Etat_global.py
path = ROOT / "noethys/Dlg/DLG_Etat_global.py"
text = path.read_text(encoding="utf-8")
marker = "from Utils.UTILS_Traduction import _\n"
if "from Utils import UTILS_Expressions\n" not in text:
    if marker not in text:
        raise SystemExit("import marker absent DLG_Etat_global")
    text = text.replace(marker, marker + "from Utils import UTILS_Expressions\n", 1)
old = "resultat = eval(formule)"
new = 'resultat = UTILS_Expressions.EvaluerExpression(formule, variables={"self": self, "duree": duree}, fonctions={"SI": SI})'
if text.count(old) != 1:
    raise SystemExit(f"1 eval attendu DLG_Etat_global, trouvé {text.count(old)}")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("DLG_Etat_global.py migré")

# OL_Etat_nomin_resultats.py
path = ROOT / "noethys/Ol/OL_Etat_nomin_resultats.py"
text = path.read_text(encoding="utf-8")
marker = "from Utils.UTILS_Traduction import _\n"
if "from Utils import UTILS_Expressions\n" not in text:
    if marker not in text:
        raise SystemExit("import marker absent OL_Etat_nomin_resultats")
    text = text.replace(marker, marker + "from Utils import UTILS_Expressions\n", 1)
old = "setattr(self, champ.code, eval(formule))"
new = 'setattr(self, champ.code, UTILS_Expressions.EvaluerExpression(formule, variables={"self": self}, fonctions={"SI": SI}))'
if text.count(old) != 1:
    raise SystemExit(f"1 eval attendu OL_Etat_nomin_resultats, trouvé {text.count(old)}")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("OL_Etat_nomin_resultats.py migré")
