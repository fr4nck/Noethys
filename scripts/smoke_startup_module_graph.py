#!/usr/bin/env python3
"""Vérifie les imports exécutés au démarrage de Noethys sans lancer l'interface.

Le test charge d'abord les hooks runtime, puis importe les modules principaux
référencés en tête de Noethys.py. Il n'instancie pas MainFrame, ne démarre pas
la boucle wx et n'ouvre aucune base de données.
"""
from __future__ import annotations

import importlib
import importlib.util
import sys
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
    spec = importlib.util.spec_from_file_location(f"startup_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Impossible de charger {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


def main() -> int:
    for filename in HOOKS:
        load_hook(filename)

    failures = 0
    for module_name in STARTUP_MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as err:
            failures += 1
            print(f"- {module_name}: {type(err).__name__}: {err}")
        else:
            print(f"- {module_name}: ok")

    if failures:
        print(f"\n{failures} module(s) du démarrage non importable(s).", file=sys.stderr)
        return 1
    print("\nGraphe d'imports du démarrage valide.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
