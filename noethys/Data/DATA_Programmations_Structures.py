#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Schéma additif des programmations annuelles Noe-062E."""
from __future__ import unicode_literals


DB_PROGRAMMATIONS_STRUCTURES = {
    "structures_programmations": [
        ("IDprogrammation_structure", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID local de la programmation annuelle"),
        ("uid", "VARCHAR(64)", u"Identifiant stable inter-applications"),
        ("type_source", "VARCHAR(50)", u"relation ou activite"),
        ("IDrelation_structure", "INTEGER", u"Relation contractuelle source si applicable"),
        ("IDactivite", "INTEGER", u"Activité Noethys source si applicable"),
        ("IDgroupe_activite", "INTEGER", u"Groupe d'activité Noethys optionnel"),
        ("IDprogrammation_parent", "INTEGER", u"Programmation N-1 ou version source"),
        ("saison", "VARCHAR(50)", u"Saison ou exercice de référence"),
        ("libelle", "VARCHAR(300)", u"Libellé métier de la programmation"),
        ("statut", "VARCHAR(50)", u"brouillon, soumise, validee, annulee"),
        ("date_debut", "DATE", u"Début de la programmation"),
        ("date_fin", "DATE", u"Fin de la programmation"),
        ("UIDintervenant_habituel", "VARCHAR(100)", u"UID RH stable de l'intervenant habituel"),
        ("IDlieu_habituel", "INTEGER", u"Lieu habituel optionnel"),
        ("actif", "INTEGER", u"Programmation active 0/1"),
        ("memo", "VARCHAR(2000)", u"Mémo"),
        ("date_creation", "DATE", u"Date de création"),
        ("date_modification", "DATE", u"Date de dernière modification"),
    ],

    "structures_programmations_creneaux": [
        ("IDcreneau_programmation", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID local du créneau récurrent"),
        ("uid", "VARCHAR(64)", u"Identifiant stable du créneau"),
        ("IDprogrammation_structure", "INTEGER", u"Programmation annuelle concernée"),
        ("IDcreneau_source", "INTEGER", u"Créneau N-1 source éventuel"),
        ("jour_semaine", "INTEGER", u"Jour Python 0=lundi à 6=dimanche"),
        ("heure_debut", "VARCHAR(5)", u"Heure de début HH:MM"),
        ("heure_fin", "VARCHAR(5)", u"Heure de fin HH:MM"),
        ("date_debut", "DATE", u"Borne de début spécifique optionnelle"),
        ("date_fin", "DATE", u"Borne de fin spécifique optionnelle"),
        ("appliquer_scolaire", "INTEGER", u"Inclure les périodes scolaires 0/1"),
        ("appliquer_vacances", "INTEGER", u"Inclure les vacances 0/1"),
        ("inclure_feries", "INTEGER", u"Inclure les jours fériés 0/1"),
        ("frequence", "INTEGER", u"Code historique 1,2,3,4,5 paire,6 impaire"),
        ("IDlieu", "INTEGER", u"Lieu spécifique optionnel"),
        ("groupe", "VARCHAR(200)", u"Libellé groupe/classe/section pour l'annexe"),
        ("observations", "VARCHAR(1000)", u"Observations prévisionnelles"),
        ("etat_renouvellement", "VARCHAR(50)", u"ajoute, inchange, modifie, supprime"),
        ("actif", "INTEGER", u"Créneau actif 0/1"),
        ("date_creation", "DATE", u"Date de création"),
        ("date_modification", "DATE", u"Date de dernière modification"),
    ],
}


def GetChamps(nom_table):
    return tuple(champ[0] for champ in DB_PROGRAMMATIONS_STRUCTURES[nom_table])
