# -*- coding: utf-8 -*-
"""Smoke test du bundle PyInstaller avant l'exécution de Noethys.py."""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path


def _finish(root: Path, code: int, message: str) -> None:
    marker = root / ("FROZEN-SMOKE-OK.txt" if code == 0 else "FROZEN-SMOKE-ERROR.txt")
    try:
        marker.write_text(message + "\n", encoding="utf-8")
    finally:
        os._exit(code)


if os.environ.get("NOETHYS_FROZEN_SMOKE") == "1":
    root = Path(sys.executable).resolve().parent
    if not getattr(sys, "frozen", False):
        _finish(root, 2, "Le smoke NOETHYS_FROZEN_SMOKE exige un exécutable figé")

    required = (
        root / "Static",
        root / "Versions.txt",
        root / "Licence.txt",
        root / "Icone.ico",
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        _finish(root, 3, "Ressources du bundle absentes: %s" % ", ".join(missing))

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
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            _finish(
                root,
                4,
                "Import figé en échec pour %s: %s: %s"
                % (module_name, type(exc).__name__, exc),
            )

    _finish(root, 0, "Bundle figé Noethys validé")
