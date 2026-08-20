#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Licence:          GNU GPL
#------------------------------------------------------------------------

"""Actualisation des contenus dynamiques avant export Connecthys.

Le module reste séparé de ``UTILS_Portail_synchro`` afin de pouvoir tester la
politique de cache et de panne réseau sans démarrer le moteur complet de
synchronisation.
"""

from Utils import UTILS_Portail_contenus


def _log(log, message):
    try:
        log.EcritLog(message)
    except Exception:
        pass


def actualiser(DB, log=None, constructeur=None):
    """Actualise les blocs dynamiques et leur cache HTML local.

    Le commit reste volontairement à la charge de l'appelant. En cas d'échec
    d'un flux, le ``texte_html`` existant n'est jamais modifié : le dernier
    rendu valide reste donc disponible pour l'export suivant.

    Retourne un état exploitable par le moteur principal : ``present`` permet
    de forcer l'export des pages à chaque synchronisation.
    """
    constructeur = constructeur or UTILS_Portail_contenus.construire_html
    etat = {"present": False, "modifies": 0, "erreurs": 0}

    req = """SELECT IDelement, parametres, texte_html
    FROM portail_elements
    WHERE parametres IS NOT NULL;"""
    if not DB.ExecuterReq(req):
        return etat

    for IDelement, parametres, texte_html in DB.ResultatReq():
        if not UTILS_Portail_contenus.est_configuration_dynamique(parametres):
            continue

        etat["present"] = True
        config = UTILS_Portail_contenus.deserialiser_parametres(parametres)
        try:
            nouveau_html = constructeur(config)
        except Exception as err:
            etat["erreurs"] += 1
            _log(log, u"[AVERTISSEMENT] Flux RSS/Atom indisponible (%s). Dernière version conservée." % err)
            continue

        if isinstance(texte_html, bytes):
            texte_compare = texte_html.decode("utf-8", "replace")
        else:
            texte_compare = texte_html

        if nouveau_html != texte_compare:
            succes = DB.ReqMAJ(
                "portail_elements",
                [("texte_html", nouveau_html)],
                "IDelement",
                IDelement,
                commit=False,
            )
            if succes:
                etat["modifies"] += 1
            else:
                etat["erreurs"] += 1
                _log(log, u"[AVERTISSEMENT] Impossible de mettre à jour le cache du flux RSS/Atom %s." % IDelement)

    return etat
