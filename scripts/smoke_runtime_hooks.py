#!/usr/bin/env python3
"""Exécute les hooks runtime du package avant le lancement de PyInstaller."""
from __future__ import annotations

import builtins
import importlib.util
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))

HOOKS = (
    ROOT / "packaging" / "runtime_python2_builtins_compat.py",
    ROOT / "packaging" / "runtime_wx_compat.py",
    ROOT / "packaging" / "runtime_wx_text_compat.py",
    ROOT / "packaging" / "runtime_wx_list_width_compat.py",
    ROOT / "packaging" / "runtime_objectlistview_value_compat.py",
    ROOT / "packaging" / "runtime_objectlistview_date_compat.py",
    ROOT / "packaging" / "runtime_aui_compat.py",
    ROOT / "packaging" / "runtime_pillow_compat.py",
    ROOT / "packaging" / "runtime_sqlite_path_compat.py",
    ROOT / "packaging" / "runtime_mysql_interface_compat.py",
    ROOT / "packaging" / "runtime_gestiondb_lifecycle_compat.py",
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
    import GestionDB
    import wx
    import wx.lib.agw.aui as aui
    from PIL import Image
    from ObjectListView import CellEditor

    aliases_attendus = {
        "long": int,
        "basestring": str,
        "unicode": str,
        "unichr": chr,
        "xrange": range,
    }
    for nom, cible in aliases_attendus.items():
        if getattr(builtins, nom, None) is not cible:
            raise RuntimeError("Compatibilité builtin Python 2 inactive : %s" % nom)
    if builtins.cmp(1, 2) != -1 or builtins.cmp(2, 1) != 1 or builtins.cmp(1, 1) != 0:
        raise RuntimeError("Compatibilité builtin Python 2 inactive : cmp")

    for nom in ("EmptyBitmap", "EmptyIcon", "EmptyImage", "BitmapFromImage", "NewId"):
        if not hasattr(wx, nom):
            raise RuntimeError("Alias wx manquant après hook : %s" % nom)

    if wx.TextCtrl.SetValue.__name__ != "_wx_text_compat":
        raise RuntimeError("Normalisation bytes/texte wx.TextCtrl inactive")
    if wx.StaticText.SetLabel.__name__ != "_wx_text_compat":
        raise RuntimeError("Normalisation bytes/texte wx.StaticText inactive")
    if wx.ListCtrl.SetColumnWidth.__name__ != "_set_column_width_compat":
        raise RuntimeError("Normalisation des largeurs wx.ListCtrl inactive")
    if CellEditor.BaseCellTextEditor.SetValue.__name__ != "_set_value_compat":
        raise RuntimeError("Normalisation des valeurs vides ObjectListView inactive")
    if CellEditor.DateEditor.SetValue.__name__ != "_set_value_compat":
        raise RuntimeError("Tolérance des dates ObjectListView inactive")

    if aui.AuiManager.LoadPerspective.__name__ != "_load_perspective_compat":
        raise RuntimeError("Protection AUI LoadPerspective inactive")
    if aui.AuiManager.UnInit.__name__ != "_uninit_compat":
        raise RuntimeError("Protection AUI UnInit inactive")

    for nom in ("ANTIALIAS", "NEAREST", "BILINEAR", "BICUBIC", "LANCZOS"):
        if not hasattr(Image, nom):
            raise RuntimeError("Alias Pillow manquant après hook : %s" % nom)
    if not hasattr(Image.Image, "tostring") or not hasattr(Image, "fromstring"):
        raise RuntimeError("Compatibilité historique Pillow incomplète")

    if GestionDB.DB.Close.__name__ != "_close_compat":
        raise RuntimeError("Fermeture idempotente GestionDB inactive")
    if GestionDB.DB.ReqInsert.__name__ != "_req_insert_compat":
        raise RuntimeError("Retour sûr ReqInsert GestionDB inactif")

    connexion = sqlite3.connect(b":memory:")
    try:
        connexion.execute("SELECT 1")
    finally:
        connexion.close()

    if (
        not GestionDB.IMPORT_MYSQLDB_OK
        and GestionDB.IMPORT_MYSQLCONNECTOR_OK
        and GestionDB.INTERFACE_MYSQL != "mysql.connector"
    ):
        raise RuntimeError("Le repli automatique vers mysql.connector n'est pas actif")


def main() -> int:
    for hook in HOOKS:
        print("Hook runtime : %s" % hook.name)
        charger_hook(hook)
    verifier_garanties()
    print("Hooks runtime valides.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
