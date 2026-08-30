#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extension opérationnelle 1:1 des séances Noe-062C.

La séance canonique reste dans ``interventions``. Ce module ne duplique ni le
référentiel RH (Teamworks reste source de vérité), ni les lieux : il conserve
uniquement leurs UID/IDs de référence et les écarts entre prévu et réalisé.
"""
from __future__ import unicode_literals

import datetime

from Utils import UTILS_Interventions
from Utils import UTILS_Lieux


CHAMPS_EXECUTION = (
    "IDintervention",
    "UIDintervenant_habituel",
    "UIDintervenant_prevu",
    "UIDintervenant_reel",
    "IDlieu_prevu",
    "IDlieu_reel",
    "heure_debut_reelle",
    "heure_fin_reelle",
    "duree_reelle_minutes",
    "commentaire_realise",
    "date_modification",
)

CHAMPS_UID_RH = (
    "UIDintervenant_habituel",
    "UIDintervenant_prevu",
    "UIDintervenant_reel",
)

CHAMPS_LIEUX = ("IDlieu_prevu", "IDlieu_reel")


def _texte(valeur):
    if valeur is None:
        return u""
    try:
        return valeur.strip()
    except Exception:
        return valeur


def _uid_externe(valeur):
    valeur = _texte(valeur)
    if not valeur:
        return None
    if len(valeur) > 100:
        raise ValueError("UID intervenant trop long")
    if any(ord(ch) < 32 for ch in valeur):
        raise ValueError("UID intervenant invalide")
    return valeur


def _liste_pairs(donnees):
    return [(champ, donnees.get(champ)) for champ in CHAMPS_EXECUTION if champ in donnees]


class GestionnaireExecutionInterventions(object):
    def __init__(self, db):
        self.db = db
        self.interventions = UTILS_Interventions.GestionnaireInterventions(db)
        self.lieux = UTILS_Lieux.GestionnaireLieux(db)

    def _verifier_intervention(self, IDintervention):
        if not IDintervention:
            raise ValueError("IDintervention obligatoire")
        intervention = self.interventions.LireIntervention(int(IDintervention))
        if not intervention:
            raise ValueError("Séance canonique introuvable")
        return intervention

    def _verifier_lieu(self, IDlieu):
        if IDlieu in (None, "", 0, "0"):
            return None
        IDlieu = int(IDlieu)
        if not self.lieux.LireLieu(IDlieu):
            raise ValueError("Lieu introuvable: %s" % IDlieu)
        return IDlieu

    def LireExecution(self, IDintervention):
        self._verifier_intervention(IDintervention)
        req = "SELECT IDexecution_intervention, %s FROM interventions_execution WHERE IDintervention=%d ORDER BY IDexecution_intervention;" % (
            ", ".join(CHAMPS_EXECUTION), int(IDintervention))
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq()
        if not lignes:
            return None
        if len(lignes) > 1:
            raise RuntimeError("Plusieurs exécutions existent pour une même séance canonique")
        return dict(zip(("IDexecution_intervention",) + CHAMPS_EXECUTION, lignes[0]))

    def EnregistrerExecution(self, IDintervention, donnees, date=None):
        """Crée ou met à jour l'unique extension opérationnelle d'une séance."""
        self._verifier_intervention(IDintervention)
        donnees = dict(donnees or {})
        if not donnees:
            raise ValueError("Aucune donnée d'exécution à enregistrer")
        courant = self.LireExecution(IDintervention)
        valeurs = {"IDintervention": int(IDintervention)} if courant is None else {}

        for champ in CHAMPS_UID_RH:
            if champ in donnees:
                valeurs[champ] = _uid_externe(donnees.get(champ))

        for champ in CHAMPS_LIEUX:
            if champ in donnees:
                valeurs[champ] = self._verifier_lieu(donnees.get(champ))

        if "commentaire_realise" in donnees:
            valeurs["commentaire_realise"] = _texte(donnees.get("commentaire_realise"))

        change_debut = "heure_debut_reelle" in donnees
        change_fin = "heure_fin_reelle" in donnees
        if change_debut or change_fin:
            debut = donnees.get("heure_debut_reelle") if change_debut else (courant or {}).get("heure_debut_reelle")
            fin = donnees.get("heure_fin_reelle") if change_fin else (courant or {}).get("heure_fin_reelle")
            debut = _texte(debut)
            fin = _texte(fin)
            if not debut and not fin:
                valeurs["heure_debut_reelle"] = None
                valeurs["heure_fin_reelle"] = None
                valeurs["duree_reelle_minutes"] = None
            elif not debut or not fin:
                raise ValueError("Les horaires réels doivent être renseignés ou effacés ensemble")
            else:
                # Réutilise exactement le validateur horaire du contrat de séance.
                duree = UTILS_Interventions.CalculerDureeMinutes(debut, fin)
                valeurs["heure_debut_reelle"] = UTILS_Interventions._heure_hhmm(debut)
                valeurs["heure_fin_reelle"] = UTILS_Interventions._heure_hhmm(fin)
                valeurs["duree_reelle_minutes"] = duree

        valeurs["date_modification"] = (
            date.date().isoformat() if isinstance(date, datetime.datetime)
            else date.isoformat() if isinstance(date, datetime.date)
            else _texte(date) if date else datetime.date.today().isoformat()
        )

        if courant is None:
            return self.db.ReqInsert("interventions_execution", _liste_pairs(valeurs))
        self.db.ReqMAJ(
            "interventions_execution",
            _liste_pairs(valeurs),
            "IDexecution_intervention",
            int(courant["IDexecution_intervention"]),
        )
        return courant["IDexecution_intervention"]

    def LireSeanceComplete(self, IDintervention):
        """Retourne l'agrégat canonique : séance + exécution + lieux référencés."""
        intervention = self._verifier_intervention(IDintervention)
        execution = self.LireExecution(IDintervention)
        resultat = dict(intervention)
        resultat["execution"] = execution
        resultat["lieu_prevu"] = None
        resultat["lieu_reel"] = None
        if execution:
            if execution.get("IDlieu_prevu"):
                resultat["lieu_prevu"] = self.lieux.LireLieu(execution["IDlieu_prevu"])
            if execution.get("IDlieu_reel"):
                resultat["lieu_reel"] = self.lieux.LireLieu(execution["IDlieu_reel"])
        return resultat

    def ConstruireInterventionEchange(self, IDintervention):
        """Construit une ligne rétrocompatible avec ``noethys-session/1``.

        Les clés 062B historiques restent au premier niveau. Les données 062C
        sont ajoutées sans convertir le prévu en réalisé et sans exposer les ID
        locaux de lieux dans le contrat inter-applications.
        """
        complet = self.LireSeanceComplete(IDintervention)
        execution = complet.get("execution") or {}
        lieu_prevu = complet.get("lieu_prevu") or {}
        lieu_reel = complet.get("lieu_reel") or {}

        resultat = {
            champ: complet.get(champ)
            for champ in ("IDintervention",) + UTILS_Interventions.CHAMPS_INTERVENTION
        }
        resultat.update({
            "UIDintervenant_habituel": execution.get("UIDintervenant_habituel"),
            "UIDintervenant_prevu": execution.get("UIDintervenant_prevu"),
            "UIDintervenant_reel": execution.get("UIDintervenant_reel"),
            "UIDlieu_prevu": lieu_prevu.get("uid"),
            "UIDlieu_reel": lieu_reel.get("uid"),
            "heure_debut_reelle": execution.get("heure_debut_reelle"),
            "heure_fin_reelle": execution.get("heure_fin_reelle"),
            "duree_reelle_minutes": execution.get("duree_reelle_minutes"),
            "commentaire_realise": execution.get("commentaire_realise"),
            "execution_date_modification": execution.get("date_modification"),
        })
        return resultat
