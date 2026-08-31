#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Référentiel canonique des lieux Noe-062C, sans dépendance wxPython."""
from __future__ import unicode_literals

import datetime
import uuid


TYPES_LIEUX = ("gymnase", "terrain", "ecole", "salle", "piscine", "siege", "autre")

CHAMPS_LIEU = (
    "uid", "nom", "type_lieu", "rue", "complement", "cp", "ville",
    "latitude", "longitude", "IDstructure_gestionnaire",
    "informations_acces", "notes", "actif", "date_creation", "date_modification",
)

CHAMPS_TEXTE = (
    "nom", "rue", "complement", "cp", "ville", "informations_acces", "notes",
)


def _texte(valeur):
    if valeur is None:
        return u""
    try:
        return valeur.strip()
    except Exception:
        return valeur


def _date_iso(valeur=None):
    valeur = valeur or datetime.date.today()
    if isinstance(valeur, datetime.datetime):
        valeur = valeur.date()
    if isinstance(valeur, datetime.date):
        return valeur.isoformat()
    return _texte(valeur)


def _coord(valeur, minimum, maximum, nom):
    if valeur in (None, u"", ""):
        return None
    try:
        resultat = float(valeur)
    except (TypeError, ValueError):
        raise ValueError("%s doit être un nombre" % nom)
    if resultat < minimum or resultat > maximum:
        raise ValueError("%s hors limites" % nom)
    return resultat


def GenererUIDLieu():
    return "LIEU-%s" % uuid.uuid4().hex


def NormaliserLieu(donnees, date=None, creation=False):
    donnees = dict(donnees or {})
    if creation:
        nom = _texte(donnees.get("nom"))
        if not nom:
            raise ValueError("Le nom du lieu est obligatoire")
        type_lieu = _texte(donnees.get("type_lieu")) or "autre"
    else:
        if not donnees:
            raise ValueError("Aucune donnée à modifier")
        nom = None
        type_lieu = None
        if "nom" in donnees:
            nom = _texte(donnees.get("nom"))
            if not nom:
                raise ValueError("Le nom du lieu ne peut pas être vide")
        if "type_lieu" in donnees:
            type_lieu = _texte(donnees.get("type_lieu"))
            if not type_lieu:
                raise ValueError("type_lieu ne peut pas être vide")

    if type_lieu is not None and type_lieu not in TYPES_LIEUX:
        raise ValueError("type_lieu inconnu: %s" % type_lieu)

    resultat = {}
    for champ in CHAMPS_LIEU:
        if champ in donnees:
            resultat[champ] = donnees[champ]

    if creation or "nom" in donnees:
        resultat["nom"] = nom
    if creation or "type_lieu" in donnees:
        resultat["type_lieu"] = type_lieu

    for champ in CHAMPS_TEXTE:
        if champ == "nom":
            continue
        if creation or champ in donnees:
            resultat[champ] = _texte(donnees.get(champ))

    if creation or "latitude" in donnees:
        resultat["latitude"] = _coord(donnees.get("latitude"), -90.0, 90.0, "latitude")
    if creation or "longitude" in donnees:
        resultat["longitude"] = _coord(donnees.get("longitude"), -180.0, 180.0, "longitude")

    if creation or "IDstructure_gestionnaire" in donnees:
        valeur = donnees.get("IDstructure_gestionnaire")
        resultat["IDstructure_gestionnaire"] = int(valeur) if valeur not in (None, "", 0, "0") else None

    if creation or "actif" in donnees:
        resultat["actif"] = 1 if donnees.get("actif", 1) not in (0, False, "0") else 0
    resultat["date_modification"] = _date_iso(date)

    if creation:
        resultat["uid"] = _texte(donnees.get("uid")) or GenererUIDLieu()
        resultat["date_creation"] = _date_iso(donnees.get("date_creation") or date)
    else:
        resultat.pop("uid", None)
        resultat.pop("date_creation", None)

    return resultat


def _liste_pairs(donnees):
    return [(champ, donnees.get(champ)) for champ in CHAMPS_LIEU if champ in donnees]


class GestionnaireLieux(object):
    def __init__(self, db):
        self.db = db

    def CreerLieu(self, donnees, date=None):
        valeurs = NormaliserLieu(donnees, date=date, creation=True)
        return self.db.ReqInsert("lieux", _liste_pairs(valeurs))

    def ModifierLieu(self, IDlieu, donnees, date=None):
        if not IDlieu:
            raise ValueError("IDlieu obligatoire")
        valeurs = NormaliserLieu(donnees, date=date, creation=False)
        return self.db.ReqMAJ("lieux", _liste_pairs(valeurs), "IDlieu", int(IDlieu))

    def ArchiverLieu(self, IDlieu, date=None):
        return self.ModifierLieu(IDlieu, {"actif": 0}, date=date)

    def LireLieu(self, IDlieu):
        req = "SELECT IDlieu, %s FROM lieux WHERE IDlieu=%d;" % (
            ", ".join(CHAMPS_LIEU), int(IDlieu))
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq()
        if not lignes:
            return None
        return dict(zip(("IDlieu",) + CHAMPS_LIEU, lignes[0]))

    def LireLieuParUID(self, uid):
        uid = _texte(uid)
        if not uid:
            return None
        if not all(ch.isalnum() or ch in "-_" for ch in uid):
            raise ValueError("UID de lieu invalide")
        req = "SELECT IDlieu, %s FROM lieux WHERE uid='%s';" % (
            ", ".join(CHAMPS_LIEU), uid)
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq()
        if not lignes:
            return None
        return dict(zip(("IDlieu",) + CHAMPS_LIEU, lignes[0]))

    def ListerLieux(self, actifs_seulement=True):
        condition = " WHERE actif=1" if actifs_seulement else ""
        req = "SELECT IDlieu, %s FROM lieux%s ORDER BY nom, IDlieu;" % (
            ", ".join(CHAMPS_LIEU), condition)
        if self.db.ExecuterReq(req) != 1:
            return []
        return [dict(zip(("IDlieu",) + CHAMPS_LIEU, ligne)) for ligne in self.db.ResultatReq()]
