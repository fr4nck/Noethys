#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Pont documentaire des conventions persistées Noe-062.

Ce module ne crée ni PDF, ni prestation, ni convention concurrente. Il étend
le workflow persistant de ``UTILS_Conventions_Structures`` afin que les
nouvelles validations produisent un snapshot autoportant, puis transforme ce
snapshot figé en paquet de fusion destiné au moteur documentaire historique.

Une convention déjà validée/signée est toujours relue depuis son
``snapshot_contractuel`` et son SHA-256. Les données courantes du tiers ou de
la relation ne sont jamais réinjectées dans un document officiel.
"""
from __future__ import unicode_literals

import datetime
import hashlib
import json

from Utils import UTILS_Conventions_Structures
from Utils import UTILS_Tiers


DOCUMENT_CONVENTION = "convention"
DOCUMENT_AVENANT = "avenant"
SCHEMA_SNAPSHOT_DOCUMENTABLE = "noe-062-convention-v2"

STATUTS_DOCUMENT_OFFICIEL = (
    UTILS_Conventions_Structures.STATUT_VALIDEE,
    UTILS_Conventions_Structures.STATUT_SIGNEE,
    UTILS_Conventions_Structures.STATUT_TERMINEE,
)

CHAMPS_STRUCTURE_SNAPSHOT = (
    "uid",
    "type_structure",
    "nom",
    "nom_court",
    "nom_officiel",
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
)

CHAMPS_GROUPE_SNAPSHOT = (
    "IDgroupe_structure",
    "nom",
)


def _texte(valeur):
    if valeur is None:
        return u""
    try:
        return valeur.strip()
    except Exception:
        return valeur


def _chaine(valeur):
    if valeur is None:
        return u""
    if isinstance(valeur, bytes):
        return valeur.decode("utf-8")
    return str(valeur)


def _date_fr(valeur):
    valeur = _texte(valeur)
    if not valeur:
        return u""
    try:
        return datetime.datetime.strptime(valeur, "%Y-%m-%d").strftime("%d/%m/%Y")
    except (TypeError, ValueError):
        return valeur


def _nombre(valeur):
    if valeur in (None, ""):
        return u""
    try:
        nombre = float(valeur)
    except (TypeError, ValueError):
        return _chaine(valeur)
    if nombre.is_integer():
        return str(int(nombre))
    return ("%.2f" % nombre).rstrip("0").rstrip(".")


def _snapshot_structure(structure):
    if not structure:
        return None
    return dict((champ, structure.get(champ)) for champ in CHAMPS_STRUCTURE_SNAPSHOT)


def _snapshot_groupe(groupe):
    if not groupe:
        return None
    return dict((champ, groupe.get(champ)) for champ in CHAMPS_GROUPE_SNAPSHOT)


def _libelle_payeur(payeur, structure=None):
    libelle = _texte(payeur.get("libelle_payeur"))
    if libelle:
        return libelle
    if structure:
        return _texte(structure.get("nom"))
    if payeur.get("type_payeur") == "famille" and payeur.get("IDfamille"):
        return "Famille #%s" % int(payeur["IDfamille"])
    if payeur.get("type_payeur") == "departement_ase":
        return "Département / ASE"
    return _texte(payeur.get("type_payeur"))


def _normaliser_ligne_annexe(ligne, numero):
    ligne = dict(ligne or {})
    resultat = {
        "numero": int(numero),
        "date": _texte(ligne.get("date")),
        "heure_debut": _texte(ligne.get("heure_debut")),
        "heure_fin": _texte(ligne.get("heure_fin")),
        "duree_minutes": ligne.get("duree_minutes"),
        "groupe": _texte(ligne.get("groupe")),
        "lieu": _texte(ligne.get("lieu")),
        "observations": _texte(ligne.get("observations")),
        "identifiant_stable": _texte(ligne.get("identifiant_stable")),
    }
    if not resultat["date"]:
        raise ValueError("Une ligne d'annexe doit avoir une date")
    if resultat["duree_minutes"] not in (None, ""):
        try:
            resultat["duree_minutes"] = int(resultat["duree_minutes"])
        except (TypeError, ValueError):
            raise ValueError("duree_minutes d'annexe invalide")
        if resultat["duree_minutes"] < 0:
            raise ValueError("duree_minutes d'annexe ne peut pas être négative")
    return resultat


def NormaliserAnnexe(lignes=None):
    """Normalise une annexe déjà calculée par le moteur de récurrence historique.

    Le calcul vacances/fériés/fréquences n'est volontairement pas réimplémenté
    ici. Ce module ne fait que trier/dédupliquer les occurrences reçues.
    """
    resultat = []
    signatures = set()
    for index, ligne in enumerate(lignes or (), 1):
        item = _normaliser_ligne_annexe(ligne, index)
        signature = (
            item["identifiant_stable"],
            item["date"],
            item["heure_debut"],
            item["heure_fin"],
            item["groupe"],
            item["lieu"],
        )
        if signature in signatures:
            continue
        signatures.add(signature)
        resultat.append(item)
    resultat.sort(
        key=lambda item: (
            item["date"],
            item["heure_debut"],
            item["heure_fin"],
            item["identifiant_stable"],
        )
    )
    for index, item in enumerate(resultat, 1):
        item["numero"] = index
    return resultat


def _ligne_annexe_texte(ligne):
    horaire = ""
    if ligne["heure_debut"] or ligne["heure_fin"]:
        horaire = "%s-%s" % (ligne["heure_debut"], ligne["heure_fin"])
    morceaux = [m for m in (ligne["date"], horaire, ligne["groupe"], ligne["lieu"]) if m]
    return " | ".join(morceaux)


def _payer_fields(payeurs):
    champs = {
        "{PAYEURS_NOMBRE}": str(len(payeurs)),
        "{PAYEURS_LIGNES_TEXTE}": "\n".join(
            "%s%s" % (
                _texte(payeur.get("libelle_document")),
                (" — %s %%" % _nombre(payeur.get("taux_prise_en_charge")))
                if payeur.get("taux_prise_en_charge") not in (None, "")
                else "",
            )
            for payeur in payeurs
        ),
        "{PAYEUR_NOM}": "",
        "{PAYEUR_TYPE}": "",
        "{PAYEUR_TAUX_PRISE_EN_CHARGE}": "",
        "{PAYEUR_REFERENCE}": "",
    }
    if len(payeurs) == 1:
        payeur = payeurs[0]
        champs.update({
            "{PAYEUR_NOM}": _texte(payeur.get("libelle_document")),
            "{PAYEUR_TYPE}": _texte(payeur.get("type_payeur")),
            "{PAYEUR_TAUX_PRISE_EN_CHARGE}": _nombre(payeur.get("taux_prise_en_charge")),
            "{PAYEUR_REFERENCE}": _texte(payeur.get("reference")),
        })
    return champs


def ConstruireChampsFusion(snapshot, convention, lignes_annexe=None):
    """Transforme uniquement les données figées en champs pour modèles Noethys."""
    if not isinstance(snapshot, dict):
        raise ValueError("Snapshot contractuel invalide")
    schema = snapshot.get("schema")
    if schema not in ("noe-062-convention-v1", SCHEMA_SNAPSHOT_DOCUMENTABLE):
        raise ValueError("Version de snapshot contractuel inconnue: %s" % schema)

    convention_snapshot = snapshot.get("convention") or {}
    relation = snapshot.get("relation") or {}
    beneficiaire = snapshot.get("beneficiaire") or {}
    groupe = snapshot.get("groupe") or {}
    payeurs = list(snapshot.get("payeurs") or [])
    complements = snapshot.get("complements") or {}
    contact = complements.get("contact_convention") or {}
    annexe = NormaliserAnnexe(lignes_annexe)

    type_document = (
        DOCUMENT_AVENANT
        if convention_snapshot.get("IDconvention_parent") or int(convention_snapshot.get("version") or 1) > 1
        else DOCUMENT_CONVENTION
    )

    champs = {
        "{DOCUMENT_TYPE}": type_document,
        "{DOCUMENT_EST_AVENANT}": "1" if type_document == DOCUMENT_AVENANT else "0",
        "{DOCUMENT_SNAPSHOT_SCHEMA}": _texte(schema),
        "{CONVENTION_ID_STABLE}": _texte(convention_snapshot.get("uid")),
        "{CONVENTION_REFERENCE}": _texte(convention_snapshot.get("reference")),
        "{CONVENTION_VERSION}": _chaine(convention_snapshot.get("version")),
        "{CONVENTION_PARENT_ID}": _chaine(convention_snapshot.get("IDconvention_parent")),
        "{CONVENTION_DATE_DEBUT}": _date_fr(convention_snapshot.get("date_debut")),
        "{CONVENTION_DATE_FIN}": _date_fr(convention_snapshot.get("date_fin")),
        "{CONVENTION_OBJET}": _texte(convention_snapshot.get("objet")),
        "{CONVENTION_STATUT}": _texte(convention.get("statut")),
        "{CONVENTION_DATE_VALIDATION}": _date_fr(convention.get("date_validation")),
        "{CONVENTION_DATE_SIGNATURE}": _date_fr(convention.get("date_signature")),
        "{CONVENTION_EMPREINTE_SHA256}": _texte(convention.get("empreinte_sha256")),
        "{RELATION_ID_STABLE}": _texte(relation.get("uid")),
        "{RELATION_LIBELLE}": _texte(relation.get("libelle")),
        "{RELATION_SAISON}": _texte(relation.get("saison")),
        "{RELATION_TYPE}": _texte(relation.get("type_relation")),
        "{RELATION_TARIF}": _nombre(relation.get("tarif")),
        "{RELATION_UNITE_TARIF}": _texte(relation.get("unite_tarif")),
        "{RELATION_REGLE_ADHESION}": _texte(relation.get("regle_adhesion")),
        "{RELATION_MODE_FACTURATION}": _texte(relation.get("mode_facturation")),
        "{BENEFICIAIRE_ID_STABLE}": _texte(beneficiaire.get("uid")),
        "{BENEFICIAIRE_NOM}": _texte(beneficiaire.get("nom")),
        "{BENEFICIAIRE_NOM_OFFICIEL}": _texte(beneficiaire.get("nom_officiel")),
        "{BENEFICIAIRE_RUE}": _texte(beneficiaire.get("rue")),
        "{BENEFICIAIRE_CP}": _texte(beneficiaire.get("cp")),
        "{BENEFICIAIRE_VILLE}": _texte(beneficiaire.get("ville")),
        "{BENEFICIAIRE_TEL}": _texte(beneficiaire.get("tel")),
        "{BENEFICIAIRE_MAIL}": _texte(beneficiaire.get("mail")),
        "{BENEFICIAIRE_SIRET}": _texte(beneficiaire.get("siret")),
        "{GROUPE_NOM}": _texte(groupe.get("nom")),
        "{CONTACT_CONVENTION_NOM}": _texte(contact.get("nom")),
        "{CONTACT_CONVENTION_PRENOM}": _texte(contact.get("prenom")),
        "{CONTACT_CONVENTION_FONCTION}": _texte(contact.get("fonction") or contact.get("role")),
        "{CONTACT_CONVENTION_MAIL}": _texte(contact.get("mail")),
        "{CONTACT_CONVENTION_TELEPHONE}": _texte(contact.get("tel") or contact.get("mobile")),
        "{ANNEXE_NB_SEANCES}": str(len(annexe)),
        "{ANNEXE_DUREE_TOTALE_MINUTES}": str(sum(
            int(item.get("duree_minutes") or 0) for item in annexe
        )),
        "{ANNEXE_LIGNES_TEXTE}": "\n".join(_ligne_annexe_texte(item) for item in annexe),
    }
    champs.update(_payer_fields(payeurs))
    return champs, annexe


class GestionnaireConventionsDocumentaires(
    UTILS_Conventions_Structures.GestionnaireConventionsStructures
):
    """Même stockage/workflow que #301, avec snapshot documentable autoportant."""

    def __init__(self, db):
        super(GestionnaireConventionsDocumentaires, self).__init__(db)
        self.tiers = UTILS_Tiers.GestionnaireTiers(db)

    def ConstruireSnapshotContractuel(self, IDconvention_structure, complements=None):
        snapshot = super(GestionnaireConventionsDocumentaires, self).ConstruireSnapshotContractuel(
            IDconvention_structure, complements=complements
        )
        relation = snapshot.get("relation") or {}
        IDstructure = relation.get("IDstructure")
        beneficiaire = self.tiers.LireStructure(IDstructure) if IDstructure else None
        if not beneficiaire:
            raise ValueError("Structure bénéficiaire introuvable pour le snapshot")
        snapshot["beneficiaire"] = _snapshot_structure(beneficiaire)

        IDgroupe = relation.get("IDgroupe_structure")
        snapshot["groupe"] = _snapshot_groupe(self.tiers.LireGroupe(IDgroupe)) if IDgroupe else None

        payeurs_enrichis = []
        for payeur in snapshot.get("payeurs") or []:
            item = dict(payeur)
            structure_payeur = None
            IDstructure_payeur = item.get("IDstructure_payeur")
            if IDstructure_payeur:
                structure_payeur = self.tiers.LireStructure(IDstructure_payeur)
            if item.get("implicite") and not structure_payeur:
                structure_payeur = beneficiaire
            item["structure"] = _snapshot_structure(structure_payeur)
            item["libelle_document"] = _libelle_payeur(item, structure=structure_payeur)
            payeurs_enrichis.append(item)
        snapshot["payeurs"] = payeurs_enrichis
        snapshot["schema"] = SCHEMA_SNAPSHOT_DOCUMENTABLE
        return UTILS_Conventions_Structures._normaliser_json(snapshot)

    def ConstruirePaquetDocumentaire(self, IDconvention_structure, lignes_annexe=None):
        convention = self.LireConvention(IDconvention_structure)
        if not convention:
            raise ValueError("Convention introuvable")
        if convention.get("statut") not in STATUTS_DOCUMENT_OFFICIEL:
            raise ValueError("Une convention brouillon ou annulée n'est pas documentable officiellement")
        snapshot = self.LireSnapshot(IDconvention_structure)
        champs, annexe = ConstruireChampsFusion(
            snapshot, convention, lignes_annexe=lignes_annexe
        )
        paquet = {
            "type_document": champs["{DOCUMENT_TYPE}"],
            "convention_uid": champs["{CONVENTION_ID_STABLE}"],
            "snapshot_schema": snapshot.get("schema"),
            "snapshot_sha256": convention.get("empreinte_sha256"),
            "champs": champs,
            "lignes_annexe": annexe,
        }
        contenu = json.dumps(
            paquet,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        paquet["empreinte_paquet_sha256"] = hashlib.sha256(contenu).hexdigest()
        return paquet
