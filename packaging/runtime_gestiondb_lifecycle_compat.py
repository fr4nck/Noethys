# -*- coding: utf-8 -*-
"""Sécurise le cycle de vie des connexions GestionDB sous Python 3.

Le correctif reste limité aux erreurs de compatibilité observées : fermeture
répétée d'une connexion et variable de retour non initialisée dans ReqInsert.
"""
from __future__ import annotations

import GestionDB


_original_close = GestionDB.DB.Close
_original_req_insert = GestionDB.DB.ReqInsert


def _close_compat(self):
    connexion = getattr(self, "connexion", None)
    if connexion is not None:
        try:
            connexion.close()
        except Exception:
            pass
        finally:
            self.connexion = None

    identifiant = getattr(self, "IDconnexion", None)
    if identifiant in GestionDB.DICT_CONNEXIONS:
        del GestionDB.DICT_CONNEXIONS[identifiant]


def _req_insert_compat(self, nomTable="", listeDonnees=None, commit=True):
    if listeDonnees is None:
        listeDonnees = []
    try:
        return _original_req_insert(self, nomTable, listeDonnees, commit)
    except UnboundLocalError:
        # Le code historique tente de retourner newID après une erreur SQL.
        return None


if getattr(GestionDB.DB.Close, "__name__", "") != "_close_compat":
    GestionDB.DB.Close = _close_compat

if getattr(GestionDB.DB.ReqInsert, "__name__", "") != "_req_insert_compat":
    GestionDB.DB.ReqInsert = _req_insert_compat
