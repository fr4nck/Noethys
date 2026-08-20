# -*- coding: utf-8 -*-
"""Helpers Repens pour les ``HyperTreeList`` historiques de Noethys.

Le composant reste un contrôle desktop dense. On ne remplace pas son modèle de
données : on lui donne une surface sémantique, des métriques DPI et une colonne
texte qui absorbe la largeur disponible au lieu de laisser un grand vide.
"""

import wx

from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics


def Configurer(ctrl, largeurs_numeriques):
    if ctrl is None:
        return False
    ctrl._repens_largeurs_numeriques = tuple(largeurs_numeriques or ())
    try:
        ctrl.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
        ctrl.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
    except Exception:
        pass
    try:
        ctrl.GetMainWindow().SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
        ctrl.GetMainWindow().SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
    except Exception:
        pass

    if not getattr(ctrl, "_repens_resize_installe", False):
        ctrl._repens_resize_installe = True
        try:
            ctrl.Bind(wx.EVT_SIZE, lambda event: _OnSize(ctrl, event))
        except Exception:
            pass
    wx.CallAfter(AjusterColonnes, ctrl)
    return True


def _OnSize(ctrl, event):
    event.Skip()
    if getattr(ctrl, "_repens_resize_pending", False):
        return
    ctrl._repens_resize_pending = True

    def Appliquer():
        ctrl._repens_resize_pending = False
        AjusterColonnes(ctrl)

    wx.CallAfter(Appliquer)


def AjusterColonnes(ctrl):
    """Donne l'espace libre à la première colonne textuelle."""
    try:
        total = int(ctrl.GetClientSize().GetWidth())
    except Exception:
        return False
    if total <= 100:
        return False

    specs = getattr(ctrl, "_repens_largeurs_numeriques", ())
    fixes = []
    for largeur in specs:
        fixes.append(UTILS_UIMetrics.px(largeur))

    marge = UTILS_UIMetrics.px(28)
    minimum_texte = UTILS_UIMetrics.px(210)
    largeur_texte = max(minimum_texte, total - sum(fixes) - marge)
    try:
        ctrl.SetColumnWidth(0, largeur_texte)
        for index, largeur in enumerate(fixes, start=1):
            ctrl.SetColumnWidth(index, largeur)
    except Exception:
        return False
    return True


def CouleurEtat(etat):
    roles = {
        "success": "success",
        "warning": "warning",
        "danger": "danger",
        "info": "info",
        "group": "surface_container_high",
        "date": "surface_container_low",
        "neutral": "surface_container_lowest",
    }
    return UTILS_Interface.GetCouleurRole(roles.get(etat, "surface_container_lowest"))


def CouleurTexte(etat):
    roles = {
        "success": "success_text",
        "warning": "warning_text",
        "danger": "danger_text",
        "info": "info_text",
        "group": "on_surface",
        "date": "on_surface",
        "neutral": "on_surface",
    }
    return UTILS_Interface.GetCouleurRole(roles.get(etat, "on_surface"))
