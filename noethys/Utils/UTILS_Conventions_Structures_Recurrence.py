#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Adaptateur Noe-062 entre le moteur commun de récurrence et les documents.

Ce module ne calcule aucune règle de calendrier : il appelle exclusivement
``UTILS_Locations_Recurrence.CalculerOccurrencesAnnexe`` puis convertit les
occurrences obtenues vers le contrat d'annexe de
``UTILS_Conventions_Structures_Documents``.

Aucune écriture en base, prestation ou PDF n'est créée ici.
"""
from __future__ import unicode_literals

import hashlib

from Utils import UTILS_Conventions_Structures_Documents
from Utils import UTILS_Locations_Recurrence


def _texte(valeur):
    if valeur is None:
        return u""
    try:
        return valeur.strip()
    except Exception:
        return valeur


def _identifiant_occurrence(convention_uid, debut, fin, groupe, lieu):
    """Produit un identifiant déterministe pour une occurrence d'annexe."""
    cle = u"|".join((
        _texte(convention_uid),
        debut.isoformat(),
        fin.isoformat(),
        _texte(groupe),
        _texte(lieu),
    ))
    return "SEANCE-%s" % hashlib.sha256(cle.encode("utf-8")).hexdigest()[:24]


def ConstruireLignesAnnexeDepuisOccurrences(
    occurrences=None,
    convention_uid="",
    groupe="",
    lieu="",
    observations="",
):
    """Convertit les occurrences du moteur historique en lignes d'annexe."""
    lignes = []
    for occurrence in occurrences or ():
        occurrence = dict(occurrence or {})
        debut = occurrence.get("date_debut")
        fin = occurrence.get("date_fin")
        if debut is None or fin is None:
            raise ValueError("Une occurrence doit fournir date_debut et date_fin")
        if fin < debut:
            raise ValueError("La fin d'une occurrence ne peut pas précéder son début")
        duree_secondes = (fin - debut).total_seconds()
        if duree_secondes % 60:
            raise ValueError("La durée d'une occurrence doit être exprimable en minutes entières")
        lignes.append({
            "identifiant_stable": _identifiant_occurrence(
                convention_uid, debut, fin, groupe, lieu
            ),
            "date": debut.date().isoformat(),
            "heure_debut": debut.strftime("%H:%M"),
            "heure_fin": fin.strftime("%H:%M"),
            "duree_minutes": int(duree_secondes // 60),
            "groupe": _texte(groupe),
            "lieu": _texte(lieu),
            "observations": _texte(observations),
        })
    return UTILS_Conventions_Structures_Documents.NormaliserAnnexe(lignes)


def CalculerLignesAnnexe(
    dictDonnees=None,
    convention_uid="",
    groupe="",
    lieu="",
    observations="",
    DB=None,
    calendrier=None,
):
    """Calcule via le moteur commun puis adapte le résultat pour le document."""
    occurrences = UTILS_Locations_Recurrence.CalculerOccurrencesAnnexe(
        dictDonnees=dictDonnees,
        DB=DB,
        calendrier=calendrier,
    )
    return ConstruireLignesAnnexeDepuisOccurrences(
        occurrences=occurrences,
        convention_uid=convention_uid,
        groupe=groupe,
        lieu=lieu,
        observations=observations,
    )


def ConstruirePaquetDocumentaireDepuisRecurrence(
    gestion,
    IDconvention_structure,
    dictDonnees,
    groupe="",
    lieu="",
    observations="",
    DB=None,
    calendrier=None,
):
    """Construit le paquet documentaire avec une annexe issue du moteur commun."""
    convention = gestion.LireConvention(IDconvention_structure)
    if not convention:
        raise ValueError("Convention introuvable")
    lignes = CalculerLignesAnnexe(
        dictDonnees=dictDonnees,
        convention_uid=convention.get("uid") or "",
        groupe=groupe,
        lieu=lieu,
        observations=observations,
        DB=DB,
        calendrier=calendrier,
    )
    return gestion.ConstruirePaquetDocumentaire(
        IDconvention_structure,
        lignes_annexe=lignes,
    )
