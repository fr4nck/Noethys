# -*- coding: utf-8 -*-
"""Smoke test du bundle PyInstaller avant l'exécution de Noethys.py.

Ce runtime hook ne fait strictement rien en usage normal. Quand
``NOETHYS_FROZEN_SMOKE=1`` est défini, il valide que l'exécutable est réellement
figé, que ses ressources essentielles sont présentes et que plusieurs piles
runtime critiques sont importables depuis le bundle. Il quitte ensuite avec un
code 0 avant que Noethys n'ouvre une configuration ou une base utilisateur.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path


if os.environ.get("NOETHYS_FROZEN_SMOKE") == "1":
    if not getattr(sys, "frozen", False):
        raise RuntimeError("Le smoke NOETHYS_FROZEN_SMOKE exige un exécutable figé")

    root = Path(sys.executable).resolve().parent
    required = (
        root / "Static",
        root / "Versions.txt",
        root / "Licence.txt",
        root / "Icone.ico",
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError("Ressources du bundle absentes: %s" % ", ".join(missing))

    # Imports représentatifs des fonctions critiques et de leurs modules natifs.
    # Aucun de ces imports ne doit ouvrir une base, créer wx.App ou écrire la
    # configuration utilisateur.
    modules = (
        "wx",
        "PIL.Image",
        "reportlab.pdfgen.canvas",
        "dateutil.parser",
        "pytz",
        "lxml.etree",
        "mysql.connector",
        "MySQLdb",
        "Crypto.Hash.SHA256",
        "cryptography",
        "requests",
    )
    for module_name in modules:
        importlib.import_module(module_name)

    raise SystemExit(0)
