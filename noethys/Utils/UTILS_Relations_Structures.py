#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Relations contractuelles et prises en charge du référentiel Noe-062.

Ce module ne génère ni prestation, ni facture, ni document. Il conserve les
règles canoniques qui alimenteront ces moteurs historiques : bénéficiaire,
payeur/financeur, période, tarif de référence, adhésion et périodicité.
"""
from __future__ import unicode_literals

import datetime
import uuid
from decimal import Decimal, InvalidOperation


TYPES_RELATION = (
    "mise_disposition",
    "prestation",
    "adhesion",
    "eps",
    "autre",
)

REGLES_ADHESION = (
    "requise",
    "non_requise",
    "non_applicable",
    "exoneree",
)

UNITES_TARIF = (
    "heure",
    "seance",
    "forfait",
    "journee",
    "autre",
)

ALIASES_UNITES_TARIF = {
    "séance": "seance",
    "jour": "journee",
}

MODES_FACTURATION = (
    "mensuel",
    "trimestriel",
    "apres_validation",
    "manuel",
    "autre",
)

ALIASES_MODES_FACTURATION = {
    "apres_realise": "apres_validation",
}

TYPES_PAYEUR = (
    "famille",
    "structure",
    "departement_ase",
    "autre",
)

CHAMPS_RELATION = (
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
    "actif",
    "memo",
    "date_creation",
    "date_modification",
)

CHAMPS_PAYEUR = (
    "IDrelation_structure",
    "type_payeur",
    "IDfamille",
    "IDstructure_payeur",
    "libelle_payeur",
    "taux_prise_en_charge",
    "montant_plafond",
    "date_debut",
    "date_fin",
    "reference",
    "actif",
    "date_creation",
    "date_modification",
)

CHAMPS_TEXTE_RELATION = (
    "libelle",
    "saison",
    "fonction_intervenant",
    "IDintervenant_externe",
    "nom_intervenant",
    "memo",
)

CHAMPS_TEXTE_PAYEUR = (
    "libelle_payeur",
    "reference",
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
    return _date_iso(date, "date")


def _entier_optionnel(valeur, nom_champ):
    if valeur in (None, "", 0, "0"):
        return None
    try:
        resultat = int(valeur)
    except (TypeError, ValueError):
        raise ValueError("%s doit être un identifiant entier" % nom_champ)
    if resultat <= 0:
        raise ValueError("%s doit être positif" % nom_champ)
    return resultat


def _nombre_optionnel(valeur, nom_champ, minimum=None, maximum=None):
    if valeur in (None, ""):
        return None
    try:
        resultat = Decimal(str(valeur))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("%s doit être un nombre" % nom_champ)
    if not resultat.is_finite():
        raise ValueError("%s doit être fini" % nom_champ)
    if minimum is not None and resultat < Decimal(str(minimum)):
        raise ValueError("%s est inférieur au minimum autorisé" % nom_champ)
    if maximum is not None and resultat > Decimal(str(maximum)):
        raise ValueError("%s dépasse le maximum autorisé" % nom_champ)
    # GestionDB/Noethys stocke historiquement ces montants dans des FLOAT.
    return float(resultat)


def _uid_relation(valeur=None):
    valeur = _texte(valeur)
    if not valeur:
        return "REL-%s" % uuid.uuid4().hex
    if len(valeur) > 64 or not all(ch.isalnum() or ch in "-_" for ch in valeur):
        raise ValueError("UID de relation invalide")
    return valeur


def _liste_pairs(donnees, ordre):
    return [(champ, donnees.get(champ)) for champ in ordre if champ in donnees]


def _verifier_periode(date_debut, date_fin):
    if date_debut and date_fin and date_fin < date_debut:
        raise ValueError("date_fin ne peut pas précéder date_debut")


def NormaliserRelation(donnees, creation=True, date=None):
    donnees = dict(donnees or {})
    if not donnees:
        raise ValueError("Aucune donnée de relation")

    if creation:
        IDstructure = _entier_optionnel(donnees.get("IDstructure"), "IDstructure")
        if not IDstructure:
            raise ValueError("IDstructure bénéficiaire obligatoire")
        type_relation = _texte(donnees.get("type_relation"))
        if not type_relation:
            raise ValueError("type_relation obligatoire")
        libelle = _texte(donnees.get("libelle"))
        if not libelle:
            raise ValueError("libelle obligatoire")
    else:
        IDstructure = None
        type_relation = None
        libelle = None
        if "IDstructure" in donnees:
            IDstructure = _entier_optionnel(donnees.get("IDstructure"), "IDstructure")
            if not IDstructure:
                raise ValueError("IDstructure bénéficiaire ne peut pas être vide")
        if "type_relation" in donnees:
            type_relation = _texte(donnees.get("type_relation"))
            if not type_relation:
                raise ValueError("type_relation ne peut pas être vide")
        if "libelle" in donnees:
            libelle = _texte(donnees.get("libelle"))
            if not libelle:
                raise ValueError("libelle ne peut pas être vide")

    if type_relation is not None and type_relation not in TYPES_RELATION:
        raise ValueError("type_relation inconnu: %s" % type_relation)

    resultat = {}
    if creation:
        resultat["uid"] = _uid_relation(donnees.get("uid"))
        resultat["IDstructure"] = IDstructure
        resultat["type_relation"] = type_relation
        resultat["libelle"] = libelle
    else:
        if "IDstructure" in donnees:
            resultat["IDstructure"] = IDstructure
        if "type_relation" in donnees:
            resultat["type_relation"] = type_relation
        if "libelle" in donnees:
            resultat["libelle"] = libelle

    if creation or "IDgroupe_structure" in donnees:
        resultat["IDgroupe_structure"] = _entier_optionnel(
            donnees.get("IDgroupe_structure"), "IDgroupe_structure"
        )
    if creation or "IDactivite" in donnees:
        resultat["IDactivite"] = _entier_optionnel(donnees.get("IDactivite"), "IDactivite")

    for champ in CHAMPS_TEXTE_RELATION:
        if champ == "libelle":
            continue
        if creation or champ in donnees:
            resultat[champ] = _texte(donnees.get(champ))

    date_debut = None
    date_fin = None
    if creation or "date_debut" in donnees:
        date_debut = _date_iso(donnees.get("date_debut"), "date_debut")
        resultat["date_debut"] = date_debut
    if creation or "date_fin" in donnees:
        date_fin = _date_iso(donnees.get("date_fin"), "date_fin")
        resultat["date_fin"] = date_fin
    if creation:
        _verifier_periode(date_debut, date_fin)

    if creation or "tarif" in donnees:
        resultat["tarif"] = _nombre_optionnel(donnees.get("tarif"), "tarif", minimum=0)

    if creation or "unite_tarif" in donnees:
        unite = _texte(donnees.get("unite_tarif")) or "heure"
        unite = ALIASES_UNITES_TARIF.get(unite, unite)
        if unite not in UNITES_TARIF:
            raise ValueError("unite_tarif inconnue: %s" % unite)
        resultat["unite_tarif"] = unite

    if creation or "regle_adhesion" in donnees:
        regle = _texte(donnees.get("regle_adhesion")) or "non_requise"
        if regle not in REGLES_ADHESION:
            raise ValueError("regle_adhesion inconnue: %s" % regle)
        resultat["regle_adhesion"] = regle

    if creation or "mode_facturation" in donnees:
        mode = _texte(donnees.get("mode_facturation")) or "manuel"
        mode = ALIASES_MODES_FACTURATION.get(mode, mode)
        if mode not in MODES_FACTURATION:
            raise ValueError("mode_facturation inconnu: %s" % mode)
        resultat["mode_facturation"] = mode

    if creation or "jour_facturation" in donnees:
        jour = _entier_optionnel(donnees.get("jour_facturation"), "jour_facturation")
        if jour is not None and not 1 <= jour <= 31:
            raise ValueError("jour_facturation doit être compris entre 1 et 31")
        resultat["jour_facturation"] = jour

    if creation or "actif" in donnees:
        resultat["actif"] = 1 if donnees.get("actif", 1) not in (0, False, "0") else 0
    if creation or "memo" in donnees:
        resultat["memo"] = _texte(donnees.get("memo"))

    resultat["date_modification"] = _date_maintenant(date)
    if creation:
        resultat["date_creation"] = _date_iso(
            donnees.get("date_creation") or date or datetime.date.today(),
            "date_creation",
            obligatoire=True,
        )
    return resultat


def NormaliserPayeur(donnees, creation=True, date=None):
    donnees = dict(donnees or {})
    if not donnees:
        raise ValueError("Aucune donnée de payeur")

    IDrelation = _entier_optionnel(donnees.get("IDrelation_structure"), "IDrelation_structure")
    if creation and not IDrelation:
        raise ValueError("IDrelation_structure obligatoire")

    type_payeur = _texte(donnees.get("type_payeur"))
    if creation and not type_payeur:
        raise ValueError("type_payeur obligatoire")
    if type_payeur and type_payeur not in TYPES_PAYEUR:
        raise ValueError("type_payeur inconnu: %s" % type_payeur)

    resultat = {}
    if creation or "IDrelation_structure" in donnees:
        resultat["IDrelation_structure"] = IDrelation
    if creation or "type_payeur" in donnees:
        resultat["type_payeur"] = type_payeur

    if creation or "IDfamille" in donnees:
        resultat["IDfamille"] = _entier_optionnel(donnees.get("IDfamille"), "IDfamille")
    if creation or "IDstructure_payeur" in donnees:
        resultat["IDstructure_payeur"] = _entier_optionnel(
            donnees.get("IDstructure_payeur"), "IDstructure_payeur"
        )
    for champ in CHAMPS_TEXTE_PAYEUR:
        if creation or champ in donnees:
            resultat[champ] = _texte(donnees.get(champ))

    if creation or "taux_prise_en_charge" in donnees:
        resultat["taux_prise_en_charge"] = _nombre_optionnel(
            donnees.get("taux_prise_en_charge"),
            "taux_prise_en_charge",
            minimum=0,
            maximum=100,
        )
    if creation or "montant_plafond" in donnees:
        resultat["montant_plafond"] = _nombre_optionnel(
            donnees.get("montant_plafond"), "montant_plafond", minimum=0
        )

    date_debut = None
    date_fin = None
    if creation or "date_debut" in donnees:
        date_debut = _date_iso(donnees.get("date_debut"), "date_debut")
        resultat["date_debut"] = date_debut
    if creation or "date_fin" in donnees:
        date_fin = _date_iso(donnees.get("date_fin"), "date_fin")
        resultat["date_fin"] = date_fin
    if creation:
        _verifier_periode(date_debut, date_fin)

    if creation or "actif" in donnees:
        resultat["actif"] = 1 if donnees.get("actif", 1) not in (0, False, "0") else 0
    resultat["date_modification"] = _date_maintenant(date)
    if creation:
        resultat["date_creation"] = _date_iso(
            donnees.get("date_creation") or date or datetime.date.today(),
            "date_creation",
            obligatoire=True,
        )

    if creation:
        _normaliser_cible_payeur(resultat)
    return resultat


def _normaliser_cible_payeur(donnees):
    type_payeur = donnees.get("type_payeur")
    if type_payeur == "famille":
        if not donnees.get("IDfamille"):
            raise ValueError("IDfamille obligatoire pour un payeur famille")
        donnees["IDstructure_payeur"] = None
    elif type_payeur in ("structure", "departement_ase"):
        if not donnees.get("IDstructure_payeur"):
            raise ValueError("IDstructure_payeur obligatoire pour ce type de payeur")
        donnees["IDfamille"] = None
    elif type_payeur == "autre":
        if not _texte(donnees.get("libelle_payeur")):
            raise ValueError("libelle_payeur obligatoire pour un payeur autre")
        donnees["IDfamille"] = None
        donnees["IDstructure_payeur"] = None
    return donnees


class GestionnaireRelationsStructures(object):
    def __init__(self, db):
        self.db = db

    def _existe(self, table, cle, ID):
        ID = int(ID)
        req = "SELECT %s FROM %s WHERE %s=%d;" % (cle, table, cle, ID)
        if self.db.ExecuterReq(req) != 1:
            return False
        return bool(self.db.ResultatReq())

    def _verifier_structure(self, IDstructure):
        if not self._existe("structures", "IDstructure", IDstructure):
            raise ValueError("Structure introuvable: %s" % IDstructure)

    def _verifier_groupe(self, IDgroupe_structure, IDstructure):
        if not IDgroupe_structure:
            return
        req = (
            "SELECT IDstructure FROM structures_groupes "
            "WHERE IDgroupe_structure=%d;" % int(IDgroupe_structure)
        )
        if self.db.ExecuterReq(req) != 1:
            raise ValueError("Impossible de vérifier le groupe")
        lignes = self.db.ResultatReq() or []
        if not lignes:
            raise ValueError("Groupe introuvable: %s" % IDgroupe_structure)
        if int(lignes[0][0]) != int(IDstructure):
            raise ValueError("Le groupe n'appartient pas à la structure bénéficiaire")

    def _verifier_activite(self, IDactivite):
        if not IDactivite:
            return
        if not self._existe("activites", "IDactivite", IDactivite):
            raise ValueError("Activité Noethys introuvable: %s" % IDactivite)

    def CreerRelation(self, donnees, date=None):
        valeurs = NormaliserRelation(donnees, creation=True, date=date)
        self._verifier_structure(valeurs["IDstructure"])
        self._verifier_groupe(valeurs.get("IDgroupe_structure"), valeurs["IDstructure"])
        self._verifier_activite(valeurs.get("IDactivite"))
        if self.LireRelationParUID(valeurs["uid"]):
            raise ValueError("UID de relation déjà utilisé")
        return self.db.ReqInsert("structures_relations", _liste_pairs(valeurs, CHAMPS_RELATION))

    def LireRelation(self, IDrelation_structure):
        if not IDrelation_structure:
            raise ValueError("IDrelation_structure obligatoire")
        req = "SELECT IDrelation_structure, %s FROM structures_relations WHERE IDrelation_structure=%d;" % (
            ", ".join(CHAMPS_RELATION), int(IDrelation_structure)
        )
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq() or []
        if not lignes:
            return None
        return dict(zip(("IDrelation_structure",) + CHAMPS_RELATION, lignes[0]))

    def LireRelationParUID(self, uid):
        uid = _uid_relation(uid)
        req = "SELECT IDrelation_structure, %s FROM structures_relations WHERE uid='%s';" % (
            ", ".join(CHAMPS_RELATION), uid
        )
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq() or []
        if not lignes:
            return None
        if len(lignes) > 1:
            raise RuntimeError("UID de relation dupliqué")
        return dict(zip(("IDrelation_structure",) + CHAMPS_RELATION, lignes[0]))

    def ModifierRelation(self, IDrelation_structure, donnees, date=None):
        courant = self.LireRelation(IDrelation_structure)
        if not courant:
            raise ValueError("Relation introuvable")
        fusion = dict(courant)
        fusion.update(dict(donnees or {}))
        normalise = NormaliserRelation(fusion, creation=True, date=date)
        normalise["uid"] = courant["uid"]
        normalise["date_creation"] = courant["date_creation"]
        self._verifier_structure(normalise["IDstructure"])
        self._verifier_groupe(normalise.get("IDgroupe_structure"), normalise["IDstructure"])
        self._verifier_activite(normalise.get("IDactivite"))
        _verifier_periode(normalise.get("date_debut"), normalise.get("date_fin"))
        valeurs = {
            champ: normalise.get(champ)
            for champ in CHAMPS_RELATION
            if champ not in ("uid", "date_creation")
        }
        return self.db.ReqMAJ(
            "structures_relations",
            _liste_pairs(valeurs, CHAMPS_RELATION),
            "IDrelation_structure",
            int(IDrelation_structure),
        )

    def ArchiverRelation(self, IDrelation_structure, date=None):
        return self.ModifierRelation(IDrelation_structure, {"actif": 0}, date=date)

    def ListerRelations(self, IDstructure=None, actifs_seulement=True):
        conditions = []
        if IDstructure:
            conditions.append("IDstructure=%d" % int(IDstructure))
        if actifs_seulement:
            conditions.append("actif=1")
        req = "SELECT IDrelation_structure, %s FROM structures_relations" % ", ".join(CHAMPS_RELATION)
        if conditions:
            req += " WHERE " + " AND ".join(conditions)
        req += " ORDER BY date_debut, libelle, IDrelation_structure;"
        if self.db.ExecuterReq(req) != 1:
            return []
        return [
            dict(zip(("IDrelation_structure",) + CHAMPS_RELATION, ligne))
            for ligne in (self.db.ResultatReq() or [])
        ]

    def CreerPayeur(self, donnees, date=None):
        valeurs = NormaliserPayeur(donnees, creation=True, date=date)
        if not self.LireRelation(valeurs["IDrelation_structure"]):
            raise ValueError("Relation introuvable")
        self._verifier_cible_payeur(valeurs)
        return self.db.ReqInsert("structures_payeurs", _liste_pairs(valeurs, CHAMPS_PAYEUR))

    def LirePayeur(self, IDpayeur_structure):
        if not IDpayeur_structure:
            raise ValueError("IDpayeur_structure obligatoire")
        req = "SELECT IDpayeur_structure, %s FROM structures_payeurs WHERE IDpayeur_structure=%d;" % (
            ", ".join(CHAMPS_PAYEUR), int(IDpayeur_structure)
        )
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq() or []
        if not lignes:
            return None
        return dict(zip(("IDpayeur_structure",) + CHAMPS_PAYEUR, lignes[0]))

    def ModifierPayeur(self, IDpayeur_structure, donnees, date=None):
        courant = self.LirePayeur(IDpayeur_structure)
        if not courant:
            raise ValueError("Payeur introuvable")
        fusion = dict(courant)
        fusion.update(dict(donnees or {}))
        normalise = NormaliserPayeur(fusion, creation=True, date=date)
        normalise["date_creation"] = courant["date_creation"]
        if not self.LireRelation(normalise["IDrelation_structure"]):
            raise ValueError("Relation introuvable")
        self._verifier_cible_payeur(normalise)
        _verifier_periode(normalise.get("date_debut"), normalise.get("date_fin"))
        valeurs = {
            champ: normalise.get(champ)
            for champ in CHAMPS_PAYEUR
            if champ != "date_creation"
        }
        return self.db.ReqMAJ(
            "structures_payeurs",
            _liste_pairs(valeurs, CHAMPS_PAYEUR),
            "IDpayeur_structure",
            int(IDpayeur_structure),
        )

    def ArchiverPayeur(self, IDpayeur_structure, date=None):
        return self.ModifierPayeur(IDpayeur_structure, {"actif": 0}, date=date)

    def ListerPayeurs(self, IDrelation_structure, actifs_seulement=True):
        if not IDrelation_structure:
            raise ValueError("IDrelation_structure obligatoire")
        condition = " AND actif=1" if actifs_seulement else ""
        req = "SELECT IDpayeur_structure, %s FROM structures_payeurs WHERE IDrelation_structure=%d%s ORDER BY IDpayeur_structure;" % (
            ", ".join(CHAMPS_PAYEUR), int(IDrelation_structure), condition
        )
        if self.db.ExecuterReq(req) != 1:
            return []
        return [
            dict(zip(("IDpayeur_structure",) + CHAMPS_PAYEUR, ligne))
            for ligne in (self.db.ResultatReq() or [])
        ]

    def ListerPayeursEffectifs(self, IDrelation_structure):
        """Retourne les payeurs explicites ou le bénéficiaire comme repli logique.

        Le repli n'écrit rien : il évite de dupliquer une prise en charge à 100 %
        quand bénéficiaire et payeur sont la même structure.
        """
        payeurs = self.ListerPayeurs(IDrelation_structure, actifs_seulement=True)
        if payeurs:
            resultat = []
            for payeur in payeurs:
                item = dict(payeur)
                item["implicite"] = False
                resultat.append(item)
            return resultat
        relation = self.LireRelation(IDrelation_structure)
        if not relation:
            raise ValueError("Relation introuvable")
        return [{
            "IDpayeur_structure": None,
            "IDrelation_structure": int(IDrelation_structure),
            "type_payeur": "structure",
            "IDfamille": None,
            "IDstructure_payeur": relation["IDstructure"],
            "libelle_payeur": "",
            "taux_prise_en_charge": 100.0,
            "montant_plafond": None,
            "date_debut": relation.get("date_debut"),
            "date_fin": relation.get("date_fin"),
            "reference": "",
            "actif": 1,
            "date_creation": None,
            "date_modification": None,
            "implicite": True,
        }]

    def _verifier_cible_payeur(self, payeur):
        type_payeur = payeur["type_payeur"]
        if type_payeur == "famille":
            IDfamille = payeur.get("IDfamille")
            if not self._existe("familles", "IDfamille", IDfamille):
                raise ValueError("Famille payeuse introuvable: %s" % IDfamille)
        elif type_payeur in ("structure", "departement_ase"):
            self._verifier_structure(payeur.get("IDstructure_payeur"))

