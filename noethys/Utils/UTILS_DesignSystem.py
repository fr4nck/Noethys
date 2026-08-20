#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Licence :        GNU GPL
#------------------------------------------------------------------------
"""Contrat sémantique UI/UX commun à Noethys.

Ce module complète ``UTILS_Interface`` sans remplacer les thèmes historiques.
Il définit le vocabulaire stable que les composants transversaux doivent
progressivement consommer : surfaces, textes, accents, états interactifs et
couleurs métier.

Principes :
- Fluent 2 pour la grammaire desktop et les états interactifs ;
- Material Design 3 pour les rôles sémantiques et la hiérarchie des surfaces ;
- effets de profondeur réservés aux couches fonctionnelles ;
- compatibilité avec Vert / Bleu / Noir et avec les écrans historiques.
"""

import wx


# Rôles publics. Un écran métier ne devrait pas inventer un nouveau nom de
# couleur quand l'un de ces rôles exprime déjà son intention.
ROLES = (
    "surface",
    "surface_container_lowest",
    "surface_container_low",
    "surface_container",
    "surface_container_high",
    "surface_container_highest",
    "on_surface",
    "on_surface_variant",
    "primary",
    "on_primary",
    "primary_container",
    "on_primary_container",
    "outline",
    "outline_variant",
    "selection",
    "selection_text",
    "disabled",
    "disabled_text",
    "focus",
    "success",
    "success_text",
    "warning",
    "warning_text",
    "danger",
    "danger_text",
    "info",
    "info_text",
)

ETATS_INTERACTIFS = (
    "normal",
    "hover",
    "focus",
    "pressed",
    "selected",
    "disabled",
    "error",
)


# Palette claire volontairement neutre. L'accent reste fourni par le thème
# historique afin de ne pas changer l'identité des installations existantes.
PALETTE_CLAIRE = {
    "surface": wx.Colour(248, 249, 250),
    "surface_container_lowest": wx.Colour(255, 255, 255),
    "surface_container_low": wx.Colour(246, 247, 248),
    "surface_container": wx.Colour(240, 242, 244),
    "surface_container_high": wx.Colour(233, 235, 238),
    "surface_container_highest": wx.Colour(225, 228, 232),
    "on_surface": wx.Colour(31, 31, 31),
    "on_surface_variant": wx.Colour(82, 82, 82),
    "outline": wx.Colour(124, 124, 124),
    "outline_variant": wx.Colour(207, 207, 207),
    "selection": wx.Colour(218, 235, 210),
    "selection_text": wx.Colour(29, 48, 24),
    "disabled": wx.Colour(235, 235, 235),
    "disabled_text": wx.Colour(145, 145, 145),
    "focus": wx.Colour(0, 95, 184),
    "success": wx.Colour(224, 242, 221),
    "success_text": wx.Colour(37, 87, 35),
    "warning": wx.Colour(250, 238, 202),
    "warning_text": wx.Colour(103, 76, 0),
    "danger": wx.Colour(250, 222, 222),
    "danger_text": wx.Colour(128, 38, 38),
    "info": wx.Colour(224, 236, 248),
    "info_text": wx.Colour(33, 70, 110),
}


# Palette sombre graphite. On évite volontairement le noir pur et les traits
# très lumineux : la profondeur vient de surfaces proches mais distinctes,
# comme dans les outils métier modernes. Les couleurs d'état restent
# désaturées afin de conserver la lisibilité des informations métier.
PALETTE_SOMBRE = {
    "surface": wx.Colour(24, 27, 31),
    "surface_container_lowest": wx.Colour(19, 22, 25),
    "surface_container_low": wx.Colour(28, 32, 37),
    "surface_container": wx.Colour(33, 38, 44),
    "surface_container_high": wx.Colour(41, 47, 54),
    "surface_container_highest": wx.Colour(50, 57, 65),
    "on_surface": wx.Colour(232, 235, 239),
    "on_surface_variant": wx.Colour(174, 181, 190),
    "outline": wx.Colour(92, 101, 112),
    "outline_variant": wx.Colour(52, 59, 67),
    "selection": wx.Colour(36, 67, 52),
    "selection_text": wx.Colour(234, 245, 238),
    "disabled": wx.Colour(39, 44, 50),
    "disabled_text": wx.Colour(118, 126, 136),
    "focus": wx.Colour(112, 169, 235),
    "success": wx.Colour(31, 72, 49),
    "success_text": wx.Colour(175, 226, 194),
    "warning": wx.Colour(79, 63, 27),
    "warning_text": wx.Colour(240, 215, 145),
    "danger": wx.Colour(81, 42, 48),
    "danger_text": wx.Colour(240, 181, 189),
    "info": wx.Colour(31, 59, 83),
    "info_text": wx.Colour(170, 207, 239),
}


ACCENTS_CLAIRS = {
    "Vert": {
        "primary": wx.Colour(79, 128, 54),
        "on_primary": wx.Colour(255, 255, 255),
        "primary_container": wx.Colour(220, 239, 209),
        "on_primary_container": wx.Colour(35, 67, 24),
    },
    "Bleu": {
        "primary": wx.Colour(0, 103, 180),
        "on_primary": wx.Colour(255, 255, 255),
        "primary_container": wx.Colour(218, 233, 250),
        "on_primary_container": wx.Colour(0, 54, 101),
    },
    "Noir": {
        "primary": wx.Colour(78, 78, 78),
        "on_primary": wx.Colour(255, 255, 255),
        "primary_container": wx.Colour(231, 231, 231),
        "on_primary_container": wx.Colour(47, 47, 47),
    },
}

