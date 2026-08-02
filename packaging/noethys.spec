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
):
    hiddenimports += collect_submodules(package)

datas = [
    (str(NOETHYS / "Static"), "noethys/Static"),
    (str(NOETHYS / "Versions.txt"), "noethys"),
    (str(NOETHYS / "Licence.txt"), "noethys"),
    (str(NOETHYS / "Icone.ico"), "noethys"),
]
datas += collect_data_files("matplotlib")
datas += collect_data_files("pytz")
datas += collect_data_files("reportlab")

analysis = Analysis(
    [str(NOETHYS / "Noethys.py")],
    pathex=[str(ROOT), str(NOETHYS)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
