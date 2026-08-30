#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Activation additive Noe-062C sans modifier le contrat strict Noe-062B.

Noe-062B reste responsable de ``structures``, ``structures_contacts`` et
``interventions``. Noe-062C ajoute uniquement les tables ``lieux`` et
``interventions_execution``. Une base 062B conforme peut donc être enrichie
sans modification de table existante ni réparation silencieuse.
"""
from __future__ import unicode_literals

from Utils import UTILS_Tiers_Schema


TABLES_062C = ("lieux", "interventions_execution")
TABLES_062C_COMPLET = UTILS_Tiers_Schema.TABLES_062B_COMPLET + TABLES_062C


def InspecterSchema062C(db):
    """Inspecte le socle 062B et les deux tables additives 062C sans écrire."""
    return UTILS_Tiers_Schema.InspecterSchema(db, tables=TABLES_062C_COMPLET)


def AssurerSchema062C(db, appliquer=False):
    """Active explicitement le schéma complet 062C.

    Le préflight reste global : si une table 062A/062B/062C déjà présente est
    incohérente, aucune nouvelle table n'est créée. Une base 062B conforme ne
    reçoit que ``lieux`` et ``interventions_execution``.
    """
    return UTILS_Tiers_Schema._assurer_schema(
        db,
        TABLES_062C_COMPLET,
        appliquer=appliquer,
    )
