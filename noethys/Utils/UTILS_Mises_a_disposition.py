#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Licence :        GNU GPL
#------------------------------------------------------------------------

"""Règles métier pures pour les mises à disposition.

Ce module ne dépend volontairement ni de wxPython ni de GestionDB. Il sert de
noyau commun aux écrans, aux éditions de conventions/avenants, au reporting et
aux futurs échanges avec PMSL-Équipe.
"""

import datetime
import uuid
from decimal import Decimal, InvalidOperation


STATUT_BROUILLON = "brouillon"
STATUT_VALIDEE = "validee"
STATUT_SIGNEE = "signee"
STATUT_TERMINEE = "terminee"
STATUT_ANNULEE = "annulee"

STATUTS = (
    STATUT_BROUILLON,
    STATUT_VALIDEE,
    STATUT_SIGNEE,
    STATUT_TERMINEE,
    STATUT_ANNULEE,
)

FACTURATION_MANUELLE = "manuelle"
FACTURATION_MENSUELLE = "mensuelle"
FACTURATION_TRIMESTRIELLE = "trimestrielle"
FACTURATION_APRES_REALISE = "apres_realise"

MODES_FACTURATION = (
    FACTURATION_MANUELLE,
    FACTURATION_MENSUELLE,
    FACTURATION_TRIMESTRIELLE,
    FACTURATION_APRES_REALISE,
)

TYPE_ASSOCIATION = "association"
TYPE_ECOLE = "ecole"
TYPE_COLLECTIVITE = "collectivite"
TYPE_ORGANISME = "organisme"
TYPE_ENTREPRISE = "entreprise"
TYPE_AUTRE = "autre"

TYPES_STRUCTURE = (
    TYPE_ASSOCIATION,
    TYPE_ECOLE,
    TYPE_COLLECTIVITE,
    TYPE_ORGANISME,
    TYPE_ENTREPRISE,
    TYPE_AUTRE,
)

ROLE_CONTACT_PRESIDENCE = "presidence"
ROLE_CONTACT_TRESORERIE = "tresorerie"
ROLE_CONTACT_DIRECTION = "direction"
ROLE_CONTACT_APEL = "apel"
ROLE_CONTACT_SECTION = "responsable_section"
ROLE_CONTACT_PLANNING = "planning"
ROLE_CONTACT_FACTURATION = "facturation"
ROLE_CONTACT_CONVENTION = "convention"
ROLE_CONTACT_ADMINISTRATIF = "administratif"
ROLE_CONTACT_URGENCE = "urgence"

ROLES_CONTACT = (
    ROLE_CONTACT_PRESIDENCE,
    ROLE_CONTACT_TRESORERIE,
    ROLE_CONTACT_DIRECTION,
    ROLE_CONTACT_APEL,
    ROLE_CONTACT_SECTION,
    ROLE_CONTACT_PLANNING,
    ROLE_CONTACT_FACTURATION,
    ROLE_CONTACT_CONVENTION,
    ROLE_CONTACT_ADMINISTRATIF,
    ROLE_CONTACT_URGENCE,
)

ADHESION_REQUISE = "requise"
ADHESION_NON_REQUISE = "non_requise"
ADHESION_NON_APPLICABLE = "non_applicable"
ADHESION_EXONEREE = "exoneree"

REGLES_ADHESION = (
    ADHESION_REQUISE,
    ADHESION_NON_REQUISE,
    ADHESION_NON_APPLICABLE,
    ADHESION_EXONEREE,
)

UNITE_HEURE = "heure"
UNITE_SEANCE = "seance"
UNITE_FORFAIT = "forfait"
UNITE_JOURNEE = "journee"

UNITES_TARIF = (
    UNITE_HEURE,
    UNITE_SEANCE,
    UNITE_FORFAIT,
    UNITE_JOURNEE,
)


def _GetDate(valeur, nom_champ):
    """Retourne une date à partir d'une date, datetime ou chaîne ISO."""
    if valeur in (None, ""):
        return None
    if isinstance(valeur, datetime.datetime):
        return valeur.date()
    if isinstance(valeur, datetime.date):
        return valeur
    if isinstance(valeur, str):
        try:
            return datetime.datetime.strptime(valeur, "%Y-%m-%d").date()
        except ValueError:
            pass
    raise ValueError("%s doit être une date ou une date ISO YYYY-MM-DD" % nom_champ)


