#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Service métier des programmations annuelles et créneaux Noe-062E.

La programmation décrit la règle prévisionnelle. Les séances datées restent
les ``interventions`` canoniques de Noethys et seront matérialisées dans un lot
séparé depuis les règles exposées par ``ConstruireRegleRecurrence``.

Le même stockage accepte une relation contractuelle externe ou une activité
interne Noethys. Il ne duplique ni le moteur calendrier, ni le moteur de
facturation, ni le stockage des séances réalisées.
"""
from __future__ import unicode_literals

import datetime
import uuid

from Utils import UTILS_Relations_Structures


TYPE_SOURCE_RELATION = "relation"
TYPE_SOURCE_ACTIVITE = "activite"
TYPES_SOURCE = (TYPE_SOURCE_RELATION, TYPE_SOURCE_ACTIVITE)

STATUT_BROUILLON = "brouillon"
STATUT_SOUMISE = "soumise"
STATUT_VALIDEE = "validee"
STATUT_ANNULEE = "annulee"
STATUTS = (STATUT_BROUILLON, STATUT_SOUMISE, STATUT_VALIDEE, STATUT_ANNULEE)

RENOUVELLEMENT_AJOUTE = "ajoute"
RENOUVELLEMENT_INCHANGE = "inchange"
RENOUVELLEMENT_MODIFIE = "modifie"
RENOUVELLEMENT_SUPPRIME = "supprime"
ETATS_RENOUVELLEMENT = (
    RENOUVELLEMENT_AJOUTE,
    RENOUVELLEMENT_INCHANGE,
    RENOUVELLEMENT_MODIFIE,
    RENOUVELLEMENT_SUPPRIME,
)

FREQUENCES = (1, 2, 3, 4, 5, 6)

CHAMPS_PROGRAMMATION = (
    "uid",
    "type_source",
    "IDrelation_structure",
    "IDactivite",
    "IDgroupe_activite",
    "IDprogrammation_parent",
    "saison",
    "libelle",
    "statut",
    "date_debut",
    "date_fin",
    "UIDintervenant_habituel",
    "IDlieu_habituel",
    "actif",
    "memo",
    "date_creation",
    "date_modification",
)

CHAMPS_CRENEAU = (
    "uid",
    "IDprogrammation_structure",
    "IDcreneau_source",
    "jour_semaine",
    "heure_debut",
    "heure_fin",
    "date_debut",
    "date_fin",
    "appliquer_scolaire",
    "appliquer_vacances",
    "inclure_feries",
    "frequence",
    "IDlieu",
    "groupe",
    "observations",
    "etat_renouvellement",
    "actif",
    "date_creation",
    "date_modification",
)


def _texte(valeur):
    if valeur is None:
        return u""
    try:
        return valeur.strip()
    except Exception:
        return valeur


def _sql_texte(valeur):
    return _texte(valeur).replace("'", "''")


def _uid(prefixe, valeur=None, generer=True):
    valeur = _texte(valeur)
    if not valeur:
        if not generer:
            raise ValueError("UID obligatoire")
        valeur = "%s-%s" % (prefixe, uuid.uuid4().hex)
    if len(valeur) > 64 or not all(ch.isalnum() or ch in "-_" for ch in valeur):
        raise ValueError("UID invalide")
    return valeur


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


def _date_obj(valeur, nom_champ, obligatoire=False):
    if valeur in (None, ""):
        if obligatoire:
            raise ValueError("%s est obligatoire" % nom_champ)
        return None
    if isinstance(valeur, datetime.datetime):
        return valeur.date()
    if isinstance(valeur, datetime.date):
        return valeur
    valeur = _texte(valeur)
    try:
        return datetime.datetime.strptime(valeur, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError("%s doit être une date ISO YYYY-MM-DD" % nom_champ)


def _date_iso(valeur, nom_champ, obligatoire=False):
    date = _date_obj(valeur, nom_champ, obligatoire=obligatoire)
    return date.isoformat() if date else None


def _heure(valeur, nom_champ):
    valeur = _texte(valeur)
    try:
        return datetime.datetime.strptime(valeur, "%H:%M").strftime("%H:%M")
    except (TypeError, ValueError):
        raise ValueError("%s doit être une heure HH:MM" % nom_champ)


def _booleen(valeur, defaut=False):
    if valeur in (None, ""):
        return 1 if defaut else 0
    return 0 if valeur in (0, False, "0", "false", "False") else 1


def _maintenant(date=None):
    return _date_iso(date or datetime.date.today(), "date", obligatoire=True)


def _liste_pairs(donnees, ordre):
    return [(champ, donnees.get(champ)) for champ in ordre if champ in donnees]


def _rollback(db):
    for attribut in ("connexion", "conn"):
        connexion = getattr(db, attribut, None)
        if connexion is not None:
            try:
                connexion.rollback()
            except Exception:
                pass
            return


def _verifier_periode(date_debut, date_fin, prefixe="programmation"):
    debut = _date_obj(date_debut, "%s.date_debut" % prefixe, obligatoire=True)
    fin = _date_obj(date_fin, "%s.date_fin" % prefixe, obligatoire=True)
    if fin < debut:
        raise ValueError("date_fin ne peut pas précéder date_debut")
    return debut, fin


def NormaliserProgrammation(donnees, creation=True, date=None):
    donnees = dict(donnees or {})
    if not donnees:
        raise ValueError("Aucune donnée de programmation")

    resultat = {}
    if creation:
        resultat["uid"] = _uid("PROG", donnees.get("uid"), generer=True)
        type_source = _texte(donnees.get("type_source"))
        if type_source not in TYPES_SOURCE:
            raise ValueError("type_source doit être relation ou activite")
        resultat["type_source"] = type_source
        IDrelation = _entier_positif(
            donnees.get("IDrelation_structure"), "IDrelation_structure"
        )
        IDactivite = _entier_positif(donnees.get("IDactivite"), "IDactivite")
        IDgroupe = _entier_positif(
            donnees.get("IDgroupe_activite"), "IDgroupe_activite"
        )
        if type_source == TYPE_SOURCE_RELATION:
            if not IDrelation or IDactivite or IDgroupe:
                raise ValueError("Une programmation relation exige uniquement IDrelation_structure")
        else:
            if not IDactivite or IDrelation:
                raise ValueError("Une programmation activité exige IDactivite et aucune relation")
        resultat["IDrelation_structure"] = IDrelation
        resultat["IDactivite"] = IDactivite
        resultat["IDgroupe_activite"] = IDgroupe
        resultat["IDprogrammation_parent"] = _entier_positif(
            donnees.get("IDprogrammation_parent"), "IDprogrammation_parent"
        )
        resultat["statut"] = STATUT_BROUILLON
    else:
        proteges = (
            "uid", "type_source", "IDrelation_structure", "IDactivite",
            "IDgroupe_activite", "IDprogrammation_parent", "statut",
            "date_creation", "actif",
        )
        if any(champ in donnees for champ in proteges):
            raise ValueError("Modification directe d'un champ protégé de programmation")

    if creation or "saison" in donnees:
        saison = _texte(donnees.get("saison"))
        if not saison:
            raise ValueError("saison est obligatoire")
        resultat["saison"] = saison
    for champ in ("libelle", "UIDintervenant_habituel", "memo"):
        if creation or champ in donnees:
            resultat[champ] = _texte(donnees.get(champ))

    if creation or "date_debut" in donnees:
        resultat["date_debut"] = _date_iso(
            donnees.get("date_debut"), "date_debut", obligatoire=creation
        )
    if creation or "date_fin" in donnees:
        resultat["date_fin"] = _date_iso(
            donnees.get("date_fin"), "date_fin", obligatoire=creation
        )
    if creation:
        _verifier_periode(resultat["date_debut"], resultat["date_fin"])

    if creation or "IDlieu_habituel" in donnees:
        resultat["IDlieu_habituel"] = _entier_positif(
            donnees.get("IDlieu_habituel"), "IDlieu_habituel"
        )
    resultat["date_modification"] = _maintenant(date)
    if creation:
        resultat["actif"] = 1
        resultat["date_creation"] = _maintenant(donnees.get("date_creation") or date)
    return resultat


def NormaliserCreneau(donnees, creation=True, date=None):
    donnees = dict(donnees or {})
    if not donnees:
        raise ValueError("Aucune donnée de créneau")

    resultat = {}
    if creation:
        resultat["uid"] = _uid("CREN", donnees.get("uid"), generer=True)
        resultat["IDprogrammation_structure"] = _entier_positif(
            donnees.get("IDprogrammation_structure"),
            "IDprogrammation_structure",
            obligatoire=True,
        )
        resultat["IDcreneau_source"] = _entier_positif(
            donnees.get("IDcreneau_source"), "IDcreneau_source"
        )
    else:
        proteges = (
            "uid", "IDprogrammation_structure", "IDcreneau_source",
            "etat_renouvellement", "date_creation", "actif",
        )
        if any(champ in donnees for champ in proteges):
            raise ValueError("Modification directe d'un champ protégé de créneau")

    if creation or "jour_semaine" in donnees:
        try:
            jour = int(donnees.get("jour_semaine"))
        except (TypeError, ValueError):
            raise ValueError("jour_semaine doit être compris entre 0 et 6")
        if jour < 0 or jour > 6:
            raise ValueError("jour_semaine doit être compris entre 0 et 6")
        resultat["jour_semaine"] = jour

    if creation or "heure_debut" in donnees:
        resultat["heure_debut"] = _heure(donnees.get("heure_debut"), "heure_debut")
    if creation or "heure_fin" in donnees:
        resultat["heure_fin"] = _heure(donnees.get("heure_fin"), "heure_fin")
    if creation and resultat["heure_fin"] <= resultat["heure_debut"]:
        raise ValueError("heure_fin doit être postérieure à heure_debut")

    for champ in ("date_debut", "date_fin"):
        if creation or champ in donnees:
            resultat[champ] = _date_iso(donnees.get(champ), champ)
    if creation and resultat.get("date_debut") and resultat.get("date_fin"):
        if resultat["date_fin"] < resultat["date_debut"]:
            raise ValueError("date_fin du créneau ne peut pas précéder date_debut")

    if creation or "appliquer_scolaire" in donnees:
        resultat["appliquer_scolaire"] = _booleen(
            donnees.get("appliquer_scolaire"), defaut=True
        )
    if creation or "appliquer_vacances" in donnees:
        resultat["appliquer_vacances"] = _booleen(
            donnees.get("appliquer_vacances"), defaut=False
        )
    if creation:
        if not resultat["appliquer_scolaire"] and not resultat["appliquer_vacances"]:
            raise ValueError("Le créneau doit s'appliquer en période scolaire ou vacances")
    if creation or "inclure_feries" in donnees:
        resultat["inclure_feries"] = _booleen(
            donnees.get("inclure_feries"), defaut=False
        )

    if creation or "frequence" in donnees:
        try:
            frequence = int(donnees.get("frequence", 1))
        except (TypeError, ValueError):
            raise ValueError("frequence invalide")
        if frequence not in FREQUENCES:
            raise ValueError("frequence doit être un code historique de 1 à 6")
        resultat["frequence"] = frequence

    if creation or "IDlieu" in donnees:
        resultat["IDlieu"] = _entier_positif(donnees.get("IDlieu"), "IDlieu")
    for champ in ("groupe", "observations"):
        if creation or champ in donnees:
            resultat[champ] = _texte(donnees.get(champ))

    if creation:
        etat = _texte(donnees.get("etat_renouvellement"))
        if not etat:
            etat = (
                RENOUVELLEMENT_INCHANGE
                if resultat.get("IDcreneau_source")
                else RENOUVELLEMENT_AJOUTE
            )
        if etat not in ETATS_RENOUVELLEMENT:
            raise ValueError("etat_renouvellement invalide")
        if resultat.get("IDcreneau_source") and etat == RENOUVELLEMENT_AJOUTE:
            raise ValueError("Un créneau renouvelé ne peut pas être marqué ajouté")
        if not resultat.get("IDcreneau_source") and etat != RENOUVELLEMENT_AJOUTE:
            raise ValueError("Un nouveau créneau doit être marqué ajouté")
        resultat["etat_renouvellement"] = etat
        resultat["actif"] = 1
        resultat["date_creation"] = _maintenant(donnees.get("date_creation") or date)
    resultat["date_modification"] = _maintenant(date)
    return resultat


class GestionnaireProgrammationsStructures(object):
    def __init__(self, db):
        self.db = db
        self.relations = UTILS_Relations_Structures.GestionnaireRelationsStructures(db)

    def LireProgrammation(self, IDprogrammation_structure):
        IDprogrammation_structure = _entier_positif(
            IDprogrammation_structure, "IDprogrammation_structure", obligatoire=True
        )
        req = "SELECT IDprogrammation_structure, %s FROM structures_programmations WHERE IDprogrammation_structure=%d;" % (
            ", ".join(CHAMPS_PROGRAMMATION), IDprogrammation_structure
        )
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq() or []
        if not lignes:
            return None
        return dict(zip(("IDprogrammation_structure",) + CHAMPS_PROGRAMMATION, lignes[0]))

    def LireProgrammationParUID(self, uid):
        uid = _uid("PROG", uid, generer=False)
        req = "SELECT IDprogrammation_structure, %s FROM structures_programmations WHERE uid='%s';" % (
            ", ".join(CHAMPS_PROGRAMMATION), _sql_texte(uid)
        )
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq() or []
        if len(lignes) > 1:
            raise RuntimeError("UID de programmation dupliqué")
        if not lignes:
            return None
        return dict(zip(("IDprogrammation_structure",) + CHAMPS_PROGRAMMATION, lignes[0]))

    def LireCreneau(self, IDcreneau_programmation):
        IDcreneau_programmation = _entier_positif(
            IDcreneau_programmation, "IDcreneau_programmation", obligatoire=True
        )
        req = "SELECT IDcreneau_programmation, %s FROM structures_programmations_creneaux WHERE IDcreneau_programmation=%d;" % (
            ", ".join(CHAMPS_CRENEAU), IDcreneau_programmation
        )
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq() or []
        if not lignes:
            return None
        return dict(zip(("IDcreneau_programmation",) + CHAMPS_CRENEAU, lignes[0]))

    def _source_existe(self, valeurs):
        if valeurs["type_source"] == TYPE_SOURCE_RELATION:
            relation = self.relations.LireRelation(valeurs["IDrelation_structure"])
            if not relation:
                raise ValueError("Relation contractuelle introuvable")
            return relation
        if not self.db.IsTableExists("activites"):
            raise ValueError("Table activites introuvable")
        req = "SELECT IDactivite FROM activites WHERE IDactivite=%d;" % int(valeurs["IDactivite"])
        if self.db.ExecuterReq(req) != 1 or not (self.db.ResultatReq() or []):
            raise ValueError("Activité Noethys introuvable")
        return None

    def _verifier_periode_source(self, valeurs, relation=None):
        debut, fin = _verifier_periode(valeurs["date_debut"], valeurs["date_fin"])
        if relation:
            debut_relation = _date_obj(relation.get("date_debut"), "relation.date_debut")
            fin_relation = _date_obj(relation.get("date_fin"), "relation.date_fin")
            if debut_relation and debut < debut_relation:
                raise ValueError("La programmation débute avant la relation")
            if fin_relation and fin > fin_relation:
                raise ValueError("La programmation se termine après la relation")

    def _programmation_source_saison_existe(self, valeurs):
        conditions = [
            "type_source='%s'" % _sql_texte(valeurs["type_source"]),
            "saison='%s'" % _sql_texte(valeurs["saison"]),
            "actif=1",
        ]
        if valeurs["type_source"] == TYPE_SOURCE_RELATION:
            conditions.append("IDrelation_structure=%d" % int(valeurs["IDrelation_structure"]))
        else:
            conditions.append("IDactivite=%d" % int(valeurs["IDactivite"]))
            if valeurs.get("IDgroupe_activite"):
                conditions.append("IDgroupe_activite=%d" % int(valeurs["IDgroupe_activite"]))
            else:
                conditions.append("IDgroupe_activite IS NULL")
        req = "SELECT IDprogrammation_structure FROM structures_programmations WHERE %s;" % " AND ".join(conditions)
        if self.db.ExecuterReq(req) != 1:
            return False
        return bool(self.db.ResultatReq() or [])

    def CreerProgrammation(self, donnees, date=None, commit=True):
        valeurs = NormaliserProgrammation(donnees, creation=True, date=date)
        if self.LireProgrammationParUID(valeurs["uid"]):
            raise ValueError("UID de programmation déjà utilisé")
        relation = self._source_existe(valeurs)
        self._verifier_periode_source(valeurs, relation=relation)
        if self._programmation_source_saison_existe(valeurs):
            raise ValueError("Une programmation active existe déjà pour cette source et cette saison")
        return self.db.ReqInsert(
            "structures_programmations",
            _liste_pairs(valeurs, CHAMPS_PROGRAMMATION),
            commit=commit,
        )

    def ModifierProgrammation(self, IDprogrammation_structure, donnees, date=None):
        courant = self.LireProgrammation(IDprogrammation_structure)
        if not courant:
            raise ValueError("Programmation introuvable")
        if courant["statut"] != STATUT_BROUILLON:
            raise ValueError("Seule une programmation brouillon est modifiable")
        changements = NormaliserProgrammation(donnees, creation=False, date=date)
        debut = changements.get("date_debut", courant["date_debut"])
        fin = changements.get("date_fin", courant["date_fin"])
        _verifier_periode(debut, fin)
        controle = dict(courant)
        controle.update(changements)
        relation = self._source_existe(controle)
        self._verifier_periode_source(controle, relation=relation)
        return self.db.ReqMAJ(
            "structures_programmations",
            _liste_pairs(changements, CHAMPS_PROGRAMMATION),
            "IDprogrammation_structure",
            int(IDprogrammation_structure),
        )

    def ListerProgrammations(self, type_source=None, IDsource=None, actifs_seulement=True):
        conditions = []
        if type_source:
            if type_source not in TYPES_SOURCE:
                raise ValueError("type_source invalide")
            conditions.append("type_source='%s'" % _sql_texte(type_source))
            if IDsource:
                champ = "IDrelation_structure" if type_source == TYPE_SOURCE_RELATION else "IDactivite"
                conditions.append("%s=%d" % (champ, int(IDsource)))
        if actifs_seulement:
            conditions.append("actif=1")
        req = "SELECT IDprogrammation_structure, %s FROM structures_programmations" % ", ".join(CHAMPS_PROGRAMMATION)
        if conditions:
            req += " WHERE " + " AND ".join(conditions)
        req += " ORDER BY saison, IDprogrammation_structure;"
        if self.db.ExecuterReq(req) != 1:
            return []
        return [
            dict(zip(("IDprogrammation_structure",) + CHAMPS_PROGRAMMATION, ligne))
            for ligne in (self.db.ResultatReq() or [])
        ]

    def _changer_statut(self, IDprogrammation_structure, attendu, nouveau, date=None):
        courant = self.LireProgrammation(IDprogrammation_structure)
        if not courant:
            raise ValueError("Programmation introuvable")
        if courant["statut"] == nouveau:
            return True
        if courant["statut"] not in attendu:
            raise ValueError("Transition de statut de programmation invalide")
        return self.db.ReqMAJ(
            "structures_programmations",
            [("statut", nouveau), ("date_modification", _maintenant(date))],
            "IDprogrammation_structure",
            int(IDprogrammation_structure),
        )

    def SoumettreProgrammation(self, IDprogrammation_structure, date=None):
        return self._changer_statut(
            IDprogrammation_structure, (STATUT_BROUILLON,), STATUT_SOUMISE, date=date
        )

    def ValiderProgrammation(self, IDprogrammation_structure, date=None):
        creneaux = self.ListerCreneaux(IDprogrammation_structure, conserves_seulement=True)
        if not creneaux:
            raise ValueError("Une programmation validée doit contenir au moins un créneau")
        return self._changer_statut(
            IDprogrammation_structure,
            (STATUT_BROUILLON, STATUT_SOUMISE),
            STATUT_VALIDEE,
            date=date,
        )

    def AnnulerProgrammation(self, IDprogrammation_structure, date=None):
        return self._changer_statut(
            IDprogrammation_structure,
            (STATUT_BROUILLON, STATUT_SOUMISE, STATUT_VALIDEE),
            STATUT_ANNULEE,
            date=date,
        )

    def ArchiverProgrammation(self, IDprogrammation_structure, date=None):
        courant = self.LireProgrammation(IDprogrammation_structure)
        if not courant:
            raise ValueError("Programmation introuvable")
        if courant["statut"] != STATUT_ANNULEE:
            raise ValueError("Seule une programmation annulée peut être archivée")
        return self.db.ReqMAJ(
            "structures_programmations",
            [("actif", 0), ("date_modification", _maintenant(date))],
            "IDprogrammation_structure",
            int(IDprogrammation_structure),
        )

    def _exiger_brouillon(self, IDprogrammation_structure):
        programmation = self.LireProgrammation(IDprogrammation_structure)
        if not programmation:
            raise ValueError("Programmation introuvable")
        if programmation["statut"] != STATUT_BROUILLON:
            raise ValueError("Les créneaux ne sont modifiables qu'en brouillon")
        return programmation

    def _verifier_creneau_dans_programmation(self, programmation, valeurs):
        debut_programme, fin_programme = _verifier_periode(
            programmation["date_debut"], programmation["date_fin"]
        )
        debut = _date_obj(valeurs.get("date_debut"), "creneau.date_debut")
        fin = _date_obj(valeurs.get("date_fin"), "creneau.date_fin")
        if debut and debut < debut_programme:
            raise ValueError("Le créneau débute avant la programmation")
        if fin and fin > fin_programme:
            raise ValueError("Le créneau se termine après la programmation")
        if debut and fin and fin < debut:
            raise ValueError("date_fin du créneau ne peut pas précéder date_debut")

    def AjouterCreneau(self, IDprogrammation_structure, donnees, date=None, commit=True):
        programmation = self._exiger_brouillon(IDprogrammation_structure)
        donnees = dict(donnees or {})
        donnees["IDprogrammation_structure"] = int(IDprogrammation_structure)
        valeurs = NormaliserCreneau(donnees, creation=True, date=date)
        self._verifier_creneau_dans_programmation(programmation, valeurs)
        if self.LireCreneauParUID(valeurs["uid"]):
            raise ValueError("UID de créneau déjà utilisé")
        if valeurs.get("IDcreneau_source"):
            source = self.LireCreneau(valeurs["IDcreneau_source"])
            if not source:
                raise ValueError("Créneau source introuvable")
        return self.db.ReqInsert(
            "structures_programmations_creneaux",
            _liste_pairs(valeurs, CHAMPS_CRENEAU),
            commit=commit,
        )

    def LireCreneauParUID(self, uid):
        uid = _uid("CREN", uid, generer=False)
        req = "SELECT IDcreneau_programmation, %s FROM structures_programmations_creneaux WHERE uid='%s';" % (
            ", ".join(CHAMPS_CRENEAU), _sql_texte(uid)
        )
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq() or []
        if len(lignes) > 1:
            raise RuntimeError("UID de créneau dupliqué")
        if not lignes:
            return None
        return dict(zip(("IDcreneau_programmation",) + CHAMPS_CRENEAU, lignes[0]))

    def ListerCreneaux(self, IDprogrammation_structure, actifs_seulement=True, conserves_seulement=False):
        IDprogrammation_structure = _entier_positif(
            IDprogrammation_structure, "IDprogrammation_structure", obligatoire=True
        )
        conditions = ["IDprogrammation_structure=%d" % IDprogrammation_structure]
        if actifs_seulement:
            conditions.append("actif=1")
        if conserves_seulement:
            conditions.append("etat_renouvellement<>'supprime'")
        req = "SELECT IDcreneau_programmation, %s FROM structures_programmations_creneaux WHERE %s ORDER BY jour_semaine, heure_debut, IDcreneau_programmation;" % (
            ", ".join(CHAMPS_CRENEAU), " AND ".join(conditions)
        )
        if self.db.ExecuterReq(req) != 1:
            return []
        return [
            dict(zip(("IDcreneau_programmation",) + CHAMPS_CRENEAU, ligne))
            for ligne in (self.db.ResultatReq() or [])
        ]

    def ModifierCreneau(self, IDcreneau_programmation, donnees, date=None):
        courant = self.LireCreneau(IDcreneau_programmation)
        if not courant:
            raise ValueError("Créneau introuvable")
        programmation = self._exiger_brouillon(courant["IDprogrammation_structure"])
        changements = NormaliserCreneau(donnees, creation=False, date=date)
        controle = dict(courant)
        controle.update(changements)
        if controle["heure_fin"] <= controle["heure_debut"]:
            raise ValueError("heure_fin doit être postérieure à heure_debut")
        if not controle.get("appliquer_scolaire") and not controle.get("appliquer_vacances"):
            raise ValueError("Le créneau doit s'appliquer en période scolaire ou vacances")
        self._verifier_creneau_dans_programmation(programmation, controle)
        if courant.get("IDcreneau_source"):
            changements["etat_renouvellement"] = RENOUVELLEMENT_MODIFIE
        return self.db.ReqMAJ(
            "structures_programmations_creneaux",
            _liste_pairs(changements, CHAMPS_CRENEAU),
            "IDcreneau_programmation",
            int(IDcreneau_programmation),
        )

    def SupprimerCreneau(self, IDcreneau_programmation, date=None):
        courant = self.LireCreneau(IDcreneau_programmation)
        if not courant:
            raise ValueError("Créneau introuvable")
        self._exiger_brouillon(courant["IDprogrammation_structure"])
        valeurs = [("date_modification", _maintenant(date))]
        if courant.get("IDcreneau_source"):
            valeurs.append(("etat_renouvellement", RENOUVELLEMENT_SUPPRIME))
        else:
            valeurs.append(("actif", 0))
        return self.db.ReqMAJ(
            "structures_programmations_creneaux",
            valeurs,
            "IDcreneau_programmation",
            int(IDcreneau_programmation),
        )

    def ConstruireRegleRecurrence(self, IDcreneau_programmation, exiger_validee=False):
        creneau = self.LireCreneau(IDcreneau_programmation)
        if not creneau or not creneau.get("actif"):
            raise ValueError("Créneau actif introuvable")
        if creneau.get("etat_renouvellement") == RENOUVELLEMENT_SUPPRIME:
            raise ValueError("Un créneau supprimé ne produit pas de récurrence")
        programmation = self.LireProgrammation(creneau["IDprogrammation_structure"])
        if not programmation or not programmation.get("actif"):
            raise ValueError("Programmation active introuvable")
        if programmation["statut"] == STATUT_ANNULEE:
            raise ValueError("Une programmation annulée ne produit pas de récurrence")
        if exiger_validee and programmation["statut"] != STATUT_VALIDEE:
            raise ValueError("La programmation doit être validée")
        date_debut = creneau.get("date_debut") or programmation["date_debut"]
        date_fin = creneau.get("date_fin") or programmation["date_fin"]
        return {
            "date_debut": _date_obj(date_debut, "date_debut", obligatoire=True),
            "date_fin": _date_obj(date_fin, "date_fin", obligatoire=True),
            "heure_debut": creneau["heure_debut"],
            "heure_fin": creneau["heure_fin"],
            "jours_vacances": [int(creneau["jour_semaine"])] if creneau.get("appliquer_vacances") else [],
            "jours_scolaires": [int(creneau["jour_semaine"])] if creneau.get("appliquer_scolaire") else [],
            "semaines": int(creneau["frequence"]),
            "feries": bool(creneau.get("inclure_feries")),
        }

    def RenouvelerProgrammation(
        self,
        IDprogrammation_parent,
        saison,
        date_debut,
        date_fin,
        source=None,
        uid=None,
        date=None,
    ):
        parent = self.LireProgrammation(IDprogrammation_parent)
        if not parent:
            raise ValueError("Programmation parente introuvable")
        if parent["statut"] != STATUT_VALIDEE:
            raise ValueError("Seule une programmation validée peut être renouvelée")

        source = dict(source or {})
        type_source = source.get("type_source") or parent["type_source"]
        donnees = {
            "uid": uid,
            "type_source": type_source,
            "IDrelation_structure": source.get("IDrelation_structure") if type_source == TYPE_SOURCE_RELATION else None,
            "IDactivite": source.get("IDactivite") if type_source == TYPE_SOURCE_ACTIVITE else None,
            "IDgroupe_activite": source.get("IDgroupe_activite") if type_source == TYPE_SOURCE_ACTIVITE else None,
            "IDprogrammation_parent": parent["IDprogrammation_structure"],
            "saison": saison,
            "libelle": parent.get("libelle") or "",
            "date_debut": date_debut,
            "date_fin": date_fin,
            "UIDintervenant_habituel": parent.get("UIDintervenant_habituel") or "",
            "IDlieu_habituel": parent.get("IDlieu_habituel"),
            "memo": parent.get("memo") or "",
        }
        if not source:
            donnees["IDrelation_structure"] = parent.get("IDrelation_structure")
            donnees["IDactivite"] = parent.get("IDactivite")
            donnees["IDgroupe_activite"] = parent.get("IDgroupe_activite")

        valeurs = NormaliserProgrammation(donnees, creation=True, date=date)
        relation = self._source_existe(valeurs)
        self._verifier_periode_source(valeurs, relation=relation)
        if self._programmation_source_saison_existe(valeurs):
            raise ValueError("Une programmation active existe déjà pour cette source et cette saison")

        try:
            IDnouvelle = self.db.ReqInsert(
                "structures_programmations",
                _liste_pairs(valeurs, CHAMPS_PROGRAMMATION),
                commit=False,
            )
            for ancien in self.ListerCreneaux(
                IDprogrammation_parent,
                actifs_seulement=True,
                conserves_seulement=True,
            ):
                etat = (
                    RENOUVELLEMENT_MODIFIE
                    if ancien.get("date_debut") or ancien.get("date_fin")
                    else RENOUVELLEMENT_INCHANGE
                )
                clone = NormaliserCreneau({
                    "IDprogrammation_structure": IDnouvelle,
                    "IDcreneau_source": ancien["IDcreneau_programmation"],
                    "jour_semaine": ancien["jour_semaine"],
                    "heure_debut": ancien["heure_debut"],
                    "heure_fin": ancien["heure_fin"],
                    # Les dates exactes N-1 ne sont jamais transposées implicitement.
                    "date_debut": None,
                    "date_fin": None,
                    "appliquer_scolaire": ancien["appliquer_scolaire"],
                    "appliquer_vacances": ancien["appliquer_vacances"],
                    "inclure_feries": ancien["inclure_feries"],
                    "frequence": ancien["frequence"],
                    "IDlieu": ancien.get("IDlieu"),
                    "groupe": ancien.get("groupe") or "",
                    "observations": ancien.get("observations") or "",
                    "etat_renouvellement": etat,
                }, creation=True, date=date)
                self.db.ReqInsert(
                    "structures_programmations_creneaux",
                    _liste_pairs(clone, CHAMPS_CRENEAU),
                    commit=False,
                )
            self.db.Commit()
            return IDnouvelle
        except Exception:
            _rollback(self.db)
            raise
