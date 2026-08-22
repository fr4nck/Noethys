# -*- coding: utf-8 -*-
"""Smoke test du bundle PyInstaller avant l'exécution de Noethys.py.

Ce runtime hook ne fait strictement rien en usage normal. Quand
``NOETHYS_FROZEN_SMOKE=1`` est défini, il valide que l'exécutable est réellement
figé, que ses ressources essentielles sont présentes et que plusieurs piles
runtime critiques sont importables depuis le bundle. Il quitte ensuite avant
que Noethys n'ouvre une configuration ou une base utilisateur.

Le hook utilise ``os._exit`` en mode smoke afin qu'un échec dans une application
PyInstaller ``console=False`` ne puisse pas ouvrir une boîte de dialogue fatale
et laisser la CI bloquée en attente d'une interaction humaine.
"""
from __future__ import annotations

import importlib
import os
import sys
import traceback
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

    # Imports représentatifs des fonctions critiques et de leurs modules natifs.
    # Aucun de ces imports ne doit ouvrir une base, créer wx.App ou écrire la
    # configuration utilisateur. wx.richtext dépend de wx._xml : les deux sont
    # testés explicitement pour éviter un bundle PyInstaller vert mais inutilisable.
    # Les modules Noethys ajoutés ici correspondent aux régressions réellement
    # rencontrées sur le portable : ils valident aussi les hooks de compatibilité.
    modules = (
        "wx",
        "wx._xml",
        "wx.richtext",
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
        "Ctrl.CTRL_Saisie_transport",
        "Ctrl.CTRL_TaskBarIcon",
        "Dlg.DLG_Utilisateurs_reseau",
        "Ol.OL_Modes_reglements",
        "Dlg.DLG_Emetteurs",
        "Utils.UTILS_Organisateur",
    )
    for module_name in modules:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            _finish(
                root,
                4,
                "Import figé en échec pour %s: %s: %s\n%s"
                % (module_name, type(exc).__name__, exc, traceback.format_exc()),
            )

    _finish(root, 0, "Bundle figé Noethys validé")