def _GetUUID(valeur, nom_champ, obligatoire=True):
    """Normalise un identifiant stable UUID sous forme de chaîne."""
    if valeur in (None, ""):
        if obligatoire:
            return str(uuid.uuid4())
        return None
    try:
        return str(uuid.UUID(str(valeur)))
    except (ValueError, AttributeError, TypeError):
        raise ValueError("%s doit être un UUID valide" % nom_champ)


def _GetDecimal(valeur, nom_champ, obligatoire=False):
    if valeur in (None, ""):
        if obligatoire:
            raise ValueError("%s est obligatoire" % nom_champ)
        return None
    try:
        resultat = Decimal(str(valeur))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("%s doit être un nombre décimal valide" % nom_champ)
    if resultat < 0:
        raise ValueError("%s ne peut pas être négatif" % nom_champ)
    return resultat


def _FormatDate(valeur):
    if valeur is None:
        return ""
    return valeur.strftime("%d/%m/%Y")


def _FormatDecimal(valeur):
    if valeur is None:
        return ""
    return format(valeur, "f")


def _NettoyerRoles(roles):
    resultat = []
    for role in roles or ():
        role = (role or "").strip()
        if role not in ROLES_CONTACT:
            raise ValueError("rôle de contact inconnu : %s" % role)
        if role not in resultat:
            resultat.append(role)
    return tuple(resultat)


class StructureMiseADisposition(object):
    """Structure bénéficiaire, payeuse ou partenaire d'une mise à disposition.

    Une école peut être représentée ici comme structure opérationnelle même si
    son payeur juridique est une mairie, un OGEC ou une autre entité.
    """

    def __init__(
        self,
        nom,
        type_structure=TYPE_ASSOCIATION,
        identifiant_stable=None,
        siret="",
        siren="",
        rna="",
        code_ape="",
        rue="",
        cp="",
        ville="",
        mail="",
        telephone="",
    ):
        self.nom = (nom or "").strip()
        self.type_structure = type_structure
        self.identifiant_stable = _GetUUID(
            identifiant_stable, "identifiant_stable", obligatoire=True
        )
        self.siret = (siret or "").strip()
        self.siren = (siren or "").strip()
        self.rna = (rna or "").strip()
        self.code_ape = (code_ape or "").strip()
        self.rue = (rue or "").strip()
        self.cp = (cp or "").strip()
        self.ville = (ville or "").strip()
        self.mail = (mail or "").strip()
        self.telephone = (telephone or "").strip()
        self.Validation()

    def Validation(self):
        if not self.nom:
            raise ValueError("nom de structure obligatoire")
        if self.type_structure not in TYPES_STRUCTURE:
            raise ValueError("type de structure inconnu : %s" % self.type_structure)
        return True

    def GetChampsFusion(self, prefixe="STRUCTURE"):
        prefixe = (prefixe or "STRUCTURE").strip().upper()
        return {
            "{%s_ID_STABLE}" % prefixe: self.identifiant_stable,
            "{%s_NOM}" % prefixe: self.nom,
            "{%s_TYPE}" % prefixe: self.type_structure,
            "{%s_SIRET}" % prefixe: self.siret,
            "{%s_SIREN}" % prefixe: self.siren,
            "{%s_RNA}" % prefixe: self.rna,
            "{%s_APE}" % prefixe: self.code_ape,
            "{%s_RUE}" % prefixe: self.rue,
            "{%s_CP}" % prefixe: self.cp,
            "{%s_VILLE}" % prefixe: self.ville,
            "{%s_MAIL}" % prefixe: self.mail,
            "{%s_TELEPHONE}" % prefixe: self.telephone,
        }

    def GetDonnees(self):
        return {
            "identifiant_stable": self.identifiant_stable,
            "nom": self.nom,
            "type_structure": self.type_structure,
            "siret": self.siret,
            "siren": self.siren,
            "rna": self.rna,
            "code_ape": self.code_ape,
            "rue": self.rue,
            "cp": self.cp,
            "ville": self.ville,
            "mail": self.mail,
            "telephone": self.telephone,
        }


