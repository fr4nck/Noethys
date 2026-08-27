#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Couche métier minimale pour le référentiel des tiers (Noe-062A).

Le module ne dépend pas de wxPython et accepte une instance de ``GestionDB.DB``
(ou un double de test) injectée par l'appelant. Il ne crée aucune table : le
schéma reste déclaré dans ``Data.DATA_Structures`` tant que la migration
additive n'est pas explicitement activée.
"""

from __future__ import unicode_literals

import datetime
import uuid


TYPES_TIERS = (
    "association",
    "club_section",
    "ecole",
    "mairie_collectivite",
    "alsh",
    "departement_ase",
    "financeur",
    "autre",
)

ROLES_CONTACT = (
    "direction",
    "president_bureau",
    "tresorier",
    "responsable_section",
    "planning",
    "facturation",
    "convention",
    "administratif",
    "urgence",
    "autre",
)

CHAMPS_STRUCTURE = (
    "uid",
    "type_structure",
    "nom",
    "nom_court",
    "nom_officiel",
    "IDstructure_parent",
    "rue",
    "cp",
    "ville",
    "tel",
    "mail",
    "site_web",
    "rna",
    "siren",
    "siret",
    "ape",
    "memo",
    "actif",
    "date_creation",
    "date_modification",
)

CHAMPS_CONTACT = (
    "IDstructure",
    "IDindividu",
    "nom",
    "prenom",
    "fonction",
    "tel",
    "mobile",
    "mail",
    "contact_principal",
    "actif",
    "memo",
)


def _texte(valeur):
    if valeur is None:
        return u""
    try:
        return valeur.strip()
    except Exception:
        return valeur


def _date_iso(date=None):
    date = date or datetime.date.today()
    if isinstance(date, datetime.datetime):
        date = date.date()
    if isinstance(date, datetime.date):
        return date.isoformat()
    return _texte(date)


def GenererUIDStructure():
    """Produit un identifiant stable et opaque destiné aux synchronisations."""
    return "STR-%s" % uuid.uuid4().hex


def NormaliserStructure(donnees, date=None, creation=False):
    """Valide et normalise un dictionnaire de structure avant écriture."""
    donnees = dict(donnees or {})
    type_structure = _texte(donnees.get("type_structure")) or "autre"
    if type_structure not in TYPES_TIERS:
        raise ValueError("type_structure inconnu: %s" % type_structure)

    nom = _texte(donnees.get("nom"))
    if not nom:
        raise ValueError("Le nom de la structure est obligatoire")

    resultat = {}
    for champ in CHAMPS_STRUCTURE:
        if champ in donnees:
            resultat[champ] = donnees[champ]

    resultat["type_structure"] = type_structure
    resultat["nom"] = nom
    resultat["nom_court"] = _texte(donnees.get("nom_court"))
    resultat["nom_officiel"] = _texte(donnees.get("nom_officiel"))
    for champ in ("rue", "cp", "ville", "tel", "mail", "site_web", "rna", "siren", "siret", "ape", "memo"):
        resultat[champ] = _texte(donnees.get(champ))

    resultat["actif"] = 1 if donnees.get("actif", 1) not in (0, False, "0") else 0
    resultat["date_modification"] = _date_iso(date)

    if creation:
        resultat["uid"] = _texte(donnees.get("uid")) or GenererUIDStructure()
        resultat["date_creation"] = _date_iso(donnees.get("date_creation") or date)
    else:
        resultat.pop("uid", None)
        resultat.pop("date_creation", None)

    return resultat


def NormaliserContact(donnees):
    donnees = dict(donnees or {})
    if not donnees.get("IDstructure"):
        raise ValueError("IDstructure est obligatoire pour un contact")
    if not (_texte(donnees.get("nom")) or _texte(donnees.get("prenom")) or _texte(donnees.get("fonction"))):
        raise ValueError("Un contact doit avoir au moins un nom, un prénom ou une fonction")

    resultat = {}
    for champ in CHAMPS_CONTACT:
        if champ in donnees:
            resultat[champ] = donnees[champ]
    for champ in ("nom", "prenom", "fonction", "tel", "mobile", "mail", "memo"):
        resultat[champ] = _texte(donnees.get(champ))
    resultat["contact_principal"] = 1 if donnees.get("contact_principal", 0) not in (0, False, "0") else 0
    resultat["actif"] = 1 if donnees.get("actif", 1) not in (0, False, "0") else 0
    return resultat


def _liste_pairs(donnees, ordre):
    return [(champ, donnees.get(champ)) for champ in ordre if champ in donnees]


class GestionnaireTiers(object):
    """CRUD minimal du référentiel, sans dépendance UI."""

    def __init__(self, db):
        self.db = db

    def CreerStructure(self, donnees, date=None):
        valeurs = NormaliserStructure(donnees, date=date, creation=True)
        return self.db.ReqInsert("structures", _liste_pairs(valeurs, CHAMPS_STRUCTURE))

    def ModifierStructure(self, IDstructure, donnees, date=None):
        if not IDstructure:
            raise ValueError("IDstructure obligatoire")
        valeurs = NormaliserStructure(donnees, date=date, creation=False)
        return self.db.ReqMAJ(
            "structures",
            _liste_pairs(valeurs, CHAMPS_STRUCTURE),
            "IDstructure",
            int(IDstructure),
        )

    def ArchiverStructure(self, IDstructure, date=None):
        return self.ModifierStructure(IDstructure, {"nom": self.LireStructure(IDstructure)["nom"], "type_structure": self.LireStructure(IDstructure)["type_structure"], "actif": 0}, date=date)

    def LireStructure(self, IDstructure):
        req = "SELECT IDstructure, %s FROM structures WHERE IDstructure=%d;" % (
            ", ".join(CHAMPS_STRUCTURE), int(IDstructure))
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq()
        if not lignes:
            return None
        champs = ("IDstructure",) + CHAMPS_STRUCTURE
        return dict(zip(champs, lignes[0]))

    def ListerStructures(self, actifs_seulement=True):
        condition = " WHERE actif=1" if actifs_seulement else ""
        req = "SELECT IDstructure, %s FROM structures%s ORDER BY nom;" % (
            ", ".join(CHAMPS_STRUCTURE), condition)
        if self.db.ExecuterReq(req) != 1:
            return []
        champs = ("IDstructure",) + CHAMPS_STRUCTURE
        return [dict(zip(champs, ligne)) for ligne in self.db.ResultatReq()]

    def CreerContact(self, donnees):
        valeurs = NormaliserContact(donnees)
        return self.db.ReqInsert("structures_contacts", _liste_pairs(valeurs, CHAMPS_CONTACT))

    def ModifierContact(self, IDcontact, donnees):
        if not IDcontact:
            raise ValueError("IDcontact obligatoire")
        valeurs = NormaliserContact(donnees)
        return self.db.ReqMAJ(
            "structures_contacts",
            _liste_pairs(valeurs, CHAMPS_CONTACT),
            "IDcontact",
            int(IDcontact),
        )

    def ListerContacts(self, IDstructure, actifs_seulement=True):
        condition_actif = " AND actif=1" if actifs_seulement else ""
        req = "SELECT IDcontact, %s FROM structures_contacts WHERE IDstructure=%d%s ORDER BY contact_principal DESC, nom, prenom;" % (
            ", ".join(CHAMPS_CONTACT), int(IDstructure), condition_actif)
        if self.db.ExecuterReq(req) != 1:
            return []
        champs = ("IDcontact",) + CHAMPS_CONTACT
        return [dict(zip(champs, ligne)) for ligne in self.db.ResultatReq()]
