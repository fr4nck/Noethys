#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Moteur commun de récurrence des locations et annexes Noe-062.

Ce module est l'extraction sans changement fonctionnel de
``DLG_Saisie_location.Dialog.Calcule_occurences``. Il ne dépend pas de
wxPython et peut recevoir une connexion DB injectée pour les tests ou les
appelants métier.

Les valeurs historiques de ``semaines`` sont conservées :
- 1 : toutes les semaines ;
- 2, 3, 4 : une semaine sur N selon le compteur historique ;
- 5 : semaines ISO paires ;
- 6 : semaines ISO impaires.
"""
from __future__ import unicode_literals

import copy
import datetime


def _charger_calendrier(DB=None):
    """Charge vacances et jours fériés en conservant les requêtes historiques."""
    fermer = DB is None
    if DB is None:
        import GestionDB
        DB = GestionDB.DB()

    try:
        req = """SELECT date_debut, date_fin, nom, annee FROM vacances ORDER BY date_debut;"""
        DB.ExecuterReq(req)
        liste_vacances = DB.ResultatReq()
        req = """SELECT type, nom, jour, mois, annee FROM jours_feries;"""
        DB.ExecuterReq(req)
        liste_feries = DB.ResultatReq()
        return liste_vacances, liste_feries
    finally:
        if fermer:
            DB.Close()


def CalculerOccurrences(dictDonnees=None, DB=None, calendrier=None):
    """Calcule les occurrences avec les règles historiques de Locations.

    ``calendrier`` peut être un tuple ``(listeVacances, listeFeries)`` pour
    exécuter le calcul sans accès DB. À défaut, le calendrier est chargé depuis
    ``DB`` ou depuis une connexion ``GestionDB.DB()`` temporaire.
    """
    dictDonnees = dictDonnees or {}
    liste_resultats = []
    date_debut = dictDonnees["date_debut"]
    date_fin = dictDonnees["date_fin"]
    heure_debut = dictDonnees["heure_debut"]
    heure_fin = dictDonnees["heure_fin"]
    jours_vacances = dictDonnees["jours_vacances"]
    jours_scolaires = dictDonnees["jours_scolaires"]
    semaines = dictDonnees["semaines"]
    feries = dictDonnees["feries"]

    if calendrier is None:
        liste_vacances, liste_feries = _charger_calendrier(DB=DB)
    else:
        liste_vacances, liste_feries = calendrier

    def EstEnVacances(dateDD):
        date = str(dateDD)
        for valeurs in liste_vacances:
            date_debut_vacances = valeurs[0]
            date_fin_vacances = valeurs[1]
            if date >= date_debut_vacances and date <= date_fin_vacances:
                return True
        return False

    def EstFerie(dateDD):
        jour = dateDD.day
        mois = dateDD.month
        annee = dateDD.year
        for type_ferie, nom, jourTmp, moisTmp, anneeTmp in liste_feries:
            jourTmp = int(jourTmp)
            moisTmp = int(moisTmp)
            anneeTmp = int(anneeTmp)
            if type_ferie == "fixe":
                if jourTmp == jour and moisTmp == mois:
                    return True
            else:
                if jourTmp == jour and moisTmp == mois and anneeTmp == annee:
                    return True
        return False

    # Bloc historique conservé tel quel pour garantir la parité de comportement.
    date_debut_temp = date_debut
    date_fin_temp = date_fin
    if "date" in dictDonnees:
        date = dictDonnees["date"]
        if date < date_debut_temp:
            date_debut_temp = date
        if date > date_fin_temp:
            date_fin_temp = date

    listeDates = [date_debut]
    tmp = date_debut
    while tmp < date_fin:
        tmp += datetime.timedelta(days=1)
        listeDates.append(tmp)

    date = date_debut
    numSemaine = copy.copy(semaines)
    dateTemp = date
    for date in listeDates:
        valide = False
        if EstEnVacances(date):
            if date.weekday() in jours_vacances:
                valide = True
        else:
            if date.weekday() in jours_scolaires:
                valide = True

        if len(listeDates) > 0:
            if date.weekday() < dateTemp.weekday():
                numSemaine += 1

        if semaines in (2, 3, 4):
            if numSemaine % semaines != 0:
                valide = False

        if valide is True and semaines in (5, 6):
            numSemaineAnnee = date.isocalendar()[1]
            if numSemaineAnnee % 2 == 0 and semaines == 6:
                valide = False
            if numSemaineAnnee % 2 != 0 and semaines == 5:
                valide = False

        if feries is False and EstFerie(date) is True:
            valide = False

        if valide is True:
            date_debut_final = datetime.datetime(
                year=date.year,
                month=date.month,
                day=date.day,
                hour=int(heure_debut[:2]),
                minute=int(heure_debut[3:]),
            )
            date_fin_final = datetime.datetime(
                year=date.year,
                month=date.month,
                day=date.day,
                hour=int(heure_fin[:2]),
                minute=int(heure_fin[3:]),
            )
            liste_resultats.append({
                "date_debut": date_debut_final,
                "date_fin": date_fin_final,
            })

        dateTemp = date
    return liste_resultats


def CalculerOccurrencesAnnexe(dictDonnees=None, DB=None, calendrier=None):
    """Alias métier explicite pour les annexes Noe-062.

    Il s'agit volontairement du même moteur, sans variante ni règle propre aux
    conventions.
    """
    return CalculerOccurrences(dictDonnees=dictDonnees, DB=DB, calendrier=calendrier)
