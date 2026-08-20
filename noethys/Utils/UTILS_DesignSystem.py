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
- palette Repens Design plus sourde et plus adulte en sombre.
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
    "selection": wx.Colour(226, 230, 210),
    "selection_text": wx.Colour(48, 53, 35),
    "disabled": wx.Colour(235, 235, 235),
    "disabled_text": wx.Colour(145, 145, 145),
    "focus": wx.Colour(112, 96, 154),
    "success": wx.Colour(228, 232, 210),
    "success_text": wx.Colour(70, 77, 42),
    "warning": wx.Colour(246, 228, 201),
    "warning_text": wx.Colour(117, 75, 29),
    "danger": wx.Colour(235, 224, 239),
    "danger_text": wx.Colour(93, 63, 103),
    "info": wx.Colour(228, 224, 238),
    "info_text": wx.Colour(78, 65, 111),
}


# Repens Design sombre : graphite chaud, kaki/olive, ambre brûlé et prune.
# La profondeur vient d'abord de surfaces distinctes ; les accents restent
# suffisamment sourds pour cohabiter avec des tableaux très denses.
PALETTE_SOMBRE = {
    "surface": wx.Colour(22, 24, 26),
    "surface_container_lowest": wx.Colour(15, 17, 19),
    "surface_container_low": wx.Colour(28, 31, 33),
    "surface_container": wx.Colour(34, 38, 41),
    "surface_container_high": wx.Colour(43, 47, 51),
    "surface_container_highest": wx.Colour(53, 58, 63),
    "on_surface": wx.Colour(236, 234, 228),
    "on_surface_variant": wx.Colour(181, 178, 169),
    "outline": wx.Colour(94, 96, 93),
    "outline_variant": wx.Colour(55, 58, 57),
    "selection": wx.Colour(67, 74, 48),
    "selection_text": wx.Colour(240, 239, 222),
    "disabled": wx.Colour(42, 45, 47),
    "disabled_text": wx.Colour(122, 124, 121),
    "focus": wx.Colour(151, 137, 196),
    "success": wx.Colour(74, 82, 55),
    "success_text": wx.Colour(211, 219, 177),
    "warning": wx.Colour(104, 72, 35),
    "warning_text": wx.Colour(235, 181, 96),
    "danger": wx.Colour(84, 58, 87),
    "danger_text": wx.Colour(216, 190, 224),
    "info": wx.Colour(66, 59, 86),
    "info_text": wx.Colour(203, 191, 229),
}


ACCENTS_CLAIRS = {
    "Vert": {
        "primary": wx.Colour(104, 116, 66),
        "on_primary": wx.Colour(255, 255, 255),
        "primary_container": wx.Colour(230, 234, 214),
        "on_primary_container": wx.Colour(53, 61, 32),
    },
    "Bleu": {
        "primary": wx.Colour(88, 78, 128),
        "on_primary": wx.Colour(255, 255, 255),
        "primary_container": wx.Colour(232, 228, 241),
        "on_primary_container": wx.Colour(58, 49, 91),
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
        "primary": wx.Colour(164, 176, 113),
        "on_primary": wx.Colour(35, 40, 22),
        "primary_container": wx.Colour(67, 74, 48),
        "on_primary_container": wx.Colour(226, 231, 198),
    },
    "Bleu": {
        "primary": wx.Colour(161, 146, 205),
        "on_primary": wx.Colour(39, 32, 58),
        "primary_container": wx.Colour(71, 61, 94),
        "on_primary_container": wx.Colour(225, 216, 242),
    },
    "Noir": {
        "primary": wx.Colour(198, 199, 194),
        "on_primary": wx.Colour(43, 45, 46),
        "primary_container": wx.Colour(67, 70, 72),
        "on_primary_container": wx.Colour(236, 235, 231),
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
