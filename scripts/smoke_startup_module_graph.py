#!/usr/bin/env python3
"""Vérifie les imports exécutés au démarrage de Noethys sans lancer l'interface.

Le test charge d'abord les hooks runtime, puis importe les modules principaux
référencés en tête de Noethys.py. Il n'instancie pas MainFrame, ne démarre pas
la boucle wx, n'ouvre aucune base et interdit explicitement les connexions
réseau pendant les imports.
"""
from __future__ import annotations

import importlib
import importlib.util
import os
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))

# Permet aux modules compatibles de reconnaître un environnement de contrôle.
os.environ["NOETHYS_SMOKE_TEST"] = "1"

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

STARTUP_MODULES = (
    "Chemins",
    "Utils.UTILS_Traduction",
    "Utils.UTILS_Linux",
    "Utils.UTILS_Adaptations",
    "Utils.UTILS_Config",
    "Utils.UTILS_Customize",
    "Utils.UTILS_Historique",
    "Utils.UTILS_Sauvegarde_auto",
    "Utils.UTILS_Rapport_bugs",
    "Utils.UTILS_Utilisateurs",
    "Utils.UTILS_Interface",
    "Utils.UTILS_Fichiers",
    "Utils.UTILS_Json",
    "GestionDB",
    "Utils.UTILS_Parametres",
    "FonctionsPerso",
    "Ctrl.CTRL_Accueil",
    "Ctrl.CTRL_Messages",
    "Ctrl.CTRL_Identification",
    "Ctrl.CTRL_Numfacture",
    "Ctrl.CTRL_Recherche_individus",
    "Ctrl.CTRL_Ephemeride",
    "Dlg.DLG_Effectifs",
    "Dlg.DLG_Message_html",
    "Dlg.DLG_Enregistrement",
    "Ctrl.CTRL_Toaster",
    "Ctrl.CTRL_Portail_serveur",
    "Ctrl.CTRL_TaskBarIcon",
    "wx.lib.agw.aui",
    "wx.lib.agw.advancedsplash",
    "wx.lib.agw.toasterbox",
)


def load_hook(filename: str) -> None:
    path = ROOT / "packaging" / filename
    module_name = f"startup_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Impossible de charger {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)


def _network_forbidden(*args, **kwargs):
    raise RuntimeError("Accès réseau interdit pendant le smoke-test de démarrage")


def main() -> int:
    for filename in HOOKS:
        load_hook(filename)

    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_create_connection = socket.create_connection
    socket.socket.connect = _network_forbidden
    socket.socket.connect_ex = _network_forbidden
    socket.create_connection = _network_forbidden

    failures = 0
    try:
        for module_name in STARTUP_MODULES:
            try:
                importlib.import_module(module_name)
            except Exception as err:
                failures += 1
                print(f"- {module_name}: {type(err).__name__}: {err}")
            else:
                print(f"- {module_name}: ok")
    finally:
        socket.socket.connect = original_connect
        socket.socket.connect_ex = original_connect_ex
        socket.create_connection = original_create_connection

    if failures:
        print(f"\n{failures} module(s) du démarrage non importable(s).", file=sys.stderr)
        return 1
    print("\nGraphe d'imports du démarrage valide, sans accès réseau.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
