#!/usr/bin/env python3
"""Vérifie le repli des perspectives AUI persistées devenues incompatibles."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))

from Utils import UTILS_Aui


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


def _charger_version_valide(manager, perspective, fallback=None):
    """Isole ici le contrat de chargement d'une génération AUI courante."""
    verifier = UTILS_Aui.VerifierVersionPerspective
    try:
        UTILS_Aui.VerifierVersionPerspective = lambda _manager: True
        return UTILS_Aui.ChargerPerspective(manager, perspective, fallback)
    finally:
        UTILS_Aui.VerifierVersionPerspective = verifier


def _charger_version_obsolete(manager, perspective, fallback=None):
    """Simule une perspective d'une génération précédente sans état utilisateur."""
    verifier = UTILS_Aui.VerifierVersionPerspective
    try:
        UTILS_Aui.VerifierVersionPerspective = lambda _manager: False
        return UTILS_Aui.ChargerPerspective(manager, perspective, fallback)
    finally:
        UTILS_Aui.VerifierVersionPerspective = verifier


def main() -> int:
    manager = Manager({"ancienne": AssertionError("format ancien"), "defaut": True})
    if _charger_version_valide(manager, "ancienne", "defaut") is not True:
        raise RuntimeError("Le repli sur la perspective par défaut a échoué")
    if manager.appels != ["ancienne", "defaut"]:
        raise RuntimeError(f"Ordre de chargement inattendu : {manager.appels!r}")

    manager = Manager({"courante": True, "defaut": True})
    if _charger_version_valide(manager, "courante", "defaut") is not True:
        raise RuntimeError("Une perspective valide est refusée")
    if manager.appels != ["courante"]:
        raise RuntimeError("Le fallback a été utilisé sans nécessité")

    manager = Manager({"defaut": True})
    if _charger_version_valide(manager, None, "defaut") is not True:
        raise RuntimeError("Une perspective absente ne retombe pas sur le défaut")

    manager = Manager({"ancienne": False, "defaut": True})
    if _charger_version_valide(manager, "ancienne", "defaut") is not True:
        raise RuntimeError("Un échec booléen de LoadPerspective ne déclenche pas le repli")

    # Une génération explicitement obsolète ne doit même plus être présentée à
    # wxAUI : on charge directement la perspective par défaut connue compatible.
    manager = Manager({"ancienne": AssertionError("ne doit pas être chargée"), "defaut": True})
    if _charger_version_obsolete(manager, "ancienne", "defaut") is not True:
        raise RuntimeError("Une ancienne génération ne retombe pas sur le défaut")
    if manager.appels != ["defaut"]:
        raise RuntimeError(f"Perspective obsolète chargée à tort : {manager.appels!r}")

    print("Repli des perspectives AUI : OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
