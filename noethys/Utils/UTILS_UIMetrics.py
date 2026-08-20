#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Métriques d'interface communes à Noethys.

Ce module constitue la couche géométrique du design system. Les écrans ne
doivent plus déduire leur géométrie de constantes historiques isolées : ils
expriment une intention (icône, toolbar, ligne, espacement...) et cette couche
l'adapte à l'échelle choisie par l'utilisateur.

La définition est volontairement indépendante des widgets wxPython afin de
pouvoir être réutilisée comme spécification par d'autres clients Noethys.
"""

from __future__ import division

from Utils import UTILS_Config


def _echelle():
    try:
        valeur = int(UTILS_Config.GetParametre("interface_echelle", 100) or 100)
    except Exception:
        valeur = 100
    return max(80, min(200, valeur)) / 100.0


def px(valeur, minimum=1):
    """Retourne une métrique logique adaptée à l'échelle de l'interface."""
    return max(minimum, int(round(float(valeur) * _echelle())))


def spacing(niveau=2):
    """Grille d'espacement 4 px : 4, 8, 12, 16... avant mise à l'échelle."""
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


def toolbar_height(avec_libelle=True):
    """Hauteur dérivée du contenu : jamais indépendante de l'icône."""
    icone = icon_size("toolbar")
    texte = px(18) if avec_libelle else 0
    return icone + texte + spacing(3)


def command_height():
    return max(px(32), icon_size("command") + spacing(2))


def panel_min_height(contexte="secondary"):
    bases = {
        "compact": 72,
        "secondary": 96,
        "dashboard": 104,
    }
    return px(bases.get(contexte, 96))


def as_dict():
    """Expose les tokens géométriques pour diagnostic ou futur autre client."""
    return {
        "scale": _echelle(),
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
