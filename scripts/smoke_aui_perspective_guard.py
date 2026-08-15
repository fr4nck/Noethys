#!/usr/bin/env python3
"""Vérifie le repli des perspectives AUI persistées devenues incompatibles."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))

from Utils.UTILS_Aui import ChargerPerspective


class Manager:
    def __init__(self, comportements):
        self.comportements = comportements
        self.appels = []

    def LoadPerspective(self, perspective):
        self.appels.append(perspective)
        comportement = self.comportements[perspective]
        if isinstance(comportement, BaseException):
            raise comportement
        return comportement


def main() -> int:
    manager = Manager({"ancienne": AssertionError("format ancien"), "defaut": True})
    if ChargerPerspective(manager, "ancienne", "defaut") is not True:
        raise RuntimeError("Le repli sur la perspective par défaut a échoué")
    if manager.appels != ["ancienne", "defaut"]:
        raise RuntimeError(f"Ordre de chargement inattendu : {manager.appels!r}")

    manager = Manager({"courante": True, "defaut": True})
    if ChargerPerspective(manager, "courante", "defaut") is not True:
        raise RuntimeError("Une perspective valide est refusée")
    if manager.appels != ["courante"]:
        raise RuntimeError("Le fallback a été utilisé sans nécessité")

    manager = Manager({"defaut": True})
    if ChargerPerspective(manager, None, "defaut") is not True:
        raise RuntimeError("Une perspective absente ne retombe pas sur le défaut")

    manager = Manager({"ancienne": False, "defaut": True})
    if ChargerPerspective(manager, "ancienne", "defaut") is not True:
        raise RuntimeError("Un échec booléen de LoadPerspective ne déclenche pas le repli")

    print("Repli des perspectives AUI : OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
