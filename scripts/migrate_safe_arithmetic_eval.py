#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# DLG_Saisie_formule.py
path = ROOT / "noethys/Dlg/DLG_Saisie_formule.py"
text = path.read_text(encoding="utf-8")
marker = "from Utils.UTILS_Traduction import _\n"
if "from Utils import UTILS_Expressions\n" not in text:
    if marker not in text:
        raise SystemExit("import marker absent DLG_Saisie_formule")
    text = text.replace(marker, marker + "from Utils import UTILS_Expressions\n", 1)
old = "resultat = eval(texte)"
if text.count(old) != 1:
    raise SystemExit(f"1 eval attendu DLG_Saisie_formule, trouvé {text.count(old)}")
text = text.replace(old, "resultat = UTILS_Expressions.EvaluerArithmetique(texte)", 1)
path.write_text(text, encoding="utf-8")
print("DLG_Saisie_formule.py migré")

# OL_Suivi_budget.py
path = ROOT / "noethys/Ol/OL_Suivi_budget.py"
text = path.read_text(encoding="utf-8")
marker = "from Utils import UTILS_Config\n"
if "from Utils import UTILS_Expressions\n" not in text:
    if marker not in text:
        raise SystemExit("import marker absent OL_Suivi_budget")
    text = text.replace(marker, marker + "from Utils import UTILS_Expressions\n", 1)
old = "resultat = float(eval(valeur))"
if text.count(old) != 1:
    raise SystemExit(f"1 eval attendu OL_Suivi_budget, trouvé {text.count(old)}")
text = text.replace(old, "resultat = float(UTILS_Expressions.EvaluerArithmetique(valeur))", 1)
path.write_text(text, encoding="utf-8")
print("OL_Suivi_budget.py migré")
