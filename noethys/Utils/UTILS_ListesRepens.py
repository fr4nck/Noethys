# -*- coding: utf-8 -*-
"""Style commun, opt-in, des ListCtrl/ObjectListView modernisées."""

from Utils import UTILS_Interface


def Configurer(ctrl):
    if ctrl is None:
        return False
    fond = UTILS_Interface.GetCouleurRole("surface_container_lowest")
    texte = UTILS_Interface.GetCouleurRole("on_surface")
    try:
        ctrl.SetBackgroundColour(fond)
        ctrl.SetForegroundColour(texte)
    except Exception:
        pass
    try:
        ctrl.GetMainWindow().SetBackgroundColour(fond)
        ctrl.GetMainWindow().SetForegroundColour(texte)
    except Exception:
        pass
    try:
        ctrl.stEmptyListMsg.SetBackgroundColour(fond)
        ctrl.stEmptyListMsg.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface_variant"))
    except Exception:
        pass
    try:
        ctrl.Refresh()
    except Exception:
        pass
    return True
