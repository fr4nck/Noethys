# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# SPECPATH désigne le dossier contenant le fichier .spec.
ROOT = Path(SPECPATH).resolve().parent
NOETHYS = ROOT / "noethys"


def collect_runtime_submodules(package):
    """Collecte les sous-modules runtime en excluant les suites de tests.

    Certains paquets (Twisted, SQLAlchemy, icalendar, comtypes…) embarquent de
    très nombreuses suites de tests. Les inclure dans l'application portable
    augmente fortement la taille du build et peut provoquer des avertissements
    sur des dépendances de développement absentes (pytest, hypothesis, etc.).
    """
    excluded_parts = {"test", "tests", "testing"}
    return [
        name
        for name in collect_submodules(package)
        if not excluded_parts.intersection(name.split("."))
    ]


hiddenimports = [
    # Les backends réellement utilisés par Noethys. Le hook Matplotlib les
    # détecte également via les appels matplotlib.use('Agg'/'wxagg').
    "matplotlib.backends.backend_agg",
    "matplotlib.backends.backend_wxagg",
]
for package in (
    "reportlab",
    "sqlalchemy",
    "twisted",
    "lxml",
    "PIL",
    "dateutil",
    "pytz",
    "icalendar",
    "paramiko",
    "comtypes",
    "pyttsx3",
):
    hiddenimports += collect_runtime_submodules(package)

# Chemins.py recherche ces ressources à côté de Noethys.exe lorsque
# l'application est figée. Elles doivent donc être placées à la racine
# du dossier portable, et non dans un sous-répertoire noethys/.
datas = [
    (str(NOETHYS / "Static"), "Static"),
    (str(NOETHYS / "Versions.txt"), "."),
    (str(NOETHYS / "Licence.txt"), "."),
    (str(NOETHYS / "Icone.ico"), "."),
]
datas += collect_data_files("matplotlib")
datas += collect_data_files("pytz")
datas += collect_data_files("reportlab")

runtime_hooks = [
    # Le smoke figé doit être premier : en mode de qualification il valide le
    # bundle puis quitte avant tout accès à la configuration/base utilisateur.
    str(ROOT / "packaging" / "runtime_frozen_smoke.py"),
    str(ROOT / "packaging" / "runtime_wx_compat.py"),
    str(ROOT / "packaging" / "runtime_wx_text_compat.py"),
    str(ROOT / "packaging" / "runtime_wx_list_width_compat.py"),
    str(ROOT / "packaging" / "runtime_objectlistview_value_compat.py"),
    str(ROOT / "packaging" / "runtime_objectlistview_date_compat.py"),
    str(ROOT / "packaging" / "runtime_pillow_compat.py"),
]

analysis = Analysis(
    [str(NOETHYS / "Noethys.py")],
    pathex=[str(ROOT), str(NOETHYS)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=["tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6"],
    noarchive=False,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="Noethys",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(NOETHYS / "Icone.ico"),
)

collect = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Noethys",
)
