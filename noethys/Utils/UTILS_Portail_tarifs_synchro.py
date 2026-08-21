#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Licence:          GNU GPL
#------------------------------------------------------------------------

"""Actualisation automatique des blocs tarifaires avant synchro Connecthys."""

import datetime

from Utils import UTILS_Portail_tarifs_bloc
from Utils import UTILS_Portail_tarifs_donnees


def _log(log, message):
    try:
        log.EcritLog(message)
    except Exception:
        pass


def _html_publication(DB, config, constructeur=None):
    politique = UTILS_Portail_tarifs_bloc.politique_depuis_configuration(config)
    if constructeur is not None:
        return constructeur(DB, politique, config["titre"])
    publication = UTILS_Portail_tarifs_donnees.construire_publication(
        DB,
        politique=politique,
        titre=config["titre"],
    )
    return publication["html"]


def actualiser(DB, log=None, constructeur=None):
    """Régénère uniquement les blocs tarifs dont le HTML a réellement changé."""
    etat = {"present": False, "modifies": 0, "erreurs": 0}
    req = """SELECT IDelement, parametres, texte_html
    FROM portail_elements
    WHERE parametres IS NOT NULL;"""
    if not DB.ExecuterReq(req):
        return etat

    for IDelement, parametres, texte_html in DB.ResultatReq():
        if not UTILS_Portail_tarifs_bloc.est_configuration_bloc_tarifs(parametres):
            continue
        etat["present"] = True
        config = UTILS_Portail_tarifs_bloc.deserialiser_configuration(parametres)
        try:
            nouveau_html = _html_publication(DB, config, constructeur=constructeur)
        except Exception as err:
            etat["erreurs"] += 1
            _log(log, u"[AVERTISSEMENT] Publication des tarifs impossible (%s). Dernière version conservée." % err)
            continue

        if isinstance(texte_html, bytes):
            texte_compare = texte_html.decode("utf-8", "replace")
        else:
            texte_compare = texte_html
        if nouveau_html == texte_compare:
            continue

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
            _log(log, u"[AVERTISSEMENT] Impossible de mettre à jour le bloc tarifs %s." % IDelement)
    return etat


def preparer_avant_synchro(log=None, db_factory=None, parametre_setter=None,
                            constructeur=None, maintenant=None):
    """Actualise les barèmes puis force l'export uniquement s'ils ont changé."""
    if db_factory is None:
        import GestionDB
        db_factory = GestionDB.DB
    if parametre_setter is None:
        from Utils import UTILS_Parametres
        parametre_setter = UTILS_Parametres.Parametres

    DB = db_factory()
    etat = {"present": False, "modifies": 0, "erreurs": 0}
    try:
        etat = actualiser(DB, log=log, constructeur=constructeur)
        if etat["modifies"]:
            try:
                DB.Commit()
            except Exception as err:
                etat["erreurs"] += 1
                _log(log, u"[AVERTISSEMENT] Impossible d'enregistrer la publication des tarifs (%s)." % err)
                try:
                    DB.connexion.rollback()
                except Exception:
                    pass
    finally:
        try:
            DB.Close()
        except Exception:
            pass

    if etat["modifies"]:
        instant = maintenant or datetime.datetime.now()
        try:
            parametre_setter(
                mode="set",
                categorie="portail",
                nom="last_update_pages",
                valeur=str(instant),
            )
        except Exception as err:
            etat["erreurs"] += 1
            _log(log, u"[AVERTISSEMENT] Impossible de marquer les tarifs comme modifiés (%s)." % err)
    return etat
