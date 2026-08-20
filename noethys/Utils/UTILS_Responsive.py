# -*- coding: utf-8 -*-
"""Adaptateur responsive desktop pour Noethys.

``UTILS_UIMetrics`` contient les métriques portables du produit. Ce module
ajoute uniquement les contraintes propres au client desktop wxPython : DPI,
largeur d'écran et paliers d'assets disponibles.
"""

from Utils import UTILS_UIMetrics


def GetFacteurEcran():
    facteur = 1.0

    try:
        import wx
        ppi = wx.GetDisplayPPI()
        ppi_x = float(ppi[0]) if ppi and ppi[0] else 96.0
        facteur = max(facteur, min(1.50, ppi_x / 96.0))
    except Exception:
        pass

    try:
        import wx
        largeur = int(wx.GetDisplaySize()[0])
        if largeur >= 3000:
            facteur = max(facteur, 1.32)
        elif largeur >= 1900:
            facteur = max(facteur, 1.16)
    except Exception:
        pass

    # L'échelle utilisateur appartient au design system commun. Le client
    # desktop ne la redéfinit plus avec sa propre clé de configuration.
    try:
        facteur = max(facteur, min(1.50, UTILS_UIMetrics.get_scale()))
    except Exception:
        pass

    return facteur


# Alias transitoire pour les appels introduits avant la stabilisation de l'API.
_facteur_ecran = GetFacteurEcran


def GetTailleIcone(base=16):
    """Retourne une taille d'asset par paliers disponibles sur desktop."""
    try:
        base = int(base)
    except (TypeError, ValueError):
        base = 16

    facteur = GetFacteurEcran()
    if base <= 16:
        if facteur >= 1.30:
            return 24
        if facteur >= 1.10:
            return 20
        return 16
    if base <= 24:
        if facteur >= 1.30:
            return 32
        return 24
    if base <= 32:
        if facteur >= 1.24:
            return 40
        return 32
    return min(48, max(base, int(round(base * min(facteur, 1.20)))))


def GetTailleCibleAction(base=40):
    """Cible desktop lisible, cohérente avec les métriques communes."""
    facteur = min(GetFacteurEcran(), 1.45)
    cible_desktop = int(round(base * facteur))
    cible_design = UTILS_UIMetrics.action_target("standard")
    return max(36, min(64, max(cible_desktop, cible_design)))


def AdapterTailleWx(taille):
    """Adapte un tuple/wx.Size carré demandé par une toolbar."""
    try:
        x, y = int(taille[0]), int(taille[1])
    except Exception:
        return taille
    if x != y or x not in (16, 20, 24, 32, 40, 48):
        return taille
    cible = GetTailleIcone(x)
    try:
        import wx
        return wx.Size(cible, cible)
    except Exception:
        return (cible, cible)
