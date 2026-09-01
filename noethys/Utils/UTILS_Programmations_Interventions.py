#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Matérialisation sûre des programmations validées dans ``interventions``.

Ce service ne crée aucun second modèle de séance. Il calcule les occurrences
avec le moteur commun de récurrence, compare l'état désiré aux séances déjà
liées, puis crée uniquement les séances absentes. Les séances existantes ne
sont jamais réécrites automatiquement.
"""
from __future__ import unicode_literals

import datetime
import hashlib
import json

from Utils import UTILS_Locations_Recurrence
from Utils import UTILS_Programmations_Structures
from Utils import UTILS_Relations_Structures


TABLE_LIENS = "interventions_programmations"
STATUT_PLANIFIEE = "planifiee"
STATUT_REALISEE = "realisee"
STATUT_ANNULEE = "annulee"


def _texte(valeur):
    if valeur is None:
        return u""
    try:
        return valeur.strip()
    except Exception:
        return str(valeur)


def _sql_texte(valeur):
    return _texte(valeur).replace("'", "''")


def _date_iso(valeur):
    if isinstance(valeur, datetime.datetime):
        valeur = valeur.date()
    if isinstance(valeur, datetime.date):
        return valeur.isoformat()
    valeur = _texte(valeur)
    datetime.datetime.strptime(valeur, "%Y-%m-%d")
    return valeur


def _heure_hhmm(valeur):
    if isinstance(valeur, datetime.datetime):
        valeur = valeur.time()
    if isinstance(valeur, datetime.time):
        return valeur.strftime("%H:%M")
    valeur = _texte(valeur)
    return datetime.datetime.strptime(valeur, "%H:%M").strftime("%H:%M")


def _duree_minutes(debut, fin):
    h1 = datetime.datetime.strptime(_heure_hhmm(debut), "%H:%M")
    h2 = datetime.datetime.strptime(_heure_hhmm(fin), "%H:%M")
    minutes = int((h2 - h1).total_seconds() // 60)
    if minutes <= 0:
        raise ValueError("La fin d'une séance doit être postérieure au début")
    return minutes


def _json_stable(donnees):
    return json.dumps(donnees, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(donnees):
    return hashlib.sha256(_json_stable(donnees).encode("utf-8")).hexdigest()


def _cle_occurrence(uid_programme, uid_creneau, date, debut, fin):
    brut = {
        "programme": uid_programme,
        "creneau": uid_creneau,
        "date": date,
        "debut": debut,
        "fin": fin,
    }
    return "OCC-%s" % _sha256(brut)[:40]


def _uid_intervention(cle_occurrence):
    return "INT-PROG-%s" % hashlib.sha256(cle_occurrence.encode("utf-8")).hexdigest()[:32]


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


def _pairs(donnees, champs):
    return [(champ, donnees.get(champ)) for champ in champs]


CHAMPS_INTERVENTION_GENERES = (
    "uid",
    "IDstructure",
    "IDgroupe_structure",
    "IDrelation_structure",
    "nature",
    "date",
    "heure_debut",
    "heure_fin",
    "duree_minutes",
    "libelle",
    "statut",
    "notes",
    "actif",
    "date_creation",
    "date_modification",
)

CHAMPS_LIEN = (
    "IDintervention",
    "IDprogrammation_structure",
    "IDcreneau_programmation",
    "type_source",
    "IDrelation_structure",
    "IDactivite",
    "IDgroupe_activite",
    "cle_occurrence",
    "empreinte_generation",
    "date_generation",
)


class GestionnaireMaterialisationProgrammations(object):
    def __init__(self, db):
        self.db = db
        self.programmations = UTILS_Programmations_Structures.GestionnaireProgrammationsStructures(db)
        self.relations = UTILS_Relations_Structures.GestionnaireRelationsStructures(db)

    def _exiger_tables(self):
        requises = (
            "interventions",
            "interventions_execution",
            "structures_programmations",
            "structures_programmations_creneaux",
            TABLE_LIENS,
        )
        absentes = [nom for nom in requises if not self.db.IsTableExists(nom)]
        if absentes:
            raise ValueError("Tables requises absentes: %s" % ", ".join(absentes))

    def _lire_intervention_par_uid(self, uid):
        req = "SELECT IDintervention, uid, IDstructure, IDgroupe_structure, IDrelation_structure, nature, date, heure_debut, heure_fin, duree_minutes, libelle, statut, notes, actif FROM interventions WHERE uid='%s';" % _sql_texte(uid)
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq() or []
        if len(lignes) > 1:
            raise RuntimeError("UID d'intervention dupliqué: %s" % uid)
        if not lignes:
            return None
        champs = (
            "IDintervention", "uid", "IDstructure", "IDgroupe_structure",
            "IDrelation_structure", "nature", "date", "heure_debut",
            "heure_fin", "duree_minutes", "libelle", "statut", "notes", "actif",
        )
        return dict(zip(champs, lignes[0]))

    def _lire_intervention(self, IDintervention):
        req = "SELECT IDintervention, uid, IDstructure, IDgroupe_structure, IDrelation_structure, nature, date, heure_debut, heure_fin, duree_minutes, libelle, statut, notes, actif FROM interventions WHERE IDintervention=%d;" % int(IDintervention)
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq() or []
        if not lignes:
            return None
        champs = (
            "IDintervention", "uid", "IDstructure", "IDgroupe_structure",
            "IDrelation_structure", "nature", "date", "heure_debut",
            "heure_fin", "duree_minutes", "libelle", "statut", "notes", "actif",
        )
        return dict(zip(champs, lignes[0]))

    def _lire_lien_par_cle(self, cle):
        req = "SELECT IDintervention_programmation, %s FROM %s WHERE cle_occurrence='%s';" % (
            ", ".join(CHAMPS_LIEN), TABLE_LIENS, _sql_texte(cle)
        )
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq() or []
        if len(lignes) > 1:
            raise RuntimeError("Clé d'occurrence dupliquée")
        if not lignes:
            return None
        return dict(zip(("IDintervention_programmation",) + CHAMPS_LIEN, lignes[0]))

    def _lire_execution(self, IDintervention):
        req = "SELECT IDexecution_intervention, UIDintervenant_habituel, UIDintervenant_prevu, UIDintervenant_reel, IDlieu_prevu, IDlieu_reel, heure_debut_reelle, heure_fin_reelle, duree_reelle_minutes FROM interventions_execution WHERE IDintervention=%d;" % int(IDintervention)
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq() or []
        if len(lignes) > 1:
            raise RuntimeError("Plusieurs exécutions pour une séance")
        if not lignes:
            return None
        champs = (
            "IDexecution_intervention", "UIDintervenant_habituel", "UIDintervenant_prevu",
            "UIDintervenant_reel", "IDlieu_prevu", "IDlieu_reel",
            "heure_debut_reelle", "heure_fin_reelle", "duree_reelle_minutes",
        )
        return dict(zip(champs, lignes[0]))

    def _contexte_source(self, programmation):
        if programmation["type_source"] == "relation":
            relation = self.relations.LireRelation(programmation["IDrelation_structure"])
            if not relation:
                raise ValueError("Relation source introuvable")
            return {
                "IDstructure": relation.get("IDstructure"),
                "IDgroupe_structure": relation.get("IDgroupe_structure"),
                "IDrelation_structure": programmation["IDrelation_structure"],
                "IDactivite": None,
                "IDgroupe_activite": None,
            }
        if programmation["type_source"] == "activite":
            return {
                "IDstructure": None,
                "IDgroupe_structure": None,
                "IDrelation_structure": None,
                "IDactivite": programmation.get("IDactivite"),
                "IDgroupe_activite": programmation.get("IDgroupe_activite"),
            }
        raise ValueError("Type de source de programmation inconnu")

    def _occurrences_desirees(self, programmation, calendrier=None):
        contexte = self._contexte_source(programmation)
        resultat = []
        for creneau in self.programmations.ListerCreneaux(
            programmation["IDprogrammation_structure"], conserves_seulement=True
        ):
            regle = self.programmations.ConstruireRegleRecurrence(
                creneau["IDcreneau_programmation"], exiger_validee=True
            )
            occurrences = UTILS_Locations_Recurrence.CalculerOccurrences(
                regle, calendrier=calendrier
            )
            for occurrence in occurrences:
                debut_dt = occurrence["date_debut"]
                fin_dt = occurrence["date_fin"]
                date = debut_dt.date().isoformat()
                debut = debut_dt.strftime("%H:%M")
                fin = fin_dt.strftime("%H:%M")
                cle = _cle_occurrence(programmation["uid"], creneau["uid"], date, debut, fin)
                lieu = creneau.get("IDlieu") or programmation.get("IDlieu_habituel")
                desire = {
                    "uid": _uid_intervention(cle),
                    "IDstructure": contexte["IDstructure"],
                    "IDgroupe_structure": contexte["IDgroupe_structure"],
                    "IDrelation_structure": contexte["IDrelation_structure"],
                    "nature": "autre",
                    "date": date,
                    "heure_debut": debut,
                    "heure_fin": fin,
                    "duree_minutes": _duree_minutes(debut, fin),
                    "libelle": _texte(programmation.get("libelle")) or u"Séance programmée",
                    "statut": STATUT_PLANIFIEE,
                    "notes": u"",
                    "actif": 1,
                    "IDprogrammation_structure": programmation["IDprogrammation_structure"],
                    "IDcreneau_programmation": creneau["IDcreneau_programmation"],
                    "type_source": programmation["type_source"],
                    "IDactivite": contexte["IDactivite"],
                    "IDgroupe_activite": contexte["IDgroupe_activite"],
                    "cle_occurrence": cle,
                    "UIDintervenant_habituel": programmation.get("UIDintervenant_habituel"),
                    "UIDintervenant_prevu": programmation.get("UIDintervenant_habituel"),
                    "IDlieu_prevu": lieu,
                }
                empreinte = dict(
                    (cle_champ, desire.get(cle_champ))
                    for cle_champ in (
                        "uid", "IDstructure", "IDgroupe_structure", "IDrelation_structure",
                        "nature", "date", "heure_debut", "heure_fin", "duree_minutes",
                        "libelle", "type_source", "IDactivite", "IDgroupe_activite",
                        "UIDintervenant_prevu", "IDlieu_prevu",
                    )
                )
                desire["empreinte_generation"] = _sha256(empreinte)
                resultat.append(desire)
        resultat.sort(key=lambda item: (item["date"], item["heure_debut"], item["uid"]))
        return resultat

    @staticmethod
    def _ecarts(intervention, execution, desire):
        ecarts = []
        for champ in (
            "uid", "IDstructure", "IDgroupe_structure", "IDrelation_structure",
            "nature", "date", "heure_debut", "heure_fin", "duree_minutes",
            "libelle", "actif",
        ):
            if intervention.get(champ) != desire.get(champ):
                ecarts.append(champ)
        execution = execution or {}
        if execution.get("UIDintervenant_prevu") != desire.get("UIDintervenant_prevu"):
            ecarts.append("UIDintervenant_prevu")
        if execution.get("IDlieu_prevu") != desire.get("IDlieu_prevu"):
            ecarts.append("IDlieu_prevu")
        return tuple(ecarts)

    def Previsualiser(self, IDprogrammation_structure, calendrier=None):
        self._exiger_tables()
        programmation = self.programmations.LireProgrammation(IDprogrammation_structure)
        if not programmation or not programmation.get("actif"):
            raise ValueError("Programmation active introuvable")
        if programmation["statut"] != UTILS_Programmations_Structures.STATUT_VALIDEE:
            raise ValueError("Seule une programmation validée peut être matérialisée")

        desires = self._occurrences_desirees(programmation, calendrier=calendrier)
        attendues = set(item["cle_occurrence"] for item in desires)
        lignes = []
        for desire in desires:
            lien = self._lire_lien_par_cle(desire["cle_occurrence"])
            if lien:
                if int(lien["IDprogrammation_structure"]) != int(IDprogrammation_structure):
                    lignes.append({"etat": "conflit", "raison": "cle_liee_autre_programmation", "desire": desire, "lien": lien})
                    continue
                intervention = self._lire_intervention(lien["IDintervention"])
                if not intervention:
                    lignes.append({"etat": "conflit", "raison": "intervention_liee_absente", "desire": desire, "lien": lien})
                    continue
                execution = self._lire_execution(intervention["IDintervention"])
                ecarts = self._ecarts(intervention, execution, desire)
                if intervention.get("statut") in (STATUT_REALISEE, STATUT_ANNULEE):
                    lignes.append({"etat": "protegee", "raison": "seance_%s" % intervention["statut"], "ecarts": ecarts, "desire": desire, "intervention": intervention, "lien": lien})
                elif ecarts:
                    lignes.append({"etat": "conflit", "raison": "seance_planifiee_divergente", "ecarts": ecarts, "desire": desire, "intervention": intervention, "lien": lien})
                else:
                    lignes.append({"etat": "existante", "raison": "idempotente", "desire": desire, "intervention": intervention, "lien": lien})
                continue

            collision = self._lire_intervention_par_uid(desire["uid"])
            if collision:
                lignes.append({"etat": "conflit", "raison": "uid_intervention_non_trace", "desire": desire, "intervention": collision})
            else:
                lignes.append({"etat": "a_creer", "raison": "absente", "desire": desire})

        req = "SELECT IDintervention_programmation, %s FROM %s WHERE IDprogrammation_structure=%d;" % (
            ", ".join(CHAMPS_LIEN), TABLE_LIENS, int(IDprogrammation_structure)
        )
        if self.db.ExecuterReq(req) == 1:
            for row in self.db.ResultatReq() or []:
                lien = dict(zip(("IDintervention_programmation",) + CHAMPS_LIEN, row))
                if lien["cle_occurrence"] not in attendues:
                    intervention = self._lire_intervention(lien["IDintervention"])
                    lignes.append({
                        "etat": "obsolete",
                        "raison": "occurrence_plus_desiree",
                        "lien": lien,
                        "intervention": intervention,
                    })

        compteurs = {}
        for ligne in lignes:
            compteurs[ligne["etat"]] = compteurs.get(ligne["etat"], 0) + 1
        return {
            "IDprogrammation_structure": int(IDprogrammation_structure),
            "programmation_uid": programmation["uid"],
            "lignes": lignes,
            "compteurs": compteurs,
            "applicable": compteurs.get("conflit", 0) == 0,
        }

    def _creer_execution_prevue(self, IDintervention, desire, date_generation):
        if not desire.get("UIDintervenant_prevu") and not desire.get("IDlieu_prevu"):
            return None
        valeurs = [
            ("IDintervention", int(IDintervention)),
            ("UIDintervenant_habituel", desire.get("UIDintervenant_habituel")),
            ("UIDintervenant_prevu", desire.get("UIDintervenant_prevu")),
            ("UIDintervenant_reel", None),
            ("IDlieu_prevu", desire.get("IDlieu_prevu")),
            ("IDlieu_reel", None),
            ("heure_debut_reelle", None),
            ("heure_fin_reelle", None),
            ("duree_reelle_minutes", None),
            ("commentaire_realise", None),
            ("date_modification", date_generation),
        ]
        return self.db.ReqInsert("interventions_execution", valeurs, commit=False)

    def Appliquer(self, IDprogrammation_structure, calendrier=None, date=None):
        preview = self.Previsualiser(IDprogrammation_structure, calendrier=calendrier)
        if not preview["applicable"]:
            raise ValueError("La matérialisation contient des conflits ; aucune écriture effectuée")
        date_generation = _date_iso(date or datetime.date.today())
        crees = []
        try:
            for ligne in preview["lignes"]:
                if ligne["etat"] != "a_creer":
                    continue
                desire = ligne["desire"]
                valeurs_intervention = {
                    champ: desire.get(champ) for champ in CHAMPS_INTERVENTION_GENERES
                }
                valeurs_intervention["date_creation"] = date_generation
                valeurs_intervention["date_modification"] = date_generation
                IDintervention = self.db.ReqInsert(
                    "interventions",
                    _pairs(valeurs_intervention, CHAMPS_INTERVENTION_GENERES),
                    commit=False,
                )
                self._creer_execution_prevue(IDintervention, desire, date_generation)
                valeurs_lien = {
                    "IDintervention": IDintervention,
                    "IDprogrammation_structure": desire["IDprogrammation_structure"],
                    "IDcreneau_programmation": desire["IDcreneau_programmation"],
                    "type_source": desire["type_source"],
                    "IDrelation_structure": desire["IDrelation_structure"],
                    "IDactivite": desire["IDactivite"],
                    "IDgroupe_activite": desire["IDgroupe_activite"],
                    "cle_occurrence": desire["cle_occurrence"],
                    "empreinte_generation": desire["empreinte_generation"],
                    "date_generation": date_generation,
                }
                self.db.ReqInsert(TABLE_LIENS, _pairs(valeurs_lien, CHAMPS_LIEN), commit=False)
                crees.append(IDintervention)
            _commit(self.db)
        except Exception:
            _rollback(self.db)
            raise
        return {
            "ok": True,
            "crees": tuple(crees),
            "nb_crees": len(crees),
            "preview": preview,
        }
