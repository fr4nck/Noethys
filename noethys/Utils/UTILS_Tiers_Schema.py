#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Activation additive contrôlée du schéma Noe-062A.

Ce module ne s'exécute jamais au simple import. L'appelant choisit explicitement
``appliquer=True`` pour créer les tables manquantes. Une table déjà existante
mais incomplète n'est jamais réparée silencieusement : l'écart est signalé pour
éviter toute modification implicite d'une base réellement utilisée.
"""

from __future__ import unicode_literals

from Data import DATA_Structures


TABLES_062A = ("structures", "structures_contacts")


def _champs_attendus(nom_table):
    return tuple(champ[0] for champ in DATA_Structures.DB_STRUCTURES[nom_table])


def InspecterSchema(db):
    """Retourne un rapport déterministe sans modifier la base."""
    rapport = {}
    for nom_table in TABLES_062A:
        existe = bool(db.IsTableExists(nom_table))
        champs_attendus = _champs_attendus(nom_table)
        champs_presents = ()
        champs_manquants = champs_attendus
        if existe:
            champs_presents = tuple(champ[0] for champ in db.GetListeChamps2(nom_table))
            champs_manquants = tuple(champ for champ in champs_attendus if champ not in champs_presents)
        rapport[nom_table] = {
            "existe": existe,
            "champs_attendus": champs_attendus,
            "champs_presents": champs_presents,
            "champs_manquants": champs_manquants,
            "conforme": existe and not champs_manquants,
        }
    return rapport


def AssurerSchema(db, appliquer=False):
    """Crée uniquement les tables 062A absentes, de manière idempotente.

    Si une table existe déjà mais ne correspond pas au contrat attendu, aucune
    tentative d'ALTER/repair n'est faite ici. L'appelant reçoit ``ok=False`` et
    le détail des champs manquants afin de décider d'une migration explicite.
    """
    avant = InspecterSchema(db)
    creees = []

    if appliquer:
        for nom_table in TABLES_062A:
            etat = avant[nom_table]
            if not etat["existe"]:
                db.CreationTable(nom_table, DATA_Structures.DB_STRUCTURES)
                db.Commit()
                creees.append(nom_table)

    apres = InspecterSchema(db)
    incoherentes = tuple(
        nom_table for nom_table in TABLES_062A
        if apres[nom_table]["existe"] and not apres[nom_table]["conforme"]
    )
    absentes = tuple(
        nom_table for nom_table in TABLES_062A
        if not apres[nom_table]["existe"]
    )

    return {
        "ok": not incoherentes and (not appliquer or not absentes),
        "appliquer": bool(appliquer),
        "tables_creees": tuple(creees),
        "tables_absentes": absentes,
        "tables_incoherentes": incoherentes,
        "rapport": apres,
    }