ACCENTS_SOMBRES = {
    "Vert": {
        "primary": wx.Colour(126, 211, 159),
        "on_primary": wx.Colour(14, 45, 28),
        "primary_container": wx.Colour(36, 77, 52),
        "on_primary_container": wx.Colour(199, 239, 213),
    },
    "Bleu": {
        "primary": wx.Colour(123, 183, 238),
        "on_primary": wx.Colour(13, 47, 76),
        "primary_container": wx.Colour(37, 72, 103),
        "on_primary_container": wx.Colour(205, 229, 250),
    },
    "Noir": {
        "primary": wx.Colour(195, 201, 209),
        "on_primary": wx.Colour(42, 47, 53),
        "primary_container": wx.Colour(64, 71, 79),
        "on_primary_container": wx.Colour(234, 237, 241),
    },
}


# Rôle de surface recommandé selon les grandes familles wxPython et les noms de
# modules historiques Noethys. Les contrôles maison s'appellent souvent CTRL :
# le nom qualifié du module devient donc une information utile à la classification.
ROLES_COMPOSANTS = {
    "data": "surface_container_lowest",
    "input": "surface_container_low",
    "panel": "surface",
    "toolbar": "surface_container",
    "button": "surface_container_high",
    "floating": "surface_container_highest",
}


def NormaliserTheme(theme):
    return theme if theme in ACCENTS_CLAIRS else "Vert"


def GetPalette(sombre=False):
    return PALETTE_SOMBRE if sombre else PALETTE_CLAIRE


def GetCouleur(role, sombre=False, theme="Vert", defaut=None):
    """Retourne la couleur d'un rôle sans dépendre d'un écran particulier."""
    theme = NormaliserTheme(theme)
    accents = ACCENTS_SOMBRES if sombre else ACCENTS_CLAIRS
    if role in accents[theme]:
        return accents[theme][role]
    palette = GetPalette(sombre)
    if role in palette:
        return palette[role]
    return defaut


def GetRoleComposant(nom_classe=""):
    """Classe un contrôle wx ou Noethys dans une couche de surface sémantique."""
    nom = (nom_classe or "").lower()
    if any(mot in nom for mot in (
        "objectlistview", "listctrl", "listview", "dataview", "grid", "grille"
    )):
        return ROLES_COMPOSANTS["data"]
    if any(mot in nom for mot in (
        "textctrl", "treectrl", "choice", "combobox", "spin", "checklist",
        "searchctrl", "datectrl", "saisie"
    )):
        return ROLES_COMPOSANTS["input"]
    if any(mot in nom for mot in (
        "toolbar", "auitoolbar", "notebook", "choicebook", "listbook", "barre_outils"
    )):
        return ROLES_COMPOSANTS["toolbar"]
    if any(mot in nom for mot in (
        "button", "togglebutton", "bitmapbutton", "bouton"
    )):
        return ROLES_COMPOSANTS["button"]
    if any(mot in nom for mot in (
        "popup", "popover", "tipwindow", "miniframe"
    )):
        return ROLES_COMPOSANTS["floating"]
    return ROLES_COMPOSANTS["panel"]


def GetEtatCouleurs(etat="normal", sombre=False, theme="Vert"):
    """Retourne les rôles utiles pour dessiner un état interactif cohérent.

    La fonction reste volontairement simple : les contrôles natifs gardent leur
    comportement natif lorsque celui-ci est meilleur. Ce contrat sert surtout
    aux contrôles personnalisés Noethys.
    """
    if etat not in ETATS_INTERACTIFS:
        etat = "normal"

    if etat == "disabled":
        return {
            "background": GetCouleur("disabled", sombre, theme),
            "foreground": GetCouleur("disabled_text", sombre, theme),
            "outline": GetCouleur("outline_variant", sombre, theme),
        }
    if etat == "selected":
        return {
            "background": GetCouleur("selection", sombre, theme),
            "foreground": GetCouleur("selection_text", sombre, theme),
            "outline": GetCouleur("primary", sombre, theme),
        }
    if etat == "error":
        return {
            "background": GetCouleur("danger", sombre, theme),
            "foreground": GetCouleur("danger_text", sombre, theme),
            "outline": GetCouleur("danger_text", sombre, theme),
        }
    if etat == "focus":
        return {
            "background": GetCouleur("surface_container_low", sombre, theme),
            "foreground": GetCouleur("on_surface", sombre, theme),
            "outline": GetCouleur("focus", sombre, theme),
        }
    if etat == "pressed":
        return {
            "background": GetCouleur("primary_container", sombre, theme),
            "foreground": GetCouleur("on_primary_container", sombre, theme),
            "outline": GetCouleur("primary", sombre, theme),
        }
    if etat == "hover":
        return {
            "background": GetCouleur("surface_container_high", sombre, theme),
            "foreground": GetCouleur("on_surface", sombre, theme),
            "outline": GetCouleur("outline", sombre, theme),
        }
    return {
        "background": GetCouleur("surface_container_low", sombre, theme),
        "foreground": GetCouleur("on_surface", sombre, theme),
        "outline": GetCouleur("outline_variant", sombre, theme),
    }
