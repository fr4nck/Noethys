#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Façade de style unique de Repens Design.

Ce module joue le rôle du « CSS Noethys » : les écrans métier ne doivent pas
connaître les RGB, rayons, tailles d'icônes, espacements ou détails de
fontes. Ils expriment uniquement une intention visuelle et consomment cette
API.

Les sources de vérité restent spécialisées :
- UTILS_DesignSystem : rôles sémantiques et palettes ;
- UTILS_UIMetrics    : métriques DPI / échelle ;
- UTILS_Interface    : préférences utilisateur et apparence active.

Cette façade est le point d'entrée recommandé pour les nouveaux composants et
les fenêtres migrées vers Repens Design.
"""

import wx

from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics


RAYONS = {
    "compact": 5,
    "controle": 7,
    "surface": 9,
    "dialogue": 12,
}

TYPOGRAPHIES = {
    "caption": {"delta": -1, "weight": wx.FONTWEIGHT_NORMAL},
    "body": {"delta": 0, "weight": wx.FONTWEIGHT_NORMAL},
    "body_emphasis": {"delta": 0, "weight": wx.FONTWEIGHT_BOLD},
    "section": {"delta": 1, "weight": wx.FONTWEIGHT_BOLD},
    "title": {"delta": 2, "weight": wx.FONTWEIGHT_BOLD},
}


def couleur(role="surface"):
    """Retourne une couleur sémantique de l'apparence active."""
    return UTILS_Interface.GetCouleurRole(role)


def espace(niveau=2):
    return UTILS_UIMetrics.spacing(niveau)


def px(valeur, minimum=1):
    return UTILS_UIMetrics.px(valeur, minimum=minimum)


def rayon(contexte="surface"):
    return px(RAYONS.get(contexte, RAYONS["surface"]))


def taille_icone(contexte="toolbar"):
    return UTILS_UIMetrics.icon_size(contexte)


def hauteur_ligne(contexte="list"):
    return UTILS_UIMetrics.row_height(contexte)


def cible_action(contexte="standard"):
    return UTILS_UIMetrics.action_target(contexte)


def hauteur_toolbar(avec_libelle=True):
    return UTILS_UIMetrics.toolbar_height(avec_libelle=avec_libelle)


def police(role="body"):
    """Construit une fonte système à partir d'un rôle typographique."""
    definition = TYPOGRAPHIES.get(role, TYPOGRAPHIES["body"])
    try:
        fonte = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
    except Exception:
        fonte = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)

    try:
        facteur_texte = UTILS_Interface.GetTailleTexte() / 100.0
        base = max(8, fonte.GetPointSize())
        taille = max(8, int(round((base + definition["delta"]) * facteur_texte)))
        fonte.SetPointSize(taille)
        poids = definition["weight"]
        if role == "section" and hasattr(wx, "FONTWEIGHT_SEMIBOLD"):
            poids = wx.FONTWEIGHT_SEMIBOLD
        fonte.SetWeight(poids)
    except Exception:
        pass
    return fonte


def appliquer_fenetre(fenetre, role_fond="surface"):
    """Applique le socle visuel commun à un Frame/Dialog/Panel."""
    try:
        fenetre.SetBackgroundColour(couleur(role_fond))
        fenetre.SetForegroundColour(couleur("on_surface"))
        fenetre.SetFont(police("body"))
    except Exception:
        pass
    return fenetre


def appliquer_texte(ctrl, role="body", role_texte="on_surface", role_fond=None):
    try:
        ctrl.SetFont(police(role))
        ctrl.SetForegroundColour(couleur(role_texte))
        if role_fond is not None:
            ctrl.SetBackgroundColour(couleur(role_fond))
    except Exception:
        pass
    return ctrl


def appliquer_saisie(ctrl):
    """Style commun des champs de saisie natifs conservés."""
    try:
        ctrl.SetFont(police("body"))
        ctrl.SetForegroundColour(couleur("on_surface"))
        ctrl.SetBackgroundColour(couleur("surface_container_lowest"))
        ctrl.SetMinSize((-1, cible_action("compact")))
    except Exception:
        pass
    return ctrl


def appliquer_liste(ctrl):
    """Style de base des listes/grilles lorsque leur renderer reste natif."""
    try:
        ctrl.SetFont(police("body"))
        ctrl.SetForegroundColour(couleur("on_surface"))
        ctrl.SetBackgroundColour(couleur("surface_container_lowest"))
    except Exception:
        pass
    return ctrl


def tokens():
    """Expose les tokens utiles pour diagnostic/tests sans dépendre d'un écran."""
    return {
        "surface": couleur("surface"),
        "surface_container": couleur("surface_container"),
        "surface_container_low": couleur("surface_container_low"),
        "on_surface": couleur("on_surface"),
        "outline_variant": couleur("outline_variant"),
        "primary": couleur("primary"),
        "spacing_1": espace(1),
        "spacing_2": espace(2),
        "spacing_3": espace(3),
        "radius_control": rayon("controle"),
        "radius_surface": rayon("surface"),
        "action_compact": cible_action("compact"),
        "action_standard": cible_action("standard"),
        "icon_toolbar": taille_icone("toolbar"),
    }