class ContactStructure(object):
    """Contact d'une structure avec un ou plusieurs rôles métier."""

    def __init__(
        self,
        identifiant_structure,
        nom,
        prenom="",
        roles=None,
        identifiant_stable=None,
        fonction="",
        mail="",
        telephone="",
    ):
        self.identifiant_structure = _GetUUID(
            identifiant_structure, "identifiant_structure", obligatoire=True
        )
        self.identifiant_stable = _GetUUID(
            identifiant_stable, "identifiant_stable", obligatoire=True
        )
        self.nom = (nom or "").strip()
        self.prenom = (prenom or "").strip()
        self.fonction = (fonction or "").strip()
        self.mail = (mail or "").strip()
        self.telephone = (telephone or "").strip()
        self.roles = _NettoyerRoles(roles)
        self.Validation()

    def Validation(self):
        if not self.nom:
            raise ValueError("nom du contact obligatoire")
        return True

    def ALeRole(self, role):
        return role in self.roles

    def GetNomComplet(self):
        return " ".join([valeur for valeur in (self.prenom, self.nom) if valeur])

    def GetChampsFusion(self, prefixe="CONTACT"):
        prefixe = (prefixe or "CONTACT").strip().upper()
        return {
            "{%s_ID_STABLE}" % prefixe: self.identifiant_stable,
            "{%s_STRUCTURE_ID_STABLE}" % prefixe: self.identifiant_structure,
            "{%s_NOM}" % prefixe: self.nom,
            "{%s_PRENOM}" % prefixe: self.prenom,
            "{%s_NOM_COMPLET}" % prefixe: self.GetNomComplet(),
            "{%s_FONCTION}" % prefixe: self.fonction,
            "{%s_MAIL}" % prefixe: self.mail,
            "{%s_TELEPHONE}" % prefixe: self.telephone,
            "{%s_ROLES}" % prefixe: ",".join(self.roles),
        }

    def GetDonnees(self):
        return {
            "identifiant_stable": self.identifiant_stable,
            "identifiant_structure": self.identifiant_structure,
            "nom": self.nom,
            "prenom": self.prenom,
            "fonction": self.fonction,
            "mail": self.mail,
            "telephone": self.telephone,
            "roles": list(self.roles),
        }


class RelationContractuelleMiseADisposition(object):
    """Règles commerciales attachées à une relation, pas au type de structure."""

    def __init__(
        self,
        identifiant_beneficiaire,
        saison,
        activite,
        identifiant_payeur=None,
        groupe="",
        tarif_unitaire=None,
        unite_tarif=UNITE_HEURE,
        regle_adhesion=ADHESION_NON_REQUISE,
        mode_facturation=FACTURATION_MANUELLE,
        identifiant_stable=None,
    ):
        self.identifiant_beneficiaire = _GetUUID(
            identifiant_beneficiaire, "identifiant_beneficiaire", obligatoire=True
        )
        self.identifiant_payeur = _GetUUID(
            identifiant_payeur, "identifiant_payeur", obligatoire=False
        ) or self.identifiant_beneficiaire
        self.identifiant_stable = _GetUUID(
            identifiant_stable, "identifiant_stable", obligatoire=True
        )
        self.saison = (saison or "").strip()
        self.activite = (activite or "").strip()
        self.groupe = (groupe or "").strip()
        self.tarif_unitaire = _GetDecimal(
            tarif_unitaire, "tarif_unitaire", obligatoire=False
        )
        self.unite_tarif = unite_tarif
        self.regle_adhesion = regle_adhesion
        self.mode_facturation = mode_facturation
        self.Validation()

    def Validation(self):
        if not self.saison:
            raise ValueError("saison obligatoire")
        if not self.activite:
            raise ValueError("activité obligatoire")
        if self.unite_tarif not in UNITES_TARIF:
            raise ValueError("unité tarifaire inconnue : %s" % self.unite_tarif)
        if self.regle_adhesion not in REGLES_ADHESION:
            raise ValueError("règle d'adhésion inconnue : %s" % self.regle_adhesion)
        if self.mode_facturation not in MODES_FACTURATION:
            raise ValueError(
                "mode de facturation inconnu : %s" % self.mode_facturation
            )
        return True

    def EstPayeurDistinct(self):
        return self.identifiant_payeur != self.identifiant_beneficiaire

    def GetChampsFusion(self):
        return {
            "{RELATION_ID_STABLE}": self.identifiant_stable,
            "{RELATION_BENEFICIAIRE_ID_STABLE}": self.identifiant_beneficiaire,
            "{RELATION_PAYEUR_ID_STABLE}": self.identifiant_payeur,
            "{RELATION_PAYEUR_DISTINCT}": "1" if self.EstPayeurDistinct() else "0",
            "{RELATION_SAISON}": self.saison,
            "{RELATION_ACTIVITE}": self.activite,
            "{RELATION_GROUPE}": self.groupe,
            "{RELATION_TARIF_UNITAIRE}": _FormatDecimal(self.tarif_unitaire),
            "{RELATION_UNITE_TARIF}": self.unite_tarif,
            "{RELATION_ADHESION}": self.regle_adhesion,
            "{RELATION_MODE_FACTURATION}": self.mode_facturation,
        }

    def GetDonnees(self):
        return {
            "identifiant_stable": self.identifiant_stable,
            "identifiant_beneficiaire": self.identifiant_beneficiaire,
            "identifiant_payeur": self.identifiant_payeur,
            "saison": self.saison,
            "activite": self.activite,
            "groupe": self.groupe,
            "tarif_unitaire": (
                _FormatDecimal(self.tarif_unitaire)
                if self.tarif_unitaire is not None
                else None
            ),
            "unite_tarif": self.unite_tarif,
            "regle_adhesion": self.regle_adhesion,
            "mode_facturation": self.mode_facturation,
        }


