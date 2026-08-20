#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import os, sys

frozen = getattr(sys, 'frozen', '')
if not frozen:
    REP_COURANT = os.path.dirname(os.path.abspath(__file__))
else :
    REP_COURANT = os.path.dirname(sys.executable)

if REP_COURANT not in sys.path :
    sys.path.insert(1, REP_COURANT)

for rep in os.listdir(REP_COURANT) :
    chemin = os.path.join(REP_COURANT, rep)
    if os.path.isdir(chemin) and chemin not in sys.path :
        sys.path.insert(2, chemin)


def _GetIconeModerne(fichier):
    """Substitution prudente des vieux pictos d'interface 16/32 px.

    Tout fichier non reconnu, toute erreur de génération ou l'activation de
    NOETHYS_LEGACY_ICONS laisse strictement fonctionner la ressource historique.
    """
    if not fichier:
        return None
    if os.environ.get("NOETHYS_LEGACY_ICONS", "").strip().lower() in ("1", "true", "yes", "oui"):
        return None

    normalise = fichier.replace("\\", "/")
    if not (
        normalise.startswith("Images/16x16/")
        or normalise.startswith("Images/32x32/")
    ):
        return None

    try:
        from Utils import UTILS_Icones_modernes
        return UTILS_Icones_modernes.GetLegacyOverridePath(normalise)
    except Exception:
        return None


def GetStaticPath(fichier=""):
    """ Retourne le chemin du répertoire Static """
    chemin = os.path.join(REP_COURANT, "Static")
    icone_moderne = _GetIconeModerne(fichier)
    if icone_moderne:
        return icone_moderne
    return os.path.join(chemin, fichier)


def GetMainPath(fichier=""):
    """ Retourne le chemin du répertoire principal """
    return os.path.join(REP_COURANT, fichier)