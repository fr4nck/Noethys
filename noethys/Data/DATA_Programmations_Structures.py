#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Schéma additif des programmations annuelles Noe-062E.

La programmation décrit les créneaux prévisionnels d'une relation contractuelle.
Elle ne remplace ni le moteur historique de récurrence, ni les séances
``interventions`` : les occurrences sont calculées à partir de ces créneaux puis
matérialisées dans une étape distincte.
"""
from __future__ import unicode_literals


DB_PROGRAMMATIONS_STRUCTURES = {
    "structures_programmations": [
        ("IDprogrammation_structure", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID local de la programmation"),
        ("uid", "VARCHAR(64)", u"Identifiant stable inter-applications"),
        ("IDrelation_structure", "INTEGER", u"Relation contractuelle concernée"),
        ("IDprogrammation_source", "INTEGER", u"Programmation N-1 source optionnelle"),
        ("saison", "VARCHAR(50)", u"Saison / exercice"),
        ("statut", "VARCHAR(30)", u"brouillon, soumise, validee, annulee"),
        ("date_debut", "DATE", u"Début de la programmation"),
        ("date_fin", "DATE", u"Fin de la programmation"),
        ("notes", "VARCHAR(2000)", u"Notes de programmation"),
        ("actif", "INTEGER", u"Programmation active 0/1"),
        ("date_creation", "DATE", u"Date de création"),
        ("date_modification", "DATE", u"Date de modification"),
    ],
    "structures_programmations_creneaux": [
        ("IDcreneau_programmation", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID local du créneau"),
        ("uid", "VARCHAR(64)", u"Identifiant stable du créneau"),
        ("IDprogrammation_structure", "INTEGER", u"Programmation parente"),
        ("IDcreneau_source", "INTEGER", u"Créneau N-1 source optionnel"),
        ("jour_semaine", "INTEGER", u"Jour 0=lundi à 6=dimanche"),
        ("heure_debut", "VARCHAR(5)", u"Heure HH:MM"),
        ("heure_fin", "VARCHAR(5)", u"Heure HH:MM"),
        ("date_debut", "DATE", u"Borne spécifique optionnelle"),
        ("date_fin", "DATE", u"Borne spécifique optionnelle"),
        ("IDgroupe_structure", "INTEGER", u"Section/classe/groupe optionnel"),
        ("IDlieu", "INTEGER", u"Lieu habituel optionnel"),
        ("nature", "VARCHAR(50)", u"sport, animation, autre"),
        ("libelle", "VARCHAR(300)", u"Libellé prévisionnel de la séance"),
        ("appliquer_scolaire", "INTEGER", u"Inclure périodes scolaires 0/1"),
        ("appliquer_vacances", "INTEGER", u"Inclure vacances 0/1"),
        ("inclure_feries", "INTEGER", u"Inclure jours fériés 0/1"),
        ("frequence", "INTEGER", u"Code fréquence historique 1 à 6"),
        ("etat_renouvellement", "VARCHAR(30)", u"inchange, modifie, supprime, ajoute"),
        ("observations", "VARCHAR(2000)", u"Observations"),
        ("actif", "INTEGER", u"Créneau actif 0/1"),
        ("date_creation", "DATE", u"Date de création"),
        ("date_modification", "DATE", u"Date de modification"),
    ],
}


def GetNomsTables():
    return tuple(DB_PROGRAMMATIONS_STRUCTURES.keys())


def GetChamps(nom_table):
    return tuple(champ[0] for champ in DB_PROGRAMMATIONS_STRUCTURES[nom_table])
