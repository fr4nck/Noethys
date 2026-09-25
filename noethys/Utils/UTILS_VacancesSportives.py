#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Règles de calendrier spécifiques aux activités sportives."""

import datetime


def _ConvertirDate(valeur):
    if isinstance(valeur, datetime.date):
        return valeur
    if isinstance(valeur, datetime.datetime):
        return valeur.date()
    if isinstance(valeur, str):
        return datetime.datetime.strptime(valeur[:10], "%Y-%m-%d").date()
    raise ValueError("Date de vacances invalide : %r" % (valeur,))


def GetDebutVacancesSportives(date_debut):
    """Retourne le premier dimanche à partir du début officiel des vacances."""
    date_debut = _ConvertirDate(date_debut)
    jours_jusqua_dimanche = (6 - date_debut.weekday()) % 7
    return date_debut + datetime.timedelta(days=jours_jusqua_dimanche)


def EstEnVacancesSportives(dateDD, listeVacances):
    """Vacances sportives : du premier dimanche au dimanche de fin inclus.

    Permet notamment de conserver le premier samedi des vacances scolaires
    pour les activités sportives hebdomadaires.
    """
    dateDD = _ConvertirDate(dateDD)
    for valeurs in listeVacances:
        date_debut = GetDebutVacancesSportives(valeurs[0])
        date_fin = _ConvertirDate(valeurs[1])
        if date_debut <= dateDD <= date_fin:
            return True
    return False
