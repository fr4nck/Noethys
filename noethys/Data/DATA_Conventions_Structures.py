#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Schéma additif des conventions/avenants liés aux relations Noe-062."""
from __future__ import unicode_literals


DB_CONVENTIONS_STRUCTURES = {
    "structures_conventions": [
        ("IDconvention_structure", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID local de la convention ou de l'avenant"),
        ("uid", "VARCHAR(64)", u"Identifiant stable inter-applications"),
        ("IDrelation_structure", "INTEGER", u"Relation contractuelle concernée"),
        ("IDconvention_parent", "INTEGER", u"Convention/version parente pour un avenant"),
        ("reference", "VARCHAR(200)", u"Référence documentaire libre"),
        ("version", "INTEGER", u"Numéro de version dans la chaîne contractuelle"),
        ("statut", "VARCHAR(50)", u"brouillon, validee, signee, terminee, annulee"),
        ("date_debut", "DATE", u"Début d'effet de cette version"),
        ("date_fin", "DATE", u"Fin d'effet éventuelle"),
        ("objet", "VARCHAR(500)", u"Objet ou intitulé documentaire optionnel"),
        ("notes", "VARCHAR(2000)", u"Notes internes"),
        ("snapshot_contractuel", "LONGBLOB", u"Instantané JSON figé à la validation"),
        ("empreinte_sha256", "VARCHAR(64)", u"Empreinte de l'instantané contractuel"),
        ("date_validation", "DATE", u"Date de validation de la version"),
        ("date_signature", "DATE", u"Date de signature constatée"),
        ("actif", "INTEGER", u"Version active dans l'historique 0/1"),
        ("date_creation", "DATE", u"Date de création"),
        ("date_modification", "DATE", u"Date de dernière modification"),
    ],
}


def GetChamps(nom_table="structures_conventions"):
    return tuple(champ[0] for champ in DB_CONVENTIONS_STRUCTURES[nom_table])
