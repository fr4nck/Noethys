#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Interventions métier liées aux structures, premier vertical Noe-062B.

Le premier cas activé est volontairement simple : enregistrer une séance de
sport pour une école. Les conventions, groupes/classes et payeurs restent des
liens optionnels ; ils ne bloquent pas la saisie quotidienne.
"""

from __future__ import unicode_literals

import datetime
import uuid

from Utils import UTILS_Tiers


CHAMPS_INTERVENTION = (
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

STATUTS_SEANCE = ("planifiee", "realisee", "annulee")


def _texte(valeur):
    if valeur is None:
        return u""
    try:
        return valeur.strip()
    except Exception:
        return valeur


def _date_iso(valeur=None):
    # ``None`` signifie « valeur interne omise » et conserve le repli historique
    # sur aujourd'hui. En revanche une chaîne vide issue d'un formulaire est une
    # donnée invalide : ne jamais transformer silencieusement une date effacée en
    # date du jour.
    if valeur is None:
        valeur = datetime.date.today()
    if isinstance(valeur, datetime.datetime):
        valeur = valeur.date()
    if isinstance(valeur, datetime.date):
        return valeur.isoformat()
    texte = _texte(valeur)
    if not texte:
        raise ValueError("La date de la séance est obligatoire")
    for format_date in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.datetime.strptime(texte, format_date).date().isoformat()
        except (TypeError, ValueError):
            pass
    raise ValueError("Date invalide : utilisez JJ/MM/AAAA ou AAAA-MM-JJ")


def _heure_hhmm(valeur):
    texte = _texte(valeur)
    try:
        heure = datetime.datetime.strptime(texte, "%H:%M")
    except (TypeError, ValueError):
        raise ValueError("Heure invalide : utilisez HH:MM")
    return heure.strftime("%H:%M")


def CalculerDureeMinutes(heure_debut, heure_fin):
    debut = datetime.datetime.strptime(_heure_hhmm(heure_debut), "%H:%M")
    fin = datetime.datetime.strptime(_heure_hhmm(heure_fin), "%H:%M")
    minutes = int((fin - debut).total_seconds() // 60)
    if minutes <= 0:
        raise ValueError("L'heure de fin doit être postérieure à l'heure de début")
    return minutes


def GenererUIDIntervention():
    return "INT-%s" % uuid.uuid4().hex


def UIDStructureEcoleHistorique(IDecole):
    return "ECOLE-NOETHYS-%d" % int(IDecole)


def CompterInterventionsEcoleHistorique(db, IDecole):
    """Retourne le nombre d'interventions liées à une école historique.

    La fonction est compatible avec une base antérieure à Noe-062B : si les
    tables additives n'existent pas encore, elle renvoie simplement zéro.
    """
    if not db.IsTableExists("structures") or not db.IsTableExists("interventions"):
        return 0
    uid = UIDStructureEcoleHistorique(IDecole).replace("'", "''")
    req = """SELECT COUNT(i.IDintervention)
    FROM interventions i
    INNER JOIN structures s ON s.IDstructure=i.IDstructure
    WHERE s.uid='%s';""" % uid
    if db.ExecuterReq(req) != 1:
        raise RuntimeError("Impossible de vérifier les séances rattachées à cette école")
    lignes = db.ResultatReq()
    if not lignes:
        return 0
    return int(lignes[0][0] or 0)


def _liste_pairs(donnees):
    return [(champ, donnees[champ]) for champ in CHAMPS_INTERVENTION if champ in donnees]


class GestionnaireInterventions(object):
    def __init__(self, db):
        self.db = db
        self.tiers = UTILS_Tiers.GestionnaireTiers(db)

    def _verifier_ecole(self, IDstructure):
        structure = self.tiers.LireStructure(int(IDstructure))
        if not structure:
            raise ValueError("École introuvable dans le référentiel des structures")
        if structure.get("type_structure") != "ecole":
            raise ValueError("La structure sélectionnée n'est pas une école")
        if structure.get("actif") in (0, False, "0"):
            raise ValueError("Cette école est archivée")
        return structure

    def SynchroniserEcoleHistorique(self, IDecole):
        """Crée/met à jour le tiers école depuis la table historique ``ecoles``.

        Le lien est stable grâce à l'UID ``ECOLE-NOETHYS-<IDecole>``. La table
        historique reste la source de vérité de la fiche école tant que sa
        migration complète n'est pas décidée.
        """
        IDecole = int(IDecole)
        req = """SELECT IDecole, nom, rue, cp, ville, tel, mail
        FROM ecoles WHERE IDecole=%d;""" % IDecole
        if self.db.ExecuterReq(req) != 1:
            raise ValueError("Impossible de lire l'école historique")
        lignes = self.db.ResultatReq()
        if not lignes:
            raise ValueError("École historique introuvable")

        IDecole, nom, rue, cp, ville, tel, mail = lignes[0]
        uid = UIDStructureEcoleHistorique(IDecole)
        donnees = {
            "type_structure": "ecole",
            "nom": _texte(nom),
            "rue": _texte(rue),
            "cp": _texte(cp),
            "ville": _texte(ville),
            "tel": _texte(tel),
            "mail": _texte(mail),
            "actif": 1,
        }

        structure_existante = None
        for structure in self.tiers.ListerStructures(actifs_seulement=False):
            if structure.get("uid") == uid:
                structure_existante = structure
                break

        if structure_existante is None:
            donnees["uid"] = uid
            IDstructure = self.tiers.CreerStructure(donnees)
            if IDstructure is None:
                raise RuntimeError("La création du tiers école a échoué")
            return self.tiers.LireStructure(IDstructure)

        IDstructure = structure_existante["IDstructure"]
        if self.tiers.ModifierStructure(IDstructure, donnees) is False:
            raise RuntimeError("La synchronisation du tiers école a échoué")
        return self.tiers.LireStructure(IDstructure)

    def CreerSeanceSportEcole(self, IDstructure, date, heure_debut, heure_fin,
                              libelle=u"Séance de sport", statut="realisee",
                              notes=u"", IDgroupe_structure=None,
                              IDrelation_structure=None):
        self._verifier_ecole(IDstructure)
        statut = _texte(statut) or "realisee"
        if statut not in STATUTS_SEANCE:
            raise ValueError("Statut de séance inconnu : %s" % statut)
        debut = _heure_hhmm(heure_debut)
        fin = _heure_hhmm(heure_fin)
        aujourd_hui = datetime.date.today().isoformat()
        valeurs = {
            "uid": GenererUIDIntervention(),
            "IDstructure": int(IDstructure),
            "IDgroupe_structure": IDgroupe_structure,
            "IDrelation_structure": IDrelation_structure,
            "nature": "sport",
            "date": _date_iso(date),
            "heure_debut": debut,
            "heure_fin": fin,
            "duree_minutes": CalculerDureeMinutes(debut, fin),
            "libelle": _texte(libelle) or u"Séance de sport",
            "statut": statut,
            "notes": _texte(notes),
            "actif": 1,
            "date_creation": aujourd_hui,
            "date_modification": aujourd_hui,
        }
        IDintervention = self.db.ReqInsert("interventions", _liste_pairs(valeurs))
        if IDintervention is None:
            raise RuntimeError("L'enregistrement de la séance a échoué")
        return IDintervention

    def LireIntervention(self, IDintervention):
        req = "SELECT IDintervention, %s FROM interventions WHERE IDintervention=%d;" % (
            ", ".join(CHAMPS_INTERVENTION), int(IDintervention))
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq()
        if not lignes:
            return None
        return dict(zip(("IDintervention",) + CHAMPS_INTERVENTION, lignes[0]))

    def ModifierSeanceSport(self, IDintervention, donnees):
        courant = self.LireIntervention(IDintervention)
        if not courant or courant.get("nature") != "sport":
            raise ValueError("Séance de sport introuvable")
        donnees = dict(donnees or {})
        if not donnees:
            raise ValueError("Aucune donnée à modifier")

        valeurs = {}
        if "IDstructure" in donnees:
            self._verifier_ecole(donnees["IDstructure"])
            valeurs["IDstructure"] = int(donnees["IDstructure"])
        if "IDgroupe_structure" in donnees:
            valeurs["IDgroupe_structure"] = donnees["IDgroupe_structure"]
        if "IDrelation_structure" in donnees:
            valeurs["IDrelation_structure"] = donnees["IDrelation_structure"]
        if "date" in donnees:
            valeurs["date"] = _date_iso(donnees["date"])
        if "libelle" in donnees:
            valeurs["libelle"] = _texte(donnees["libelle"]) or u"Séance de sport"
        if "notes" in donnees:
            valeurs["notes"] = _texte(donnees["notes"])
        if "statut" in donnees:
            statut = _texte(donnees["statut"])
            if statut not in STATUTS_SEANCE:
                raise ValueError("Statut de séance inconnu : %s" % statut)
            valeurs["statut"] = statut
        if "actif" in donnees:
            valeurs["actif"] = 1 if donnees["actif"] not in (0, False, "0") else 0

        if "heure_debut" in donnees or "heure_fin" in donnees:
            debut = _heure_hhmm(donnees.get("heure_debut", courant["heure_debut"]))
            fin = _heure_hhmm(donnees.get("heure_fin", courant["heure_fin"]))
            if "heure_debut" in donnees:
                valeurs["heure_debut"] = debut
            if "heure_fin" in donnees:
                valeurs["heure_fin"] = fin
            valeurs["duree_minutes"] = CalculerDureeMinutes(debut, fin)

        valeurs["date_modification"] = datetime.date.today().isoformat()
        resultat = self.db.ReqMAJ(
            "interventions",
            _liste_pairs(valeurs),
            "IDintervention",
            int(IDintervention),
        )
        if resultat is False:
            raise RuntimeError("La modification de la séance a échoué")
        return resultat

    def ArchiverSeanceSport(self, IDintervention):
        return self.ModifierSeanceSport(IDintervention, {"actif": 0})

    def ListerSeancesSportEcole(self, IDstructure=None, date_debut=None,
                                date_fin=None, actifs_seulement=True):
        conditions = ["i.nature='sport'"]
        if IDstructure is not None:
            conditions.append("i.IDstructure=%d" % int(IDstructure))
        if date_debut is not None:
            conditions.append("i.date>='%s'" % _date_iso(date_debut))
        if date_fin is not None:
            conditions.append("i.date<='%s'" % _date_iso(date_fin))
        if actifs_seulement:
            conditions.append("i.actif=1")

        req = """SELECT i.IDintervention, %s, s.nom
        FROM interventions i
        LEFT JOIN structures s ON s.IDstructure=i.IDstructure
        WHERE %s
        ORDER BY i.date DESC, i.heure_debut DESC, i.IDintervention DESC;""" % (
            ", ".join("i.%s" % champ for champ in CHAMPS_INTERVENTION),
            " AND ".join(conditions),
        )
        if self.db.ExecuterReq(req) != 1:
            return []
        champs = ("IDintervention",) + CHAMPS_INTERVENTION + ("nom_ecole",)
        return [dict(zip(champs, ligne)) for ligne in self.db.ResultatReq()]