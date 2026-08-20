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
import sys

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
PACKAGING = ROOT / "packaging"
PORTABLE = NOETHYS / "Portable"

PORTABLE.mkdir(parents=True, exist_ok=True)

# Noethys utilise des imports historiques absolus (Ctrl, Utils, Dlg...).
sys.path.insert(0, str(NOETHYS))
sys.path.insert(0, str(ROOT))

# runtime_crashlog détermine son dossier de logs depuis sys.executable. En mode
# source, on lui présente temporairement l'emplacement de Noethys.py afin qu'il
# retrouve noethys/Portable, exactement comme le portable trouve Portable à
# côté de Noethys.exe. On restaure ensuite le vrai python.exe.
real_executable = sys.executable
try:
    sys.executable = str(NOETHYS / "Noethys.exe")
    runpy.run_path(str(PACKAGING / "runtime_crashlog.py"), run_name="__noethys_runtime_crashlog__")
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
