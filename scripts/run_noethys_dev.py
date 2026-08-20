#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lance Noethys depuis les sources avec les mêmes hooks que le portable.

Ce lanceur est destiné à la recette locale Windows : pas de PyInstaller, pas de
ZIP à retélécharger. Les hooks de diagnostic/compatibilité du portable sont
chargés avant Noethys.py, puis l'application utilise le dossier historique
``noethys/Portable`` pour sa configuration et ses logs.
"""

from pathlib import Path
import os
import runpy
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
PACKAGING = ROOT / "packaging"
PORTABLE = NOETHYS / "Portable"
PORTABLE_DATA = PORTABLE / "Data"
EXAMPLES = NOETHYS / "Static" / "Exemples"

PORTABLE.mkdir(parents=True, exist_ok=True)
PORTABLE_DATA.mkdir(parents=True, exist_ok=True)

# La fenêtre de bienvenue historique liste les fichiers locaux via
# UTILS_Fichiers.GetRepData(), donc en mode portable elle regarde Portable/Data.
# Dans une installation classique, les exemples sont copiés par la logique de
# premier démarrage. Pour la recette depuis les sources, on reproduit cette
# initialisation sans téléchargement et sans écraser un fichier existant.
if EXAMPLES.is_dir():
    for source in EXAMPLES.iterdir():
        if source.is_file() and source.name.startswith("EXEMPLE_") and source.suffix.lower() == ".dat":
            destination = PORTABLE_DATA / source.name
            if not destination.exists():
                shutil.copy2(str(source), str(destination))

# Noethys utilise des imports historiques absolus (Ctrl, Utils, Dlg...).
sys.path.insert(0, str(NOETHYS))
sys.path.insert(0, str(ROOT))

# Les hooks de diagnostic déterminent leur dossier de logs depuis
# sys.executable. En mode source, on leur présente temporairement l'emplacement
# de Noethys.py afin qu'ils retrouvent noethys/Portable, exactement comme le
# portable trouve Portable à côté de Noethys.exe. On restaure ensuite le vrai
# python.exe.
real_executable = sys.executable
try:
    sys.executable = str(NOETHYS / "Noethys.exe")
    runpy.run_path(str(PACKAGING / "runtime_crashlog.py"), run_name="__noethys_runtime_crashlog__")
    runpy.run_path(str(PACKAGING / "runtime_perf.py"), run_name="__noethys_runtime_perf__")
finally:
    sys.executable = real_executable

# Même ordre que packaging/noethys.spec, hors smoke-test réservé à PyInstaller.
for hook in (
    "runtime_wx_compat.py",
    "runtime_wx_text_compat.py",
    "runtime_wx_list_width_compat.py",
    "runtime_objectlistview_value_compat.py",
    "runtime_objectlistview_date_compat.py",
    "runtime_pillow_compat.py",
):
    runpy.run_path(str(PACKAGING / hook), run_name="__noethys_%s__" % hook.replace(".", "_"))

os.chdir(str(NOETHYS))
sys.argv[0] = str(NOETHYS / "Noethys.py")
runpy.run_path(str(NOETHYS / "Noethys.py"), run_name="__main__")
