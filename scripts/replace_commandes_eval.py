#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "noethys/Ctrl/CTRL_Commande_repas.py",
    ROOT / "noethys/Dlg/DLG_Saisie_commande.py",
]

for path in FILES:
    text = path.read_text(encoding="utf-8")
    if "import ast\n" not in text:
        marker = "import six\n"
        if marker not in text:
            raise SystemExit(f"point d'insertion ast absent: {path}")
        text = text.replace(marker, marker + "import ast\n", 1)
    count = text.count("eval(parametres)")
    if count != 2:
        raise SystemExit(f"2 eval(parametres) attendus dans {path}, trouvé {count}")
    text = text.replace("eval(parametres)", "ast.literal_eval(parametres)")
    path.write_text(text, encoding="utf-8")
    print(f"{path.name}: 2 eval remplacés")
