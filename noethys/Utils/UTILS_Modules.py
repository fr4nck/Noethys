#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Licence :        GNU GPL
#------------------------------------------------------------------------
"""Registre minimal des modules optionnels Noethys.

Un module désactivé ne doit ni importer son moteur lourd, ni lancer un timer,
ni ouvrir une connexion réseau. Ce registre ne fait que lire/écrire les flags.
"""

from Utils import UTILS_Config


MODULES = {
    "messagerie": {
        "parametre": "module_messagerie_actif",
        "defaut": False,
        "label": u"Messagerie",
    },
}


def GetDefinition(code):
    return MODULES.get(code)


def EstActif(code):
    definition = GetDefinition(code)
    if definition is None:
        return False
    return bool(
        UTILS_Config.GetParametre(
            definition["parametre"],
            defaut=definition.get("defaut", False),
        )
    )


def SetActif(code, actif=True):
    definition = GetDefinition(code)
    if definition is None:
        raise ValueError("Module Noethys inconnu : %s" % code)
    valeur = bool(actif)
    UTILS_Config.SetParametre(definition["parametre"], valeur)
    return valeur


def ListerModules():
    return sorted(MODULES.keys())
