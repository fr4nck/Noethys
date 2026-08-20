#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Métriques d'interface communes à Noethys.

Cette couche décrit la géométrie du design system. Les écrans expriment une
intention (icône, ligne, toolbar, espacement...) au lieu d'empiler des tailles
fixes. Les valeurs de référence sont indépendantes des widgets wxPython ; le
client desktop peut ensuite les adapter au DPI et à la plateforme.
"""

from __future__ import division

from Utils import UTILS_Config


ECHELLE_MIN = 80
ECHELLE_MAX = 200


def get_scale_percent():
    """Retourne l'échelle d'interface enregistrée, en pourcentage."""
    try:
        valeur = int(UTILS_Config.GetParametre("interface_echelle_pct", 100) or 100)
    except Exception:
        valeur = 100
    return max(ECHELLE_MIN, min(ECHELLE_MAX, valeur))


def get_scale():
    return get_scale_percent() / 100.0


def px(valeur, minimum=1):
    """Adapte une métrique de référence à l'échelle choisie."""
    return max(minimum, int(round(float(valeur) * get_scale())))


def spacing(niveau=2):
    """Grille d'espacement 4 px : 4, 8, 12, 16... à 100 %."""
    return px(max(1, int(niveau)) * 4)


def icon_size(contexte="toolbar"):
    bases = {
        "compact": 16,
        "inline": 20,
        "toolbar": 24,
        "command": 24,
        "hero": 32,
    }
    return px(bases.get(contexte, 24))


def row_height(contexte="list"):
    bases = {
        "compact": 24,
        "list": 28,
        "table": 28,
        "comfortable": 32,
    }
    return px(bases.get(contexte, 28))


def action_target(contexte="standard"):
    """Hauteur/cible minimale d'une commande desktop."""
    bases = {
        "compact": 32,
        "standard": 40,
        "comfortable": 44,
    }
    return px(bases.get(contexte, 40))


def toolbar_height(avec_libelle=True, icon_px=None):
    """Hauteur minimale dérivée du contenu de la toolbar.

    Même lorsqu'un backend affiche le texte à droite plutôt qu'en dessous, on
    conserve une cible suffisamment généreuse pour la lisibilité à distance et
    pour éviter les libellés rognés quand la police augmente.
    """
    if icon_px is None:
        icon_px = icon_size("toolbar")
    if avec_libelle:
        return max(px(48), int(icon_px) + spacing(4))
    return max(px(36), int(icon_px) + spacing(2))


def command_height():
    return max(action_target("standard"), icon_size("command") + spacing(2))


def panel_min_height(contexte="secondary"):
    bases = {
        "compact": 72,
        "secondary": 92,
        "dashboard": 104,
    }
    return px(bases.get(contexte, 92))


def as_dict():
    """Expose les tokens géométriques pour diagnostic ou autre client."""
    return {
        "scale_percent": get_scale_percent(),
        "scale": get_scale(),
        "spacing_1": spacing(1),
        "spacing_2": spacing(2),
        "spacing_3": spacing(3),
        "icon_inline": icon_size("inline"),
        "icon_toolbar": icon_size("toolbar"),
        "row_table": row_height("table"),
        "toolbar": toolbar_height(True),
        "command": command_height(),
        "panel_secondary": panel_min_height("secondary"),
    }
