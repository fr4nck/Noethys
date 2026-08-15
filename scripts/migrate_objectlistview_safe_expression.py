#!/usr/bin/env python3
from pathlib import Path

path = Path("noethys/Ctrl/CTRL_ObjectListView.py")
text = path.read_text(encoding="utf-8")

marker = "from Utils.UTILS_Traduction import _\n"
if "from Utils import UTILS_Expressions\n" not in text:
    if marker not in text:
        raise SystemExit("point d'insertion UTILS_Expressions absent")
    text = text.replace(marker, marker + "from Utils import UTILS_Expressions\n", 1)

old = '            filtre = Filter.Predicate(lambda track: eval(texteFiltre))'
new = '            filtre = Filter.Predicate(lambda track: UTILS_Expressions.EvaluerExpression(texteFiltre, variables={"track": track}, fonctions={"str": str}, methodes={"lower"}))'
if text.count(old) != 1:
    raise SystemExit(f"1 filtre actif attendu, trouvé {text.count(old)}")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("CTRL_ObjectListView.py migré vers UTILS_Expressions")
