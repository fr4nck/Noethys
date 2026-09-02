# -*- coding: utf-8 -*-
"""Smoke tests du bundle PyInstaller avant l'exécution de Noethys.py.

Ce runtime hook ne fait strictement rien en usage normal.

``NOETHYS_FROZEN_SMOKE=1`` valide le bundle portable sans ouvrir la
configuration ni une base utilisateur.

``NOETHYS_INSTALL_CONFIG_SMOKE=1`` valide le contrat de l'installable : la
configuration doit rester dans le profil utilisateur, ne jamais dépendre du
répertoire courant et ne pas être remplacée par la migration historique.

Le hook utilise ``os._exit`` en mode smoke afin qu'un échec dans une application
PyInstaller ``console=False`` ne puisse pas ouvrir une boîte de dialogue fatale
et laisser la CI bloquée en attente d'une interaction humaine.
"""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path


def _finish(root: Path, code: int, message: str, marker_prefix: str = "FROZEN-SMOKE") -> None:
    marker = root / (
        "%s-OK.txt" % marker_prefix if code == 0 else "%s-ERROR.txt" % marker_prefix
    )
    try:
        marker.write_text(message + "\n", encoding="utf-8")
    finally:
        os._exit(code)


def _require_frozen(root: Path, marker_prefix: str) -> None:
    if not getattr(sys, "frozen", False):
        _finish(root, 2, "Le smoke exige un exécutable figé", marker_prefix)


if os.environ.get("NOETHYS_INSTALL_CONFIG_SMOKE") == "1":
    root = Path(sys.executable).resolve().parent
    marker_prefix = "INSTALL-CONFIG-SMOKE"
    _require_frozen(root, marker_prefix)

    if (root / "Portable").exists():
        _finish(
            root,
            5,
            "L'installable contient un marqueur Portable et isolerait la configuration utilisateur",
            marker_prefix,
        )

    expected_raw = os.environ.get("NOETHYS_EXPECT_CONFIG_PATH", "")
    if not expected_raw:
        _finish(root, 6, "NOETHYS_EXPECT_CONFIG_PATH est absent", marker_prefix)

    expected = Path(expected_raw).resolve()
    if not expected.is_file():
        _finish(
            root,
            7,
            "La configuration sentinelle attendue est absente: %s" % expected,
            marker_prefix,
        )

    before = expected.read_bytes()
    try:
        import Chemins
        from Utils import UTILS_Fichiers

        actual = Path(UTILS_Fichiers.GetRepUtilisateur("Config.json")).resolve()
        if actual != expected:
            _finish(
                root,
                8,
                "Mauvais chemin de configuration: %s (attendu: %s)" % (actual, expected),
                marker_prefix,
            )

        application_root = Path(Chemins.GetMainPath("")).resolve()
        if application_root != root:
            _finish(
                root,
                9,
                "Le chemin applicatif figé n'est pas ancré sur Noethys.exe: %s" % application_root,
                marker_prefix,
            )

        # Rejoue la migration réellement exécutée au démarrage. Avec une
        # configuration déjà existante, elle doit être strictement sans effet.
        UTILS_Fichiers.DeplaceFichiers()
    except Exception as exc:
        _finish(
            root,
            10,
            "Smoke configuration installée en échec: %s: %s"
            % (type(exc).__name__, exc),
            marker_prefix,
        )

    if not expected.is_file() or expected.read_bytes() != before:
        _finish(
            root,
            11,
            "La configuration utilisateur a été modifiée pendant la migration",
            marker_prefix,
        )

    _finish(root, 0, "Configuration installable Noethys préservée", marker_prefix)


if os.environ.get("NOETHYS_FROZEN_SMOKE") == "1":
    root = Path(sys.executable).resolve().parent
    _require_frozen(root, "FROZEN-SMOKE")

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
                "Import figé en échec pour %s: %s: %s"
                % (module_name, type(exc).__name__, exc),
            )

    _finish(root, 0, "Bundle figé Noethys validé")
