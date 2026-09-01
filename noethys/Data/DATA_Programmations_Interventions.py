#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Traçabilité additive entre programmations Noe-062E et séances canoniques."""
from __future__ import unicode_literals


DB_PROGRAMMATIONS_INTERVENTIONS = {
    "interventions_programmations": [
        ("IDintervention_programmation", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID local du lien de génération"),
        ("IDintervention", "INTEGER UNIQUE", u"Séance canonique ; un seul lien de génération par séance"),
        ("IDprogrammation_structure", "INTEGER", u"Programmation annuelle source"),
        ("IDcreneau_programmation", "INTEGER", u"Créneau récurrent source"),
        ("type_source", "VARCHAR(50)", u"relation ou activite au moment de la génération"),
        ("IDrelation_structure", "INTEGER", u"Relation contractuelle source si applicable"),
        ("IDactivite", "INTEGER", u"Activité Noethys source si applicable"),
        ("IDgroupe_activite", "INTEGER", u"Groupe d'activité source optionnel"),
        ("cle_occurrence", "VARCHAR(120) UNIQUE", u"Clé déterministe programme/créneau/date/horaire"),
        ("empreinte_generation", "VARCHAR(64)", u"SHA-256 des données prévisionnelles matérialisées"),
        ("date_generation", "DATE", u"Date de première matérialisation"),
    ],
}


def GetChamps(nom_table="interventions_programmations"):
    return tuple(champ[0] for champ in DB_PROGRAMMATIONS_INTERVENTIONS[nom_table])
