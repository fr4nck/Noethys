#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Licence :        GNU GPL
#------------------------------------------------------------------------
"""Contrat sémantique UI/UX commun à Noethys.

Ce module complète ``UTILS_Interface`` sans remplacer les thèmes historiques.
Il définit le vocabulaire stable que les composants transversaux doivent
progressivement consommer : surfaces, textes, accents et états interactifs.

Principes :
- Fluent 2 pour la grammaire desktop et les états interactifs ;
- Material Design 3 pour les rôles sémantiques et la hiérarchie des surfaces ;
- effets de profondeur réservés aux couches fonctionnelles ;
- palette Repens Design issue directement du mockup de référence.
"""

import wx


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


# Version claire : les teintes sont celles du concept Repens, avec des fonds
# très neutres pour que les tables métier restent prioritaires.
PALETTE_CLAIRE = {
    "surface": wx.Colour(248, 249, 248),
    "surface_container_lowest": wx.Colour(255, 255, 255),
    "surface_container_low": wx.Colour(246, 247, 246),
    "surface_container": wx.Colour(240, 242, 240),
    "surface_container_high": wx.Colour(233, 236, 233),
    "surface_container_highest": wx.Colour(224, 228, 224),
    "on_surface": wx.Colour(31, 34, 31),
    "on_surface_variant": wx.Colour(83, 87, 82),
    "outline": wx.Colour(124, 130, 123),
    "outline_variant": wx.Colour(207, 212, 206),
    "selection": wx.Colour(221, 231, 200),
    "selection_text": wx.Colour(47, 58, 35),
    "disabled": wx.Colour(235, 236, 234),
    "disabled_text": wx.Colour(145, 148, 143),
    "focus": wx.Colour(54, 137, 55),
    "success": wx.Colour(221, 231, 200),
    "success_text": wx.Colour(62, 83, 45),
    "warning": wx.Colour(250, 239, 209),
    "warning_text": wx.Colour(126, 85, 35),
    "danger": wx.Colour(239, 224, 241),
    "danger_text": wx.Colour(112, 63, 119),
    "info": wx.Colour(222, 235, 244),
    "info_text": wx.Colour(35, 91, 130),
}


# Repens sombre : mêmes familles chromatiques que le mockup, simplement
# assourdies pour une interface dense. Pas de noir pur ni de couleurs fluo.
PALETTE_SOMBRE = {
    "surface": wx.Colour(23, 25, 25),
    "surface_container_lowest": wx.Colour(16, 18, 18),
    "surface_container_low": wx.Colour(29, 32, 31),
    "surface_container": wx.Colour(35, 39, 38),
    "surface_container_high": wx.Colour(44, 49, 47),
    "surface_container_highest": wx.Colour(54, 60, 57),
    "on_surface": wx.Colour(236, 237, 233),
    "on_surface_variant": wx.Colour(181, 185, 177),
    "outline": wx.Colour(94, 101, 94),
    "outline_variant": wx.Colour(55, 61, 57),
    "selection": wx.Colour(70, 79, 49),
    "selection_text": wx.Colour(240, 242, 224),
    "disabled": wx.Colour(42, 46, 44),
    "disabled_text": wx.Colour(123, 127, 121),
    "focus": wx.Colour(108, 164, 111),
    "success": wx.Colour(73, 82, 53),
    "success_text": wx.Colour(210, 221, 177),
    "warning": wx.Colour(104, 78, 45),
    "warning_text": wx.Colour(222, 177, 108),
    "danger": wx.Colour(82, 53, 87),
    "danger_text": wx.Colour(215, 188, 221),
    "info": wx.Colour(37, 70, 90),
    "info_text": wx.Colour(181, 207, 226),
}


# Les noms historiques de thèmes restent compatibles, mais leurs teintes sont
# désormais celles de Repens Design.
ACCENTS_CLAIRS = {
    "Vert": {
        "primary": wx.Colour(54, 137, 55),
        "on_primary": wx.Colour(255, 255, 255),
        "primary_container": wx.Colour(221, 231, 200),
        "on_primary_container": wx.Colour(45, 74, 39),
    },
    "Bleu": {
        "primary": wx.Colour(28, 98, 146),
        "on_primary": wx.Colour(255, 255, 255),
        "primary_container": wx.Colour(222, 235, 244),
        "on_primary_container": wx.Colour(27, 72, 104),
    },
    "Noir": {
        "primary": wx.Colour(136, 52, 143),
        "on_primary": wx.Colour(255, 255, 255),
        "primary_container": wx.Colour(239, 224, 241),
        "on_primary_container": wx.Colour(92, 49, 98),
    },
}

ACCENTS_SOMBRES = {
    "Vert": {
        "primary": wx.Colour(108, 164, 111),
        "on_primary": wx.Colour(21, 48, 27),
        "primary_container": wx.Colour(62, 89, 61),
        "on_primary_container": wx.Colour(218, 233, 202),
    },
    "Bleu": {
        "primary": wx.Colour(93, 151, 188),
        "on_primary": wx.Colour(20, 44, 60),
        "primary_container": wx.Colour(37, 70, 90),
        "on_primary_container": wx.Colour(205, 226, 239),
    },
    "Noir": {
        "primary": wx.Colour(169, 126, 174),
        "on_primary": wx.Colour(52, 31, 55),
        "primary_container": wx.Colour(82, 53, 87),
        "on_primary_container": wx.Colour(231, 210, 234),
    },
}


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
    """Retourne les rôles utiles pour dessiner un état interactif cohérent."""
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
