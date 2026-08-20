# -*- coding: utf-8 -*-
"""Rendu du pack générique à une taille responsive demandée."""

import os
import tempfile


def GetOverridePath(chemin, taille):
    try:
        from Utils import UTILS_Icones_modernes
    except Exception:
        return None

    try:
        icone = UTILS_Icones_modernes._icone_pour_chemin(chemin)
    except Exception:
        return None
    if icone is None:
        return None

    try:
        taille = int(taille)
    except (TypeError, ValueError):
        return None
    if taille not in (16, 20, 24, 28, 32, 36, 40, 48):
        return None

    dossier = os.path.join(tempfile.gettempdir(), "noethys-modern-icons-responsive-v1")
    destination = os.path.join(dossier, "%s-%d.png" % (icone, taille))
    if os.path.isfile(destination):
        return destination
    try:
        if UTILS_Icones_modernes._dessiner(icone, taille, destination):
            return destination
    except Exception:
        pass
    return None
