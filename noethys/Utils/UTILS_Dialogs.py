#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import os.path
import wx

from Utils import UTILS_Config
from Utils import UTILS_UIMetrics



def GetNomModule(chemin_module=""):
    nom_module = os.path.basename(chemin_module)
    for extension in (".pyc", ".py"):
        nom_module = nom_module.replace(extension, "")
    return nom_module


def _GetZoneTravail(parent=None):
    """Retourne la zone utile de l'écran portant la fenêtre."""
    try:
        index = wx.Display.GetFromWindow(parent) if parent is not None else wx.NOT_FOUND
        if index != wx.NOT_FOUND:
            zone = wx.Display(index).GetClientArea()
            if zone.GetWidth() > 0 and zone.GetHeight() > 0:
                return zone
    except Exception:
        pass
    try:
        zone = wx.GetClientDisplayRect()
        if zone.GetWidth() > 0 and zone.GetHeight() > 0:
            return zone
    except Exception:
        pass
    return wx.Rect(0, 0, 1280, 800)


def _LimiterTaille(parent, taille=None):
    """Borne une taille aux capacités réelles de l'écran courant.

    Les vieux dialogues peuvent encore annoncer un ``SetMinSize((940, 700))``.
    Sur un petit écran ou avec une échelle élevée, ce minimum ne doit pas rendre
    les boutons inaccessibles. On réduit donc seulement les minima qui excèdent
    la zone de travail ; les minima métier raisonnables restent intacts.
    """
    if parent is None:
        return None

    zone = _GetZoneTravail(parent)
    marge = UTILS_UIMetrics.spacing(4)
    largeur_max = max(UTILS_UIMetrics.px(320), int(zone.GetWidth()) - (marge * 2))
    hauteur_max = max(UTILS_UIMetrics.px(240), int(zone.GetHeight()) - (marge * 2))

    try:
        minimum = parent.GetMinSize()
        min_w = int(minimum.GetWidth())
        min_h = int(minimum.GetHeight())
        nouveau_min_w = min(min_w, largeur_max) if min_w > 0 else min_w
        nouveau_min_h = min(min_h, hauteur_max) if min_h > 0 else min_h
        if (nouveau_min_w, nouveau_min_h) != (min_w, min_h):
            parent.SetMinSize((nouveau_min_w, nouveau_min_h))
    except Exception:
        nouveau_min_w = nouveau_min_h = -1

    if taille is None:
        try:
            taille = parent.GetSize()
        except Exception:
            return None

    try:
        largeur = int(taille[0])
        hauteur = int(taille[1])
    except Exception:
        try:
            largeur = int(taille.GetWidth())
            hauteur = int(taille.GetHeight())
        except Exception:
            return None

    if largeur <= 0:
        largeur = min(UTILS_UIMetrics.px(720), largeur_max)
    if hauteur <= 0:
        hauteur = min(UTILS_UIMetrics.px(520), hauteur_max)

    if nouveau_min_w > 0:
        largeur = max(largeur, nouveau_min_w)
    if nouveau_min_h > 0:
        hauteur = max(hauteur, nouveau_min_h)

    largeur = min(largeur, largeur_max)
    hauteur = min(hauteur, hauteur_max)
    return (largeur, hauteur)


def AjusteDansEcran(parent=None, taille=None, centrer=False):
    """Applique une taille sûre sans modifier la logique métier du dialogue."""
    taille = _LimiterTaille(parent, taille=taille)
    if parent is None or taille is None:
        return False
    try:
        parent.SetSize(taille)
    except Exception:
        return False
    if centrer:
        try:
            if parent.GetParent() is not None:
                parent.CentreOnParent()
            else:
                parent.CentreOnScreen()
        except Exception:
            pass
    return True


def AjusteSizePerso(parent=None, chemin_module=""):
    """Restaure la taille utilisateur tout en garantissant une fenêtre accessible."""
    if parent is None:
        return
    nom_module = GetNomModule(chemin_module)
    taille_fenetre = UTILS_Config.GetParametre(nom_module)
    if taille_fenetre is not None:
        if taille_fenetre == (0, 0) or taille_fenetre == [0, 0]:
            try:
                parent.Maximize(True)
            except Exception:
                pass
            return
        AjusteDansEcran(parent, taille=taille_fenetre)
        return

    # Même sans préférence sauvegardée, corrige les tailles historiques qui
    # dépassent l'écran actuel.
    AjusteDansEcran(parent)


def SaveSizePerso(parent=None, chemin_module=""):
    """Mémorise la taille de la fenêtre."""
    if parent is None:
        return
    nom_module = GetNomModule(chemin_module)
    if parent.IsMaximized() is True:
        taille_fenetre = (0, 0)
    else:
        taille_fenetre = tuple(parent.GetSize())
    UTILS_Config.SetParametre(nom_module, taille_fenetre)


if __name__ == "__main__":
    pass
