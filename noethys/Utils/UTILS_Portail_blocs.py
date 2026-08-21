#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Licence:          GNU GPL
#------------------------------------------------------------------------

"""Registre léger des blocs enrichis du constructeur de pages Connecthys.

Les codes ``bloc_*`` ci-dessous sont des codes d'interface Noethys. Ils ne
créent aucune nouvelle catégorie persistante : les blocs enrichis sont encore
sauvegardés et exportés comme ``bloc_texte`` afin de préserver la compatibilité
avec Connecthys hébergé.

Ce registre permet surtout de conserver la philosophie du constructeur de
pages : chaque contenu reste un bloc indépendant, ajoutable, déplaçable,
dupliquable et supprimable séparément.
"""

from Utils import UTILS_Portail_contenus
from Utils import UTILS_Portail_tarifs_bloc


CODE_TEXTE = "bloc_texte"
CODE_CONTENU_EXTERNE = "bloc_contenu_externe"
CODE_TARIFS = "bloc_tarifs_noethys"

CODES_VIRTUELS = (CODE_CONTENU_EXTERNE, CODE_TARIFS)


def categorie_persistante(code):
    """Retourne la catégorie historique réellement enregistrée en base."""
    if code in CODES_VIRTUELS:
        return CODE_TEXTE
    return code


def detecter_code(dictParametres=None):
    """Retrouve le type d'éditeur d'un bloc texte enrichi existant."""
    dictParametres = dictParametres or {}
    categorie = dictParametres.get("categorie")
    if categorie != CODE_TEXTE:
        return categorie

    elements = dictParametres.get("elements") or []
    if not elements:
        return CODE_TEXTE
    parametres = elements[0].get("parametres")

    if UTILS_Portail_tarifs_bloc.est_configuration_bloc_tarifs(parametres):
        return CODE_TARIFS
    if UTILS_Portail_contenus.est_configuration_contenu_externe(parametres):
        return CODE_CONTENU_EXTERNE
    return CODE_TEXTE
