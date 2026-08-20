#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import os, re, sys

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


def _TailleIconeDemandee(fichier, taille=None):
    if taille is not None:
        try:
            return int(taille)
        except (TypeError, ValueError):
            return None
    normalise = (fichier or "").replace("\\", "/")
    match = re.search(r"Images/(16|20|24|32|40|48)x\1/", normalise)
    if not match:
        return None
    base = int(match.group(1))
    try:
        from Utils import UTILS_Responsive
        return UTILS_Responsive.GetTailleIcone(base)
    except Exception:
        return base


def _GetIconeModerne(fichier, taille=None):
    """Retourne un pictogramme moderne connu, sinon None."""
    if not fichier:
        return None
    if os.environ.get("NOETHYS_LEGACY_ICONS", "").strip().lower() in ("1", "true", "yes", "oui"):
        return None

    normalise = fichier.replace("\\", "/")
    dossiers = (
        "Images/16x16/", "Images/20x20/", "Images/24x24/",
        "Images/32x32/", "Images/40x40/", "Images/48x48/",
    )
    if not normalise.startswith(dossiers):
        return None

    taille_cible = _TailleIconeDemandee(normalise, taille=taille)

    try:
        from Utils import UTILS_Icones_identites
        resultat = UTILS_Icones_identites.GetLegacyOverridePath(normalise, taille=taille_cible)
        if resultat:
            return resultat
    except Exception:
        pass

    try:
        from Utils import UTILS_Icones_adaptatives
        resultat = UTILS_Icones_adaptatives.GetOverridePath(normalise, taille_cible)
        if resultat:
            return resultat
    except Exception:
        pass

    try:
        from Utils import UTILS_Icones_modernes
        return UTILS_Icones_modernes.GetLegacyOverridePath(normalise, taille=taille_cible)
    except Exception:
        return None


def GetStaticIconPath(fichier="", taille=None):
    """Retourne une ressource d'icône, avec taille de rendu optionnelle."""
    chemin = os.path.join(REP_COURANT, "Static")
    icone_moderne = _GetIconeModerne(fichier, taille=taille)
    if icone_moderne:
        return icone_moderne
    return os.path.join(chemin, fichier)


def GetStaticPath(fichier=""):
    """ Retourne le chemin du répertoire Static """
    return GetStaticIconPath(fichier)


def GetMainPath(fichier=""):
    """ Retourne le chemin du répertoire principal """
    return os.path.join(REP_COURANT, fichier)
