#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Service métier des conventions et avenants Noe-062.

La relation contractuelle reste la source des règles commerciales. Une
convention référence cette relation et fige, lors de sa validation, un snapshot
JSON canonique + une empreinte SHA-256. Une version validée/signée n'est jamais
réécrite comme un brouillon : les changements contractuels passent par un
avenant/version suivante.
"""
from __future__ import unicode_literals

import datetime
import hashlib
import json
import uuid

from Utils import UTILS_Relations_Structures


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

STATUTS_PARENT_AVENANT = (
    STATUT_VALIDEE,
    STATUT_SIGNEE,
    STATUT_TERMINEE,
)

CHAMPS_CONVENTION = (
    "uid",
    "IDrelation_structure",
    "IDconvention_parent",
    "reference",
    "version",
    "statut",
    "date_debut",
    "date_fin",
    "objet",
    "notes",
    "snapshot_contractuel",
    "empreinte_sha256",
    "date_validation",
    "date_signature",
    "actif",
    "date_creation",
    "date_modification",
)

CHAMPS_TEXTE = (
    "reference",
    "objet",
    "notes",
)

CHAMPS_RELATION_SNAPSHOT = (
    "uid",
    "IDstructure",
    "IDgroupe_structure",
    "IDactivite",
    "type_relation",
    "libelle",
    "saison",
    "fonction_intervenant",
    "IDintervenant_externe",
    "nom_intervenant",
    "date_debut",
    "date_fin",
    "tarif",
    "unite_tarif",
    "regle_adhesion",
    "mode_facturation",
    "jour_facturation",
    "memo",
)

CHAMPS_PAYEUR_SNAPSHOT = (
    "IDpayeur_structure",
    "type_payeur",
    "IDfamille",
    "IDstructure_payeur",
    "libelle_payeur",
    "taux_prise_en_charge",
    "montant_plafond",
    "date_debut",
    "date_fin",
    "reference",
    "implicite",
)


def _texte(valeur):
    if valeur is None:
        return u""
    try:
        return valeur.strip()
    except Exception:
        return valeur


def _date_iso(valeur, nom_champ, obligatoire=False):
    if valeur in (None, ""):
        if obligatoire:
            raise ValueError("%s est obligatoire" % nom_champ)
        return None
    if isinstance(valeur, datetime.datetime):
        valeur = valeur.date()
    if isinstance(valeur, datetime.date):
        return valeur.isoformat()
    valeur = _texte(valeur)
    try:
        return datetime.datetime.strptime(valeur, "%Y-%m-%d").date().isoformat()
    except (TypeError, ValueError):
        raise ValueError("%s doit être une date ISO YYYY-MM-DD" % nom_champ)


def _date_maintenant(date=None):
    if date is None:
        return datetime.date.today().isoformat()
    return _date_iso(date, "date", obligatoire=True)


def _entier_positif(valeur, nom_champ, obligatoire=False):
    if valeur in (None, "", 0, "0"):
        if obligatoire:
            raise ValueError("%s est obligatoire" % nom_champ)
        return None
    try:
        valeur = int(valeur)
    except (TypeError, ValueError):
        raise ValueError("%s doit être un entier" % nom_champ)
    if valeur <= 0:
        raise ValueError("%s doit être positif" % nom_champ)
    return valeur


def _uid_convention(valeur=None, generer=True):
    valeur = _texte(valeur)
    if not valeur:
        if not generer:
            raise ValueError("UID de convention obligatoire")
        return "CONV-%s" % uuid.uuid4().hex
    if len(valeur) > 64 or not all(ch.isalnum() or ch in "-_" for ch in valeur):
        raise ValueError("UID de convention invalide")
    return valeur


def _verifier_periode(date_debut, date_fin):
    if date_debut and date_fin and date_fin < date_debut:
        raise ValueError("date_fin ne peut pas précéder date_debut")


def _liste_pairs(donnees, ordre):
    return [(champ, donnees.get(champ)) for champ in ordre if champ in donnees]


def _normaliser_json(valeur):
    """Produit une structure JSON stable sans objets métier implicites."""
    if valeur is None or isinstance(valeur, (bool, int, float, str)):
        return valeur
    if isinstance(valeur, bytes):
        return valeur.decode("utf-8")
    if isinstance(valeur, datetime.datetime):
        return valeur.isoformat()
    if isinstance(valeur, datetime.date):
        return valeur.isoformat()
    if isinstance(valeur, (list, tuple)):
        return [_normaliser_json(item) for item in valeur]
    if isinstance(valeur, dict):
        return dict((str(cle), _normaliser_json(item)) for cle, item in valeur.items())
    raise ValueError("Valeur non sérialisable dans le snapshot: %r" % (valeur,))


def _serialiser_snapshot(snapshot):
    normalise = _normaliser_json(snapshot)
    texte = json.dumps(
        normalise,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return texte.encode("utf-8")


def _empreinte(contenu):
    if isinstance(contenu, str):
        contenu = contenu.encode("utf-8")
    return hashlib.sha256(contenu).hexdigest()


def _decoder_snapshot(contenu):
    if contenu in (None, b"", ""):
        return None
    if isinstance(contenu, bytes):
        contenu = contenu.decode("utf-8")
    return json.loads(contenu)


def NormaliserConvention(donnees, creation=True, date=None):
    donnees = dict(donnees or {})
    if not donnees:
        raise ValueError("Aucune donnée de convention")

    resultat = {}
    if creation:
        resultat["uid"] = _uid_convention(donnees.get("uid"), generer=True)
        resultat["IDrelation_structure"] = _entier_positif(
            donnees.get("IDrelation_structure"), "IDrelation_structure", obligatoire=True
        )
        resultat["IDconvention_parent"] = _entier_positif(
            donnees.get("IDconvention_parent"), "IDconvention_parent"
        )
        try:
            version = int(donnees.get("version", 1))
        except (TypeError, ValueError):
            raise ValueError("version doit être un entier")
        if version < 1:
            raise ValueError("version doit être supérieure ou égale à 1")
        resultat["version"] = version
        statut = _texte(donnees.get("statut")) or STATUT_BROUILLON
        if statut != STATUT_BROUILLON:
            raise ValueError("Une convention doit être créée en brouillon")
        resultat["statut"] = statut
    else:
        # Identité, relation, parent, version et statut sont gérés par le workflow.
        interdits = (
            "uid",
            "IDrelation_structure",
            "IDconvention_parent",
            "version",
            "statut",
            "snapshot_contractuel",
            "empreinte_sha256",
            "date_validation",
            "date_signature",
            "date_creation",
        )
        if any(champ in donnees for champ in interdits):
            raise ValueError("Modification directe d'un champ contractuel protégé")

    for champ in CHAMPS_TEXTE:
        if creation or champ in donnees:
            resultat[champ] = _texte(donnees.get(champ))

    date_debut = None
    date_fin = None
    if creation or "date_debut" in donnees:
        date_debut = _date_iso(
            donnees.get("date_debut"), "date_debut", obligatoire=creation
        )
        resultat["date_debut"] = date_debut
    if creation or "date_fin" in donnees:
        date_fin = _date_iso(donnees.get("date_fin"), "date_fin")
        resultat["date_fin"] = date_fin
    if creation:
        _verifier_periode(date_debut, date_fin)

    if creation:
        resultat["snapshot_contractuel"] = None
        resultat["empreinte_sha256"] = ""
        resultat["date_validation"] = None
        resultat["date_signature"] = None
    if creation or "actif" in donnees:
        resultat["actif"] = 1 if donnees.get("actif", 1) not in (0, False, "0") else 0

    resultat["date_modification"] = _date_maintenant(date)
    if creation:
        resultat["date_creation"] = _date_iso(
            donnees.get("date_creation") or date or datetime.date.today(),
            "date_creation",
            obligatoire=True,
        )
    return resultat


class GestionnaireConventionsStructures(object):
    def __init__(self, db):
        self.db = db
        self.relations = UTILS_Relations_Structures.GestionnaireRelationsStructures(db)

    def LireConvention(self, IDconvention_structure):
        IDconvention_structure = _entier_positif(
            IDconvention_structure, "IDconvention_structure", obligatoire=True
        )
        req = "SELECT IDconvention_structure, %s FROM structures_conventions WHERE IDconvention_structure=%d;" % (
            ", ".join(CHAMPS_CONVENTION), IDconvention_structure
        )
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq() or []
        if not lignes:
            return None
        return dict(zip(("IDconvention_structure",) + CHAMPS_CONVENTION, lignes[0]))

    def LireConventionParUID(self, uid):
        uid = _uid_convention(uid, generer=False)
        req = "SELECT IDconvention_structure, %s FROM structures_conventions WHERE uid='%s';" % (
            ", ".join(CHAMPS_CONVENTION), uid
        )
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq() or []
        if not lignes:
            return None
        if len(lignes) > 1:
            raise RuntimeError("UID de convention dupliqué")
        return dict(zip(("IDconvention_structure",) + CHAMPS_CONVENTION, lignes[0]))

    def ListerConventions(self, IDrelation_structure=None, actifs_seulement=True):
        conditions = []
        if IDrelation_structure:
            conditions.append("IDrelation_structure=%d" % int(IDrelation_structure))
        if actifs_seulement:
            conditions.append("actif=1")
        req = "SELECT IDconvention_structure, %s FROM structures_conventions" % ", ".join(CHAMPS_CONVENTION)
        if conditions:
            req += " WHERE " + " AND ".join(conditions)
        req += " ORDER BY IDrelation_structure, version, IDconvention_structure;"
        if self.db.ExecuterReq(req) != 1:
            return []
        return [
            dict(zip(("IDconvention_structure",) + CHAMPS_CONVENTION, ligne))
            for ligne in (self.db.ResultatReq() or [])
        ]

    def _version_existe(self, IDrelation_structure, version):
        req = (
            "SELECT IDconvention_structure FROM structures_conventions "
            "WHERE IDrelation_structure=%d AND version=%d;"
        ) % (int(IDrelation_structure), int(version))
        if self.db.ExecuterReq(req) != 1:
            return False
        return bool(self.db.ResultatReq() or [])

    def _verifier_periode_relation(self, relation, date_debut, date_fin):
        debut_relation = relation.get("date_debut")
        fin_relation = relation.get("date_fin")
        if debut_relation and date_debut and date_debut < debut_relation:
            raise ValueError("La convention débute avant la relation contractuelle")
        if fin_relation and date_fin and date_fin > fin_relation:
            raise ValueError("La convention se termine après la relation contractuelle")
        if fin_relation and not date_fin:
            raise ValueError("Une relation bornée exige une date_fin de convention")

    def CreerConvention(self, donnees, date=None):
        valeurs = NormaliserConvention(donnees, creation=True, date=date)
        if valeurs.get("IDconvention_parent"):
            raise ValueError("Utiliser CreerAvenant pour créer une version dérivée")
        if valeurs["version"] != 1:
            raise ValueError("Une convention initiale doit être en version 1")
        relation = self.relations.LireRelation(valeurs["IDrelation_structure"])
        if not relation:
            raise ValueError("Relation contractuelle introuvable")
        if self.LireConventionParUID(valeurs["uid"]):
            raise ValueError("UID de convention déjà utilisé")
        if self._version_existe(valeurs["IDrelation_structure"], 1):
            raise ValueError("Une convention initiale existe déjà pour cette relation")
        self._verifier_periode_relation(
            relation, valeurs.get("date_debut"), valeurs.get("date_fin")
        )
        return self.db.ReqInsert(
            "structures_conventions", _liste_pairs(valeurs, CHAMPS_CONVENTION)
        )

    def CreerAvenant(self, IDconvention_parent, donnees=None, date=None):
        parent = self.LireConvention(IDconvention_parent)
        if not parent:
            raise ValueError("Convention parente introuvable")
        if parent["statut"] not in STATUTS_PARENT_AVENANT:
            raise ValueError("Le parent doit être validé, signé ou terminé")
        donnees = dict(donnees or {})
        donnees["IDrelation_structure"] = parent["IDrelation_structure"]
        donnees["IDconvention_parent"] = parent["IDconvention_structure"]
        donnees["version"] = int(parent["version"]) + 1
        donnees["statut"] = STATUT_BROUILLON
        donnees.setdefault("date_debut", parent["date_debut"])
        donnees.setdefault("date_fin", parent["date_fin"])
        valeurs = NormaliserConvention(donnees, creation=True, date=date)
        if self._version_existe(valeurs["IDrelation_structure"], valeurs["version"]):
            raise ValueError("Cette version existe déjà pour la relation")
        relation = self.relations.LireRelation(valeurs["IDrelation_structure"])
        if not relation:
            raise ValueError("Relation contractuelle introuvable")
        if self.LireConventionParUID(valeurs["uid"]):
            raise ValueError("UID de convention déjà utilisé")
        self._verifier_periode_relation(
            relation, valeurs.get("date_debut"), valeurs.get("date_fin")
        )
        return self.db.ReqInsert(
            "structures_conventions", _liste_pairs(valeurs, CHAMPS_CONVENTION)
        )

    def ModifierConvention(self, IDconvention_structure, donnees, date=None):
        courant = self.LireConvention(IDconvention_structure)
        if not courant:
            raise ValueError("Convention introuvable")
        if courant["statut"] != STATUT_BROUILLON:
            raise ValueError("Une version figée ne peut plus être modifiée")
        changements = NormaliserConvention(donnees, creation=False, date=date)
        date_debut = changements.get("date_debut", courant.get("date_debut"))
        date_fin = changements.get("date_fin", courant.get("date_fin"))
        _verifier_periode(date_debut, date_fin)
        relation = self.relations.LireRelation(courant["IDrelation_structure"])
        if not relation:
            raise ValueError("Relation contractuelle introuvable")
        self._verifier_periode_relation(relation, date_debut, date_fin)
        return self.db.ReqMAJ(
            "structures_conventions",
            _liste_pairs(changements, CHAMPS_CONVENTION),
            "IDconvention_structure",
            int(IDconvention_structure),
        )

    def ConstruireSnapshotContractuel(self, IDconvention_structure, complements=None):
        convention = self.LireConvention(IDconvention_structure)
        if not convention:
            raise ValueError("Convention introuvable")
        relation = self.relations.LireRelation(convention["IDrelation_structure"])
        if not relation:
            raise ValueError("Relation contractuelle introuvable")
        payeurs = self.relations.ListerPayeursEffectifs(convention["IDrelation_structure"])

        convention_snapshot = {
            "uid": convention["uid"],
            "IDconvention_parent": convention.get("IDconvention_parent"),
            "reference": convention.get("reference") or "",
            "version": int(convention["version"]),
            "date_debut": convention.get("date_debut"),
            "date_fin": convention.get("date_fin"),
            "objet": convention.get("objet") or "",
        }
        relation_snapshot = dict(
            (champ, relation.get(champ)) for champ in CHAMPS_RELATION_SNAPSHOT
        )
        payeurs_snapshot = [
            dict((champ, payeur.get(champ)) for champ in CHAMPS_PAYEUR_SNAPSHOT)
            for payeur in payeurs
        ]
        snapshot = {
            "schema": "noe-062-convention-v1",
            "convention": convention_snapshot,
            "relation": relation_snapshot,
            "payeurs": payeurs_snapshot,
        }
        if complements not in (None, {}):
            snapshot["complements"] = _normaliser_json(complements)
        return _normaliser_json(snapshot)

    def ValiderConvention(self, IDconvention_structure, complements=None, date=None):
        convention = self.LireConvention(IDconvention_structure)
        if not convention:
            raise ValueError("Convention introuvable")
        if convention["statut"] != STATUT_BROUILLON:
            raise ValueError("Seul un brouillon peut être validé")
        snapshot = self.ConstruireSnapshotContractuel(
            IDconvention_structure, complements=complements
        )
        contenu = _serialiser_snapshot(snapshot)
        valeurs = {
            "statut": STATUT_VALIDEE,
            "snapshot_contractuel": contenu,
            "empreinte_sha256": _empreinte(contenu),
            "date_validation": _date_maintenant(date),
            "date_modification": _date_maintenant(date),
        }
        return self.db.ReqMAJ(
            "structures_conventions",
            _liste_pairs(valeurs, CHAMPS_CONVENTION),
            "IDconvention_structure",
            int(IDconvention_structure),
        )

    def VerifierIntegrite(self, IDconvention_structure):
        convention = self.LireConvention(IDconvention_structure)
        if not convention:
            raise ValueError("Convention introuvable")
        contenu = convention.get("snapshot_contractuel")
        empreinte = _texte(convention.get("empreinte_sha256"))
        if contenu in (None, b"", "") or not empreinte:
            return False
        return _empreinte(contenu) == empreinte

    def LireSnapshot(self, IDconvention_structure):
        convention = self.LireConvention(IDconvention_structure)
        if not convention:
            raise ValueError("Convention introuvable")
        if not self.VerifierIntegrite(IDconvention_structure):
            raise ValueError("Intégrité du snapshot contractuel invalide")
        return _decoder_snapshot(convention.get("snapshot_contractuel"))

    def SignerConvention(self, IDconvention_structure, date=None):
        convention = self.LireConvention(IDconvention_structure)
        if not convention:
            raise ValueError("Convention introuvable")
        if convention["statut"] == STATUT_SIGNEE:
            return True
        if convention["statut"] != STATUT_VALIDEE:
            raise ValueError("Seule une convention validée peut être signée")
        if not self.VerifierIntegrite(IDconvention_structure):
            raise ValueError("Snapshot contractuel absent ou altéré")
        valeurs = {
            "statut": STATUT_SIGNEE,
            "date_signature": _date_maintenant(date),
            "date_modification": _date_maintenant(date),
        }
        return self.db.ReqMAJ(
            "structures_conventions",
            _liste_pairs(valeurs, CHAMPS_CONVENTION),
            "IDconvention_structure",
            int(IDconvention_structure),
        )

    def TerminerConvention(self, IDconvention_structure, date=None):
        convention = self.LireConvention(IDconvention_structure)
        if not convention:
            raise ValueError("Convention introuvable")
        if convention["statut"] == STATUT_TERMINEE:
            return True
        if convention["statut"] not in (STATUT_VALIDEE, STATUT_SIGNEE):
            raise ValueError("Convention non terminable dans son état actuel")
        if not self.VerifierIntegrite(IDconvention_structure):
            raise ValueError("Snapshot contractuel absent ou altéré")
        valeurs = {
            "statut": STATUT_TERMINEE,
            "date_modification": _date_maintenant(date),
        }
        return self.db.ReqMAJ(
            "structures_conventions",
            _liste_pairs(valeurs, CHAMPS_CONVENTION),
            "IDconvention_structure",
            int(IDconvention_structure),
        )

    def AnnulerConvention(self, IDconvention_structure, date=None):
        convention = self.LireConvention(IDconvention_structure)
        if not convention:
            raise ValueError("Convention introuvable")
        if convention["statut"] == STATUT_ANNULEE:
            return True
        valeurs = {
            "statut": STATUT_ANNULEE,
            "date_modification": _date_maintenant(date),
        }
        return self.db.ReqMAJ(
            "structures_conventions",
            _liste_pairs(valeurs, CHAMPS_CONVENTION),
            "IDconvention_structure",
            int(IDconvention_structure),
        )

    def ArchiverConvention(self, IDconvention_structure, date=None):
        convention = self.LireConvention(IDconvention_structure)
        if not convention:
            raise ValueError("Convention introuvable")
        if convention["statut"] not in (STATUT_TERMINEE, STATUT_ANNULEE):
            raise ValueError("Seule une version terminée ou annulée peut être archivée")
        valeurs = {
            "actif": 0,
            "date_modification": _date_maintenant(date),
        }
        return self.db.ReqMAJ(
            "structures_conventions",
            _liste_pairs(valeurs, CHAMPS_CONVENTION),
            "IDconvention_structure",
            int(IDconvention_structure),
        )