class ConventionMiseADisposition(object):
    """Représentation canonique d'une convention ou d'un avenant."""

    def __init__(
        self,
        date_debut,
        date_fin=None,
        reference="",
        statut=STATUT_BROUILLON,
        mode_facturation=FACTURATION_MANUELLE,
        version=1,
        identifiant_stable=None,
        identifiant_parent=None,
        identifiant_relation=None,
    ):
        self.date_debut = _GetDate(date_debut, "date_debut")
        self.date_fin = _GetDate(date_fin, "date_fin")
        self.reference = (reference or "").strip()
        self.statut = statut
        self.mode_facturation = mode_facturation
        self.version = int(version)
        self.identifiant_stable = _GetUUID(
            identifiant_stable, "identifiant_stable", obligatoire=True
        )
        self.identifiant_parent = _GetUUID(
            identifiant_parent, "identifiant_parent", obligatoire=False
        )
        self.identifiant_relation = _GetUUID(
            identifiant_relation, "identifiant_relation", obligatoire=False
        )
        self.Validation()

    def Validation(self):
        if self.date_debut is None:
            raise ValueError("date_debut est obligatoire")
        if self.date_fin is not None and self.date_fin < self.date_debut:
            raise ValueError("date_fin ne peut pas précéder date_debut")
        if self.statut not in STATUTS:
            raise ValueError("statut de convention inconnu : %s" % self.statut)
        if self.mode_facturation not in MODES_FACTURATION:
            raise ValueError(
                "mode de facturation inconnu : %s" % self.mode_facturation
            )
        if self.version < 1:
            raise ValueError("version doit être supérieure ou égale à 1")
        if self.identifiant_parent == self.identifiant_stable:
            raise ValueError("une convention ne peut pas être son propre parent")
        if self.identifiant_parent is not None and self.version < 2:
            raise ValueError("un avenant doit avoir une version supérieure à 1")
        return True

    def EstAvenant(self):
        return self.identifiant_parent is not None

    def EstActiveA(self, date_reference):
        """Indique si la période contractuelle couvre une date donnée.

        Le statut n'est volontairement pas utilisé ici : période de validité et
        état de traitement sont deux informations distinctes.
        """
        date_reference = _GetDate(date_reference, "date_reference")
        if date_reference < self.date_debut:
            return False
        if self.date_fin is not None and date_reference > self.date_fin:
            return False
        return True

    def GetChampsFusion(self):
        """Retourne les champs canoniques utilisables par le moteur documentaire."""
        return {
            "{CONVENTION_ID_STABLE}": self.identifiant_stable,
            "{CONVENTION_RELATION_ID_STABLE}": self.identifiant_relation or "",
            "{CONVENTION_REFERENCE}": self.reference,
            "{CONVENTION_VERSION}": str(self.version),
            "{CONVENTION_STATUT}": self.statut,
            "{CONVENTION_DATE_DEBUT}": _FormatDate(self.date_debut),
            "{CONVENTION_DATE_FIN}": _FormatDate(self.date_fin),
            "{CONVENTION_MODE_FACTURATION}": self.mode_facturation,
            "{CONVENTION_PARENT_ID_STABLE}": self.identifiant_parent or "",
            "{CONVENTION_EST_AVENANT}": "1" if self.EstAvenant() else "0",
        }

    def GetDonnees(self):
        """Retourne un dictionnaire sérialisable sans dépendance de stockage."""
        return {
            "identifiant_stable": self.identifiant_stable,
            "identifiant_parent": self.identifiant_parent,
            "identifiant_relation": self.identifiant_relation,
            "reference": self.reference,
            "version": self.version,
            "statut": self.statut,
            "mode_facturation": self.mode_facturation,
            "date_debut": self.date_debut.isoformat(),
            "date_fin": self.date_fin.isoformat() if self.date_fin else None,
        }
