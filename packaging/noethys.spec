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
    # wx.richtext charge wx._xml au runtime. PyInstaller ne détecte pas toujours
    # ce module natif via le graphe d'import ; sans lui le portable plante dès
    # l'import de DLG_Portail_config.
    "wx._xml",
    "wx.richtext",
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
# l'application est figée. Le bundle onedir doit donc conserver une racine
# plate, comme les distributions historiques de Noethys.
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
    # Installer d'abord le journal d'erreurs : si un hook de compatibilité casse,
    # le diagnostic est persisté au lieu de disparaître dans l'EXE sans console.
    str(ROOT / "packaging" / "runtime_crashlog.py"),
    # Mesure localement les délais d'ouverture des fenêtres et les allers-retours
    # MySQL, sans conserver les paramètres SQL ni les titres métier.
    str(ROOT / "packaging" / "runtime_perf.py"),
    # Les hooks de compatibilité sont volontairement exécutés avant le smoke-test
    # afin que la qualification du bundle couvre aussi leur initialisation.
    str(ROOT / "packaging" / "runtime_wx_compat.py"),
    str(ROOT / "packaging" / "runtime_wx_text_compat.py"),
    str(ROOT / "packaging" / "runtime_wx_list_width_compat.py"),
    str(ROOT / "packaging" / "runtime_objectlistview_value_compat.py"),
    str(ROOT / "packaging" / "runtime_objectlistview_date_compat.py"),
    str(ROOT / "packaging" / "runtime_pillow_compat.py"),
    # En mode de qualification, le smoke valide ensuite le bundle puis quitte
    # avant tout accès à la configuration ou à la base utilisateur.
    str(ROOT / "packaging" / "runtime_frozen_smoke.py"),
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
    # PyInstaller 6 place par défaut les fichiers de support dans `_internal`.
    # Noethys résout historiquement ses ressources depuis le dossier de l'EXE ;
    # `.` restaure le layout onedir plat attendu par Chemins.py.
    contents_directory=".",
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
