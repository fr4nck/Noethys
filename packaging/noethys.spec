# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).resolve().parent
NOETHYS = ROOT / "noethys"

hiddenimports = []
for package in (
    "matplotlib.backends",
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
    "mysql.connector",
    "Crypto",
    "Cryptodome",
):
    hiddenimports += collect_submodules(package)

hiddenimports += ["pyttsx3.drivers", "pyttsx3.drivers.sapi5"]
hiddenimports += ["mysql", "mysql.connector", "mysql.connector.constants", "mysql.connector.conversion"]

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
    str(ROOT / "packaging" / "runtime_python2_builtins_compat.py"),
    str(ROOT / "packaging" / "runtime_wx_compat.py"),
    str(ROOT / "packaging" / "runtime_wx_text_compat.py"),
    str(ROOT / "packaging" / "runtime_wx_list_width_compat.py"),
    str(ROOT / "packaging" / "runtime_objectlistview_value_compat.py"),
    str(ROOT / "packaging" / "runtime_objectlistview_date_compat.py"),
    str(ROOT / "packaging" / "runtime_aui_compat.py"),
    str(ROOT / "packaging" / "runtime_pillow_compat.py"),
    str(ROOT / "packaging" / "runtime_sqlite_path_compat.py"),
    str(ROOT / "packaging" / "runtime_mysql_interface_compat.py"),
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
