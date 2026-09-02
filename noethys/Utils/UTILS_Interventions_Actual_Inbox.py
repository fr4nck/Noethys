#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Réception idempotente du réalisé validé dans le domaine activité/usagers.

Le contrat est indépendant des noms de produits. Un message met à jour la séance
canonique existante identifiée par ``session_uid`` et son extension 1:1 ; il ne
crée jamais de nouvelle séance ni de nouveau lieu.
"""
from __future__ import unicode_literals

import datetime
import hashlib
import json

from Data import DATA_Interventions_Actual_Inbox
from Utils import UTILS_Interventions
from Utils import UTILS_Interventions_Execution
from Utils import UTILS_Lieux


TABLE_INBOX = DATA_Interventions_Actual_Inbox.TABLE_INBOX
SOURCE_DOMAIN = "operations_portal"
CONTRACT_VERSION = "session-actual/1"
EVENT_TYPE = "session_actual_validated"
STATUTS_ACCEPTES = ("realisee", "annulee")


class ActualInboxError(ValueError):
    pass


def _texte(valeur):
    if valeur is None:
        return u""
    try:
        return valeur.strip()
    except Exception:
        return str(valeur).strip()


def _texte_requis(valeur, champ, longueur=255):
    valeur = _texte(valeur)
    if not valeur:
        raise ActualInboxError("%s obligatoire" % champ)
    if len(valeur) > longueur or any(ord(ch) < 32 for ch in valeur):
        raise ActualInboxError("%s invalide" % champ)
    return valeur


def _sql_texte(valeur):
    return _texte(valeur).replace("'", "''")


def _revision(valeur):
    try:
        valeur = int(valeur)
    except (TypeError, ValueError):
        raise ActualInboxError("actual_revision invalide")
    if valeur < 1:
        raise ActualInboxError("actual_revision invalide")
    return valeur


def _date_iso(valeur, champ="assignment_date"):
    if isinstance(valeur, datetime.datetime):
        valeur = valeur.date()
    if isinstance(valeur, datetime.date):
        return valeur.isoformat()
    valeur = _texte_requis(valeur, champ, 10)
    try:
        datetime.datetime.strptime(valeur, "%Y-%m-%d")
    except ValueError:
        raise ActualInboxError("%s invalide" % champ)
    return valeur


def _heure_optionnelle(valeur, champ):
    if valeur in (None, "", u""):
        return None
    valeur = _texte_requis(valeur, champ, 5)
    try:
        return datetime.datetime.strptime(valeur, "%H:%M").strftime("%H:%M")
    except ValueError:
        raise ActualInboxError("%s invalide" % champ)


def _datetime_reception(valeur=None):
    valeur = valeur or datetime.datetime.now()
    if isinstance(valeur, datetime.datetime):
        return valeur.strftime("%Y-%m-%d %H:%M:%S")
    texte = _texte_requis(valeur, "date_reception", 40).replace("T", " ")
    texte = texte[:19]
    try:
        datetime.datetime.strptime(texte, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ActualInboxError("date_reception invalide")
    return texte


def _json_stable(donnees):
    return json.dumps(donnees, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(donnees):
    return hashlib.sha256(_json_stable(donnees).encode("utf-8")).hexdigest()


def _rollback(db):
    methode = getattr(db, "Rollback", None)
    if callable(methode):
        methode()
        return
    connexion = getattr(db, "connexion", None) or getattr(db, "conn", None)
    if connexion is not None and hasattr(connexion, "rollback"):
        connexion.rollback()
        return
    raise RuntimeError("La connexion DB ne permet pas le rollback")


def _commit(db):
    methode = getattr(db, "Commit", None)
    if callable(methode):
        methode()
        return
    connexion = getattr(db, "connexion", None) or getattr(db, "conn", None)
    if connexion is not None and hasattr(connexion, "commit"):
        connexion.commit()
        return
    raise RuntimeError("La connexion DB ne permet pas le commit")


def _normaliser_message(payload):
    if not isinstance(payload, dict):
        raise ActualInboxError("payload invalide")
    contract_version = _texte_requis(payload.get("contract_version"), "contract_version", 64)
    if contract_version != CONTRACT_VERSION:
        raise ActualInboxError("version de contrat non supportée")
    event_type = _texte_requis(payload.get("event_type"), "event_type", 64)
    if event_type != EVENT_TYPE:
        raise ActualInboxError("type d'événement non supporté")
    actual_uuid = _texte_requis(payload.get("actual_uuid"), "actual_uuid", 64)
    session_uid = _texte_requis(payload.get("session_uid"), "session_uid", 128)
    revision = _revision(payload.get("actual_revision"))
    statut = _texte_requis(payload.get("session_status"), "session_status", 32)
    if statut not in STATUTS_ACCEPTES:
        raise ActualInboxError("session_status doit être realisee ou annulee")
    assignment_date = _date_iso(payload.get("assignment_date"))
    validated_at = _texte_requis(payload.get("validated_at"), "validated_at", 64)
    actual_staff_uid = _texte(payload.get("actual_staff_uid")) or None
    if actual_staff_uid is not None:
        if len(actual_staff_uid) > 100 or any(ord(ch) < 32 for ch in actual_staff_uid):
            raise ActualInboxError("actual_staff_uid invalide")
    actual_place_uid = _texte(payload.get("actual_place_uid")) or None
    if actual_place_uid is not None and len(actual_place_uid) > 128:
        raise ActualInboxError("actual_place_uid invalide")
    debut = _heure_optionnelle(payload.get("actual_start_time"), "actual_start_time")
    fin = _heure_optionnelle(payload.get("actual_end_time"), "actual_end_time")
    commentaire = _texte(payload.get("actual_comment"))
    if len(commentaire) > 2000:
        raise ActualInboxError("actual_comment trop long")

    duree = payload.get("actual_duration_minutes")
    if statut == "realisee":
        if not actual_staff_uid:
            raise ActualInboxError("intervenant réel obligatoire pour une séance réalisée")
        if debut is None or fin is None:
            raise ActualInboxError("horaires réels obligatoires pour une séance réalisée")
        calculee = UTILS_Interventions.CalculerDureeMinutes(debut, fin)
        try:
            duree = int(duree)
        except (TypeError, ValueError):
            raise ActualInboxError("actual_duration_minutes invalide")
        if duree != calculee:
            raise ActualInboxError("durée réelle incohérente avec les horaires")
    else:
        if actual_staff_uid is not None or actual_place_uid is not None or debut is not None or fin is not None or duree not in (None, "", u""):
            raise ActualInboxError("une séance annulée ne porte ni intervenant, ni lieu, ni horaires réels")
        if not commentaire:
            raise ActualInboxError("commentaire obligatoire pour une séance annulée")
        duree = None

    return {
        "contract_version": contract_version,
        "event_type": event_type,
        "actual_uuid": actual_uuid,
        "actual_revision": revision,
        "session_uid": session_uid,
        "session_status": statut,
        "assignment_date": assignment_date,
        "validated_at": validated_at,
        "actual_staff_uid": actual_staff_uid,
        "actual_place_uid": actual_place_uid,
        "actual_start_time": debut,
        "actual_end_time": fin,
        "actual_duration_minutes": duree,
        "actual_comment": commentaire,
    }


class GestionnaireInboxRealise(object):
    def __init__(self, db):
        self.db = db
        self.executions = UTILS_Interventions_Execution.GestionnaireExecutionInterventions(db)
        self.lieux = UTILS_Lieux.GestionnaireLieux(db)

    def _exiger_schema(self):
        requises = ("interventions", "interventions_execution", "lieux", TABLE_INBOX)
        absentes = [nom for nom in requises if not self.db.IsTableExists(nom)]
        if absentes:
            raise ActualInboxError("Tables requises absentes: %s" % ", ".join(absentes))

    def _lire_intervention_par_uid(self, uid):
        req = "SELECT IDintervention, uid, date, statut, actif FROM interventions WHERE uid='%s';" % _sql_texte(uid)
        if self.db.ExecuterReq(req) != 1:
            raise ActualInboxError("Impossible de lire la séance canonique")
        lignes = self.db.ResultatReq() or []
        if len(lignes) > 1:
            raise ActualInboxError("UID de séance canonique dupliqué")
        if not lignes:
            raise ActualInboxError("Séance canonique introuvable ; aucune création implicite")
        champs = ("IDintervention", "uid", "date", "statut", "actif")
        return dict(zip(champs, lignes[0]))

    def _lire_idempotence(self, cle):
        req = "SELECT idempotence_key, revision_key, source_domain, actual_uuid, session_uid, actual_revision, payload_sha256 FROM %s WHERE idempotence_key='%s';" % (
            TABLE_INBOX, _sql_texte(cle)
        )
        if self.db.ExecuterReq(req) != 1:
            raise ActualInboxError("Impossible de lire l'inbox")
        lignes = self.db.ResultatReq() or []
        if len(lignes) > 1:
            raise ActualInboxError("Clé d'idempotence dupliquée")
        if not lignes:
            return None
        champs = (
            "idempotence_key", "revision_key", "source_domain", "actual_uuid",
            "session_uid", "actual_revision", "payload_sha256",
        )
        return dict(zip(champs, lignes[0]))

    def _lire_derniere_revision(self, source_domain, session_uid):
        req = "SELECT idempotence_key, revision_key, source_domain, actual_uuid, session_uid, actual_revision, payload_sha256 FROM %s WHERE source_domain='%s' AND session_uid='%s' ORDER BY actual_revision DESC, IDinbox_execution DESC LIMIT 1;" % (
            TABLE_INBOX, _sql_texte(source_domain), _sql_texte(session_uid)
        )
        if self.db.ExecuterReq(req) != 1:
            raise ActualInboxError("Impossible de lire la dernière révision reçue")
        lignes = self.db.ResultatReq() or []
        if not lignes:
            return None
        champs = (
            "idempotence_key", "revision_key", "source_domain", "actual_uuid",
            "session_uid", "actual_revision", "payload_sha256",
        )
        return dict(zip(champs, lignes[0]))

    def AppliquerMessage(self, payload, idempotence_key, source_domain=SOURCE_DOMAIN, date_reception=None):
        """Applique une révision validée sur la séance existante, atomiquement."""
        self._exiger_schema()
        source_domain = _texte_requis(source_domain, "source_domain", 64)
        if source_domain != SOURCE_DOMAIN:
            raise ActualInboxError("domaine source non supporté")
        idempotence_key = _texte_requis(idempotence_key, "idempotence_key", 255)
        normalise = _normaliser_message(payload)
        empreinte = _sha256(normalise)
        revision_key = "%s:%s:r%d" % (
            source_domain, normalise["session_uid"], normalise["actual_revision"]
        )
        if len(revision_key) > 255:
            raise ActualInboxError("revision_key trop longue")
        date_reception_sql = _datetime_reception(date_reception)

        deja = self._lire_idempotence(idempotence_key)
        if deja is not None:
            if deja["payload_sha256"] != empreinte:
                raise ActualInboxError("clé d'idempotence rejouée avec un payload différent")
            return {
                "applique": False,
                "replay": True,
                "session_uid": normalise["session_uid"],
                "actual_revision": normalise["actual_revision"],
            }

        derniere = self._lire_derniere_revision(source_domain, normalise["session_uid"])
        if derniere is not None:
            derniere_revision = int(derniere["actual_revision"])
            if normalise["actual_revision"] < derniere_revision:
                raise ActualInboxError("révision reçue obsolète")
            if normalise["actual_revision"] == derniere_revision:
                if derniere["payload_sha256"] == empreinte and derniere["actual_uuid"] == normalise["actual_uuid"]:
                    return {
                        "applique": False,
                        "replay": True,
                        "session_uid": normalise["session_uid"],
                        "actual_revision": normalise["actual_revision"],
                    }
                raise ActualInboxError("conflit de payload pour la même révision")
            if derniere["actual_uuid"] != normalise["actual_uuid"]:
                raise ActualInboxError("identité du réalisé modifiée pour une même séance")

        intervention = self._lire_intervention_par_uid(normalise["session_uid"])
        if _date_iso(intervention["date"], "date de séance") != normalise["assignment_date"]:
            raise ActualInboxError("date reçue incohérente avec la séance canonique")
        if intervention["actif"] in (0, False, "0"):
            raise ActualInboxError("séance canonique archivée")

        IDlieu_reel = None
        if normalise["actual_place_uid"]:
            lieu = self.lieux.LireLieuParUID(normalise["actual_place_uid"])
            if not lieu:
                raise ActualInboxError("lieu réel canonique introuvable")
            IDlieu_reel = int(lieu["IDlieu"])

        valeurs_execution = {
            "UIDintervenant_reel": normalise["actual_staff_uid"],
            "IDlieu_reel": IDlieu_reel,
            "heure_debut_reelle": normalise["actual_start_time"],
            "heure_fin_reelle": normalise["actual_end_time"],
            "commentaire_realise": normalise["actual_comment"],
        }
        valeurs_inbox = (
            ("idempotence_key", idempotence_key),
            ("revision_key", revision_key),
            ("source_domain", source_domain),
            ("contract_version", normalise["contract_version"]),
            ("event_type", normalise["event_type"]),
            ("actual_uuid", normalise["actual_uuid"]),
            ("session_uid", normalise["session_uid"]),
            ("actual_revision", normalise["actual_revision"]),
            ("payload_sha256", empreinte),
            ("date_reception", date_reception_sql),
        )
        date_modification = date_reception_sql[:10]

        try:
            IDinbox = self.db.ReqInsert(TABLE_INBOX, list(valeurs_inbox), commit=False)
            if IDinbox is None:
                raise ActualInboxError("échec d'enregistrement de l'inbox")
            self.executions.EnregistrerExecution(
                intervention["IDintervention"],
                valeurs_execution,
                date=date_modification,
                commit=False,
            )
            resultat_maj = self.db.ReqMAJ(
                "interventions",
                [("statut", normalise["session_status"]), ("date_modification", date_modification)],
                "IDintervention",
                int(intervention["IDintervention"]),
                commit=False,
            )
            if resultat_maj is False:
                raise ActualInboxError("échec de mise à jour du statut de séance")
            _commit(self.db)
        except Exception:
            try:
                _rollback(self.db)
            except Exception:
                pass
            raise

        execution = self.executions.LireExecution(intervention["IDintervention"])
        if normalise["session_status"] == "realisee":
            if execution.get("duree_reelle_minutes") != normalise["actual_duration_minutes"]:
                raise RuntimeError("durée réelle persistée incohérente après commit")
        return {
            "applique": True,
            "replay": False,
            "IDintervention": int(intervention["IDintervention"]),
            "session_uid": normalise["session_uid"],
            "actual_revision": normalise["actual_revision"],
        }
