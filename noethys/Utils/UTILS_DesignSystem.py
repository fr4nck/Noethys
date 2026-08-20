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


# Palette sombre cohérente avec le socle déjà introduit dans UTILS_Interface.
# Les valeurs sont légèrement amorties pour ne pas transformer les couleurs
# métier en aplats fluorescents.
PALETTE_SOMBRE = {
    "surface": wx.Colour(20, 18, 24),
    "surface_container_lowest": wx.Colour(15, 13, 19),
    "surface_container_low": wx.Colour(29, 27, 32),
    "surface_container": wx.Colour(33, 31, 38),
    "surface_container_high": wx.Colour(43, 41, 48),
    "surface_container_highest": wx.Colour(54, 52, 59),
    "on_surface": wx.Colour(230, 224, 233),
    "on_surface_variant": wx.Colour(202, 196, 208),
    "outline": wx.Colour(147, 143, 153),
    "outline_variant": wx.Colour(73, 69, 79),
    "selection": wx.Colour(55, 74, 48),
    "selection_text": wx.Colour(232, 247, 225),
    "disabled": wx.Colour(47, 45, 51),
    "disabled_text": wx.Colour(128, 123, 132),
    "focus": wx.Colour(169, 199, 255),
    "success": wx.Colour(47, 72, 47),
    "success_text": wx.Colour(204, 232, 201),
    "warning": wx.Colour(78, 68, 38),
    "warning_text": wx.Colour(240, 224, 174),
    "danger": wx.Colour(82, 47, 49),
    "danger_text": wx.Colour(245, 197, 199),
    "info": wx.Colour(42, 61, 79),
    "info_text": wx.Colour(196, 220, 244),
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
        "primary": wx.Colour(177, 214, 154),
        "on_primary": wx.Colour(34, 57, 23),
        "primary_container": wx.Colour(57, 81, 44),
        "on_primary_container": wx.Colour(205, 238, 181),
    },
    "Bleu": {
        "primary": wx.Colour(169, 199, 255),
        "on_primary": wx.Colour(0, 48, 92),
        "primary_container": wx.Colour(31, 71, 116),
        "on_primary_container": wx.Colour(213, 227, 255),
    },
    "Noir": {
        "primary": wx.Colour(202, 196, 208),
        "on_primary": wx.Colour(50, 47, 53),
        "primary_container": wx.Colour(73, 69, 79),
        "on_primary_container": wx.Colour(232, 222, 237),
    },
}


# Rôle de surface recommandé selon les grandes familles wxPython. Cette table
# constitue un contrat central ; elle évite d'ajouter des choix visuels locaux
# dans chaque dialogue.
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
    """Classe un contrôle wx dans une couche de surface sémantique."""
    nom = (nom_classe or "").lower()
    if any(mot in nom for mot in ("objectlistview", "listctrl", "listview", "grid")):
        return ROLES_COMPOSANTS["data"]
    if any(mot in nom for mot in ("textctrl", "treectrl", "choice", "combobox", "spin", "checklist")):
        return ROLES_COMPOSANTS["input"]
    if any(mot in nom for mot in ("toolbar", "auitoolbar", "notebook", "choicebook", "listbook")):
        return ROLES_COMPOSANTS["toolbar"]
    if any(mot in nom for mot in ("button", "togglebutton", "bitmapbutton")):
        return ROLES_COMPOSANTS["button"]
    if any(mot in nom for mot in ("popup", "popover", "tipwindow", "miniframe")):
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
