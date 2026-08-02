#!/usr/bin/env python3
"""Exécute les hooks runtime du package avant le lancement de PyInstaller.

Ce contrôle ne démarre pas Noethys et n'ouvre aucune base. Il vérifie que les
modules de compatibilité sont importables et que leurs garanties minimales sont
présentes dans l'environnement Windows de fabrication.
"""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS = (
    ROOT / "packaging" / "runtime_wx_compat.py",
    ROOT / "packaging" / "runtime_pillow_compat.py",
    ROOT / "packaging" / "runtime_sqlite_path_compat.py",
    ROOT / "packaging" / "runtime_mysql_interface_compat.py",
)


def charger_hook(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    nom_module = "noethys_hook_%s" % path.stem
    spec = importlib.util.spec_from_file_location(nom_module, path)
    if spec is None or spec.loader is None:
        raise ImportError("Impossible de charger %s" % path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[nom_module] = module
    spec.loader.exec_module(module)


def verifier_garanties() -> None:
    import wx
    from PIL import Image

    for nom in ("EmptyBitmap", "EmptyIcon", "EmptyImage", "BitmapFromImage", "NewId"):
        if not hasattr(wx, nom):
            raise RuntimeError("Alias wx manquant après hook : %s" % nom)

    for nom in ("ANTIALIAS", "NEAREST", "BILINEAR", "BICUBIC", "LANCZOS"):
        if not hasattr(Image, nom):
            raise RuntimeError("Alias Pillow manquant après hook : %s" % nom)

    if not hasattr(Image.Image, "tostring") or not hasattr(Image, "fromstring"):
        raise RuntimeError("Compatibilité historique Pillow incomplète")

    # Le hook SQLite doit accepter un chemin bytes sans ouvrir une base métier.
    connexion = sqlite3.connect(b":memory:")
    try:
        connexion.execute("SELECT 1")
    finally:
        connexion.close()


def main() -> int:
    for hook in HOOKS:
        print("Hook runtime : %s" % hook.name)
        charger_hook(hook)
    verifier_garanties()
    print("Hooks runtime valides.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
