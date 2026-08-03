#!/usr/bin/env python3
"""Vérifie le cycle SQLite essentiel de GestionDB sans toucher aux données utilisateur."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))

HOOKS = (
    "runtime_python2_builtins_compat.py",
    "runtime_wx_compat.py",
    "runtime_wx_text_compat.py",
    "runtime_wx_list_width_compat.py",
    "runtime_objectlistview_value_compat.py",
    "runtime_objectlistview_date_compat.py",
    "runtime_aui_compat.py",
    "runtime_pillow_compat.py",
    "runtime_sqlite_path_compat.py",
    "runtime_mysql_interface_compat.py",
)


def load_hook(filename: str) -> None:
    path = ROOT / "packaging" / filename
    spec = importlib.util.spec_from_file_location(f"db_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)


def main() -> int:
    for filename in HOOKS:
        load_hook(filename)

    import GestionDB

    with tempfile.TemporaryDirectory(prefix="noethys-db-") as temp_dir:
        base = Path(temp_dir) / "cycle.dat"
        db = GestionDB.DB(nomFichier=str(base), suffixe=None, modeCreation=True)
        if db.echec:
            raise RuntimeError(f"Ouverture SQLite impossible : {getattr(db, 'erreur', 'erreur inconnue')}")

        db.cursor.execute("CREATE TABLE test (ID INTEGER PRIMARY KEY AUTOINCREMENT, libelle TEXT)")
        db.Commit()
        new_id = db.ReqInsert("test", [("libelle", "école")])
        if new_id != 1:
            raise RuntimeError(f"ID inattendu après insertion : {new_id!r}")

        if not db.ExecuterReq("SELECT libelle FROM test WHERE ID=1"):
            raise RuntimeError("SELECT de contrôle refusé")
        rows = db.ResultatReq()
        if rows != [("école",)]:
            raise RuntimeError(f"Résultat SQLite inattendu : {rows!r}")

        db.Close()
        db.Close()  # La fermeture doit rester sans effet secondaire.

        if db.IDconnexion in GestionDB.DICT_CONNEXIONS:
            raise RuntimeError("Connexion encore référencée après fermeture")

    print("Cycle GestionDB SQLite valide.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
