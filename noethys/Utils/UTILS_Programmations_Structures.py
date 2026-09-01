#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Programmations annuelles et aperçu d'occurrences Noe-062E.

Le service persiste les programmations et créneaux. Il ne recode pas le moteur
historique vacances/fériés/récurrences : ``GenererApercuOccurrences`` exige un
calculateur injecté acceptant le contrat historique de
``DLG_Saisie_location.Calcule_occurences``.
"""
from __future__ import unicode_literals

import datetime
import hashlib
import uuid

from Utils import UTILS_Relations_Structures


STATUT_BROUILLON = "brouillon"
STATUT_SOUMISE = "soumise"
STATUT_VALIDEE = "validee"
STATUT_ANNULEE = "annulee"
STATUTS_PROGRAMMATION = (
    STATUT_BROUILLON,
    STATUT_SOUMISE,
    STATUT_VALIDEE,
    STATUT_ANNULEE,
)

RENOUVELLEMENT_INCHANGE = "inchange"
RENOUVELLEMENT_MODIFIE = "modifie"
RENOUVELLEMENT_SUPPRIME = "supprime"
RENOUVELLEMENT_AJOUTE = "ajoute"
ETATS_RENOUVELLEMENT = (
    RENOUVELLEMENT_INCHANGE,
    RENOUVELLEMENT_MODIFIE,
    RENOUVELLEMENT_SUPPRIME,
    RENOUVELLEMENT_AJOUTE,
)

FREQUENCES_HISTORIQUES = (1, 2, 3, 4, 5, 6)
NATURES = ("sport", "animation", "autre")
JOURS = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")

CHAMPS_PROGRAMMATION = (
    "uid",
    "IDrelation_structure",
    "IDprogrammation_source",
    "saison",
    "statut",
    "date_debut",
    "date_fin",
    "notes",
    "actif",
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
    "IDgroupe_structure",
    "IDlieu",
    "nature",
    "libelle",
    "appliquer_scolaire",
    "appliquer_vacances",
    "inclure_feries",
    "frequence",
    "etat_renouvellement",
    "observations",
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


def _date_obj(valeur, nom_champ):
    iso = _date_iso(valeur, nom_champ, obligatoire=True)
    return datetime.datetime.strptime(iso, "%Y-%m-%d").date()


def _heure(valeur, nom_champ):
    texte = _texte(valeur)
    try:
        return datetime.datetime.strptime(texte, "%H:%M").strftime("%H:%M")
    except (TypeError, ValueError):
        raise ValueError("%s doit être une heure HH:MM" % nom_champ)


def _duree_minutes(debut, fin):
    d = datetime.datetime.strptime(_heure(debut, "heure_debut"), "%H:%M")
    f = datetime.datetime.strptime(_heure(fin, "heure_fin"), "%H:%M")
    minutes = int((f - d).total_seconds() // 60)
    if minutes <= 0:
        raise ValueError("heure_fin doit être postérieure à heure_debut")
    return minutes


def _entier(valeur, nom_champ, obligatoire=False):
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


def _bool01(valeur, defaut=False):
    if valeur is None:
        valeur = defaut
    return 0 if valeur in (0, False, "0", "false", "False") else 1


def _uid(prefixe, valeur=None, generer=True):
    valeur = _texte(valeur)
    if not valeur:
        if not generer:
            raise ValueError("UID obligatoire")
        return "%s-%s" % (prefixe, uuid.uuid4().hex)
    if len(valeur) > 64 or not all(c.isalnum() or c in "-_" for c in valeur):
        raise ValueError("UID invalide")
    return valeur


def _liste_pairs(donnees, ordre):
    return [(champ, donnees.get(champ)) for champ in ordre if champ in donnees]


def _maintenant(date=None):
    return _date_iso(date or datetime.date.today(), "date", obligatoire=True)


def NormaliserProgrammation(donnees, creation=True, date=None):
    donnees = dict(donnees or {})
    if not donnees:
        raise ValueError("Aucune donnée de programmation")
    resultat = {}
    if creation:
        resultat["uid"] = _uid("PROG", donnees.get("uid"))
        resultat["IDrelation_structure"] = _entier(
            donnees.get("IDrelation_structure"), "IDrelation_structure", obligatoire=True
        )
        resultat["IDprogrammation_source"] = _entier(
            donnees.get("IDprogrammation_source"), "IDprogrammation_source"
        )
        saison = _texte(donnees.get("saison"))
        if not saison:
            raise ValueError("saison obligatoire")
        resultat["saison"] = saison
        statut = _texte(donnees.get("statut")) or STATUT_BROUILLON
        if statut != STATUT_BROUILLON:
            raise ValueError("Une programmation est créée en brouillon")
        resultat["statut"] = statut
    else:
        interdits = ("uid", "IDrelation_structure", "IDprogrammation_source", "statut", "date_creation")
        if any(champ in donnees for champ in interdits):
            raise ValueError("Modification directe d'un champ protégé")
        if "saison" in donnees:
            saison = _texte(donnees.get("saison"))
            if not saison:
                raise ValueError("saison ne peut pas être vide")
            resultat["saison"] = saison

    debut = None
    fin = None
    if creation or "date_debut" in donnees:
        debut = _date_iso(donnees.get("date_debut"), "date_debut", obligatoire=creation)
        resultat["date_debut"] = debut
    if creation or "date_fin" in donnees:
        fin = _date_iso(donnees.get("date_fin"), "date_fin", obligatoire=creation)
        resultat["date_fin"] = fin
    if creation and fin < debut:
        raise ValueError("date_fin ne peut pas précéder date_debut")
    if creation or "notes" in donnees:
        resultat["notes"] = _texte(donnees.get("notes"))
    if creation or "actif" in donnees:
        resultat["actif"] = _bool01(donnees.get("actif"), True)
    resultat["date_modification"] = _maintenant(date)
    if creation:
        resultat["date_creation"] = _maintenant(donnees.get("date_creation") or date)
    return resultat


def NormaliserCreneau(donnees, creation=True, date=None):
    donnees = dict(donnees or {})
    if not donnees:
        raise ValueError("Aucune donnée de créneau")
    resultat = {}
    if creation:
        resultat["uid"] = _uid("CRN", donnees.get("uid"))
        resultat["IDprogrammation_structure"] = _entier(
            donnees.get("IDprogrammation_structure"), "IDprogrammation_structure", obligatoire=True
        )
        resultat["IDcreneau_source"] = _entier(donnees.get("IDcreneau_source"), "IDcreneau_source")
    else:
        interdits = ("uid", "IDprogrammation_structure", "IDcreneau_source", "date_creation")
        if any(champ in donnees for champ in interdits):
            raise ValueError("Modification directe d'un champ protégé")

    if creation or "jour_semaine" in donnees:
        try:
            jour = int(donnees.get("jour_semaine"))
        except (TypeError, ValueError):
            raise ValueError("jour_semaine doit être compris entre 0 et 6")
        if not 0 <= jour <= 6:
            raise ValueError("jour_semaine doit être compris entre 0 et 6")
        resultat["jour_semaine"] = jour

    debut_h = fin_h = None
    if creation or "heure_debut" in donnees:
        debut_h = _heure(donnees.get("heure_debut"), "heure_debut")
        resultat["heure_debut"] = debut_h
    if creation or "heure_fin" in donnees:
        fin_h = _heure(donnees.get("heure_fin"), "heure_fin")
        resultat["heure_fin"] = fin_h
    if creation:
        _duree_minutes(debut_h, fin_h)

    debut = fin = None
    if creation or "date_debut" in donnees:
        debut = _date_iso(donnees.get("date_debut"), "date_debut")
        resultat["date_debut"] = debut
    if creation or "date_fin" in donnees:
        fin = _date_iso(donnees.get("date_fin"), "date_fin")
        resultat["date_fin"] = fin
    if creation and debut and fin and fin < debut:
        raise ValueError("date_fin ne peut pas précéder date_debut")

    for champ in ("IDgroupe_structure", "IDlieu"):
        if creation or champ in donnees:
            resultat[champ] = _entier(donnees.get(champ), champ)

    if creation or "nature" in donnees:
        nature = _texte(donnees.get("nature")) or "autre"
        if nature not in NATURES:
            raise ValueError("nature inconnue: %s" % nature)
        resultat["nature"] = nature
    if creation or "libelle" in donnees:
        resultat["libelle"] = _texte(donnees.get("libelle")) or u"Séance"

    for champ, defaut in (
        ("appliquer_scolaire", True),
        ("appliquer_vacances", False),
        ("inclure_feries", False),
    ):
        if creation or champ in donnees:
            resultat[champ] = _bool01(donnees.get(champ), defaut)
    if creation and not resultat["appliquer_scolaire"] and not resultat["appliquer_vacances"]:
        raise ValueError("Le créneau doit s'appliquer au scolaire, aux vacances ou aux deux")

    if creation or "frequence" in donnees:
        try:
            frequence = int(donnees.get("frequence", 1))
        except (TypeError, ValueError):
            raise ValueError("fréquence historique invalide")
        if frequence not in FREQUENCES_HISTORIQUES:
            raise ValueError("fréquence historique inconnue: %s" % frequence)
        resultat["frequence"] = frequence

    if creation or "etat_renouvellement" in donnees:
        etat = _texte(donnees.get("etat_renouvellement")) or RENOUVELLEMENT_AJOUTE
        if etat not in ETATS_RENOUVELLEMENT:
            raise ValueError("état de renouvellement inconnu: %s" % etat)
        resultat["etat_renouvellement"] = etat
    if creation or "observations" in donnees:
        resultat["observations"] = _texte(donnees.get("observations"))
    if creation or "actif" in donnees:
        resultat["actif"] = _bool01(donnees.get("actif"), True)
    resultat["date_modification"] = _maintenant(date)
    if creation:
        resultat["date_creation"] = _maintenant(donnees.get("date_creation") or date)
    return resultat


class GestionnaireProgrammationsStructures(object):
    def __init__(self, db):
        self.db = db
        self.relations = UTILS_Relations_Structures.GestionnaireRelationsStructures(db)

    def _lire(self, table, cle, ID, champs):
        req = "SELECT %s, %s FROM %s WHERE %s=%d;" % (cle, ", ".join(champs), table, cle, int(ID))
        if self.db.ExecuterReq(req) != 1:
            return None
        lignes = self.db.ResultatReq() or []
        if not lignes:
            return None
        return dict(zip((cle,) + champs, lignes[0]))

    def LireProgrammation(self, IDprogrammation_structure):
        return self._lire(
            "structures_programmations", "IDprogrammation_structure",
            IDprogrammation_structure, CHAMPS_PROGRAMMATION
        )

    def LireCreneau(self, IDcreneau_programmation):
        return self._lire(
            "structures_programmations_creneaux", "IDcreneau_programmation",
            IDcreneau_programmation, CHAMPS_CRENEAU
        )

    def _uid_existe(self, table, uid):
        req = "SELECT 1 FROM %s WHERE uid='%s';" % (table, uid)
        return self.db.ExecuterReq(req) == 1 and bool(self.db.ResultatReq() or [])

    def _verifier_relation(self, IDrelation_structure):
        relation = self.relations.LireRelation(IDrelation_structure)
        if not relation:
            raise ValueError("Relation contractuelle introuvable")
        if relation.get("actif") in (0, False, "0"):
            raise ValueError("Relation contractuelle archivée")
        return relation

    def _verifier_programmation_brouillon(self, IDprogrammation_structure):
        programmation = self.LireProgrammation(IDprogrammation_structure)
        if not programmation:
            raise ValueError("Programmation introuvable")
        if programmation["statut"] != STATUT_BROUILLON:
            raise ValueError("Seule une programmation brouillon est modifiable")
        return programmation

    def CreerProgrammation(self, donnees, date=None):
        valeurs = NormaliserProgrammation(donnees, creation=True, date=date)
        relation = self._verifier_relation(valeurs["IDrelation_structure"])
        if self._uid_existe("structures_programmations", valeurs["uid"]):
            raise ValueError("UID de programmation déjà utilisé")
        req = (
            "SELECT IDprogrammation_structure FROM structures_programmations "
            "WHERE IDrelation_structure=%d AND saison='%s' AND actif=1;"
        ) % (valeurs["IDrelation_structure"], valeurs["saison"])
        if self.db.ExecuterReq(req) == 1 and (self.db.ResultatReq() or []):
            raise ValueError("Une programmation active existe déjà pour cette relation et cette saison")
        debut_relation = relation.get("date_debut")
        fin_relation = relation.get("date_fin")
        if debut_relation and valeurs["date_debut"] < debut_relation:
            raise ValueError("La programmation débute avant la relation")
        if fin_relation and valeurs["date_fin"] > fin_relation:
            raise ValueError("La programmation se termine après la relation")
        return self.db.ReqInsert(
            "structures_programmations", _liste_pairs(valeurs, CHAMPS_PROGRAMMATION)
        )

    def ModifierProgrammation(self, IDprogrammation_structure, donnees, date=None):
        courant = self._verifier_programmation_brouillon(IDprogrammation_structure)
        valeurs = NormaliserProgrammation(donnees, creation=False, date=date)
        debut = valeurs.get("date_debut", courant["date_debut"])
        fin = valeurs.get("date_fin", courant["date_fin"])
        if fin < debut:
            raise ValueError("date_fin ne peut pas précéder date_debut")
        relation = self._verifier_relation(courant["IDrelation_structure"])
        if relation.get("date_debut") and debut < relation["date_debut"]:
            raise ValueError("La programmation débute avant la relation")
        if relation.get("date_fin") and fin > relation["date_fin"]:
            raise ValueError("La programmation se termine après la relation")
        return self.db.ReqMAJ(
            "structures_programmations", _liste_pairs(valeurs, CHAMPS_PROGRAMMATION),
            "IDprogrammation_structure", int(IDprogrammation_structure)
        )

    def ListerCreneaux(self, IDprogrammation_structure, actifs_seulement=True, conserves_seulement=False):
        conditions = ["IDprogrammation_structure=%d" % int(IDprogrammation_structure)]
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

    def _verifier_groupe_et_lieu(self, programmation, IDgroupe_structure=None, IDlieu=None):
        relation = self._verifier_relation(programmation["IDrelation_structure"])
        if IDgroupe_structure:
            req = "SELECT IDstructure FROM structures_groupes WHERE IDgroupe_structure=%d AND actif=1;" % int(IDgroupe_structure)
            if self.db.ExecuterReq(req) != 1 or not (self.db.ResultatReq() or []):
                raise ValueError("Groupe introuvable ou archivé")
            if int(self.db.ResultatReq()[0][0]) != int(relation["IDstructure"]):
                raise ValueError("Le groupe n'appartient pas au bénéficiaire de la relation")
        if IDlieu:
            req = "SELECT IDlieu FROM lieux WHERE IDlieu=%d AND actif=1;" % int(IDlieu)
            if self.db.ExecuterReq(req) != 1 or not (self.db.ResultatReq() or []):
                raise ValueError("Lieu introuvable ou archivé")

    def CreerCreneau(self, IDprogrammation_structure, donnees, date=None):
        programmation = self._verifier_programmation_brouillon(IDprogrammation_structure)
        donnees = dict(donnees or {})
        donnees["IDprogrammation_structure"] = int(IDprogrammation_structure)
        valeurs = NormaliserCreneau(donnees, creation=True, date=date)
        if self._uid_existe("structures_programmations_creneaux", valeurs["uid"]):
            raise ValueError("UID de créneau déjà utilisé")
        self._verifier_groupe_et_lieu(
            programmation, valeurs.get("IDgroupe_structure"), valeurs.get("IDlieu")
        )
        debut = valeurs.get("date_debut") or programmation["date_debut"]
        fin = valeurs.get("date_fin") or programmation["date_fin"]
        if fin < debut or debut < programmation["date_debut"] or fin > programmation["date_fin"]:
            raise ValueError("La période du créneau doit rester dans la programmation")
        return self.db.ReqInsert(
            "structures_programmations_creneaux", _liste_pairs(valeurs, CHAMPS_CRENEAU)
        )

    def ModifierCreneau(self, IDcreneau_programmation, donnees, date=None):
        courant = self.LireCreneau(IDcreneau_programmation)
        if not courant:
            raise ValueError("Créneau introuvable")
        programmation = self._verifier_programmation_brouillon(courant["IDprogrammation_structure"])
        valeurs = NormaliserCreneau(donnees, creation=False, date=date)
        groupe = valeurs.get("IDgroupe_structure", courant.get("IDgroupe_structure"))
        lieu = valeurs.get("IDlieu", courant.get("IDlieu"))
        self._verifier_groupe_et_lieu(programmation, groupe, lieu)
        debut_h = valeurs.get("heure_debut", courant["heure_debut"])
        fin_h = valeurs.get("heure_fin", courant["heure_fin"])
        _duree_minutes(debut_h, fin_h)
        debut = valeurs.get("date_debut", courant.get("date_debut")) or programmation["date_debut"]
        fin = valeurs.get("date_fin", courant.get("date_fin")) or programmation["date_fin"]
        if fin < debut or debut < programmation["date_debut"] or fin > programmation["date_fin"]:
            raise ValueError("La période du créneau doit rester dans la programmation")
        if courant.get("IDcreneau_source") and courant.get("etat_renouvellement") == RENOUVELLEMENT_INCHANGE:
            valeurs["etat_renouvellement"] = RENOUVELLEMENT_MODIFIE
        return self.db.ReqMAJ(
            "structures_programmations_creneaux", _liste_pairs(valeurs, CHAMPS_CRENEAU),
            "IDcreneau_programmation", int(IDcreneau_programmation)
        )

    def SupprimerCreneau(self, IDcreneau_programmation, date=None):
        courant = self.LireCreneau(IDcreneau_programmation)
        if not courant:
            raise ValueError("Créneau introuvable")
        self._verifier_programmation_brouillon(courant["IDprogrammation_structure"])
        if courant.get("IDcreneau_source"):
            valeurs = {"etat_renouvellement": RENOUVELLEMENT_SUPPRIME, "date_modification": _maintenant(date)}
        else:
            valeurs = {"actif": 0, "date_modification": _maintenant(date)}
        return self.db.ReqMAJ(
            "structures_programmations_creneaux", _liste_pairs(valeurs, CHAMPS_CRENEAU),
            "IDcreneau_programmation", int(IDcreneau_programmation)
        )

    def ChangerStatut(self, IDprogrammation_structure, nouveau_statut, date=None):
        programmation = self.LireProgrammation(IDprogrammation_structure)
        if not programmation:
            raise ValueError("Programmation introuvable")
        nouveau_statut = _texte(nouveau_statut)
        transitions = {
            STATUT_BROUILLON: (STATUT_SOUMISE, STATUT_VALIDEE, STATUT_ANNULEE),
            STATUT_SOUMISE: (STATUT_BROUILLON, STATUT_VALIDEE, STATUT_ANNULEE),
            STATUT_VALIDEE: (STATUT_ANNULEE,),
            STATUT_ANNULEE: (),
        }
        if nouveau_statut == programmation["statut"]:
            return True
        if nouveau_statut not in transitions.get(programmation["statut"], ()):
            raise ValueError("Transition de statut interdite")
        if nouveau_statut == STATUT_VALIDEE and not self.ListerCreneaux(IDprogrammation_structure, conserves_seulement=True):
            raise ValueError("Une programmation sans créneau ne peut pas être validée")
        valeurs = {"statut": nouveau_statut, "date_modification": _maintenant(date)}
        return self.db.ReqMAJ(
            "structures_programmations", _liste_pairs(valeurs, CHAMPS_PROGRAMMATION),
            "IDprogrammation_structure", int(IDprogrammation_structure)
        )

    def RenouvelerProgrammation(self, IDprogrammation_source, IDrelation_structure, saison, date_debut, date_fin, date=None):
        source = self.LireProgrammation(IDprogrammation_source)
        if not source:
            raise ValueError("Programmation source introuvable")
        if source["statut"] != STATUT_VALIDEE:
            raise ValueError("Seule une programmation validée peut être renouvelée")
        nouvelle_id = self.CreerProgrammation(
            {
                "IDrelation_structure": IDrelation_structure,
                "IDprogrammation_source": IDprogrammation_source,
                "saison": saison,
                "date_debut": date_debut,
                "date_fin": date_fin,
                "notes": source.get("notes") or "",
            },
            date=date,
        )
        nouvelle = self.LireProgrammation(nouvelle_id)
        for ancien in self.ListerCreneaux(IDprogrammation_source, conserves_seulement=True):
            donnees = dict((champ, ancien.get(champ)) for champ in CHAMPS_CRENEAU)
            for champ in ("uid", "IDprogrammation_structure", "date_creation", "date_modification"):
                donnees.pop(champ, None)
            donnees["IDcreneau_source"] = ancien["IDcreneau_programmation"]
            donnees["etat_renouvellement"] = RENOUVELLEMENT_INCHANGE
            if ancien.get("date_debut"):
                donnees["date_debut"] = nouvelle["date_debut"]
            if ancien.get("date_fin"):
                donnees["date_fin"] = nouvelle["date_fin"]
            self.CreerCreneau(nouvelle_id, donnees, date=date)
        return nouvelle_id

    def _parametres_recurrence(self, programmation, creneau):
        debut = max(_date_obj(programmation["date_debut"], "date_debut"), _date_obj(creneau["date_debut"], "date_debut") if creneau.get("date_debut") else _date_obj(programmation["date_debut"], "date_debut"))
        fin = min(_date_obj(programmation["date_fin"], "date_fin"), _date_obj(creneau["date_fin"], "date_fin") if creneau.get("date_fin") else _date_obj(programmation["date_fin"], "date_fin"))
        if fin < debut:
            return None
        jour = int(creneau["jour_semaine"])
        return {
            "date_debut": debut,
            "date_fin": fin,
            "heure_debut": creneau["heure_debut"],
            "heure_fin": creneau["heure_fin"],
            "jours_vacances": [jour] if creneau.get("appliquer_vacances") else [],
            "jours_scolaires": [jour] if creneau.get("appliquer_scolaire") else [],
            "semaines": int(creneau["frequence"]),
            "feries": bool(creneau.get("inclure_feries")),
        }

    def GenererApercuOccurrences(self, IDprogrammation_structure, calculateur_occurrences):
        if not callable(calculateur_occurrences):
            raise TypeError("calculateur_occurrences doit être appelable")
        programmation = self.LireProgrammation(IDprogrammation_structure)
        if not programmation:
            raise ValueError("Programmation introuvable")
        if programmation["statut"] == STATUT_ANNULEE:
            raise ValueError("Une programmation annulée ne produit pas d'occurrences")
        relation = self._verifier_relation(programmation["IDrelation_structure"])
        occurrences = []
        deja = set()
        for creneau in self.ListerCreneaux(IDprogrammation_structure, conserves_seulement=True):
            params = self._parametres_recurrence(programmation, creneau)
            if params is None:
                continue
            for donnee in calculateur_occurrences(dict(params)) or ():
                debut = donnee.get("date_debut")
                fin = donnee.get("date_fin")
                if not isinstance(debut, datetime.datetime) or not isinstance(fin, datetime.datetime):
                    raise ValueError("Le calculateur historique doit retourner des datetime")
                if fin <= debut:
                    raise ValueError("Occurrence historique de durée invalide")
                signature = "%s|%s|%s" % (creneau["uid"], debut.isoformat(), fin.isoformat())
                uid = "OCC-%s" % hashlib.sha256(signature.encode("utf-8")).hexdigest()[:40]
                if uid in deja:
                    continue
                deja.add(uid)
                occurrences.append({
                    "uid": uid,
                    "IDprogrammation_structure": programmation["IDprogrammation_structure"],
                    "uid_programmation": programmation["uid"],
                    "IDcreneau_programmation": creneau["IDcreneau_programmation"],
                    "uid_creneau": creneau["uid"],
                    "IDrelation_structure": programmation["IDrelation_structure"],
                    "uid_relation": relation["uid"],
                    "IDstructure": relation["IDstructure"],
                    "IDgroupe_structure": creneau.get("IDgroupe_structure"),
                    "IDlieu": creneau.get("IDlieu"),
                    "nature": creneau["nature"],
                    "libelle": creneau["libelle"],
                    "date": debut.date().isoformat(),
                    "heure_debut": debut.strftime("%H:%M"),
                    "heure_fin": fin.strftime("%H:%M"),
                    "duree_minutes": int((fin - debut).total_seconds() // 60),
                    "observations": creneau.get("observations") or "",
                })
        return sorted(occurrences, key=lambda x: (x["date"], x["heure_debut"], x["uid"]))

    def ConstruireAnnexePrevisionnelle(self, IDprogrammation_structure, calculateur_occurrences):
        programmation = self.LireProgrammation(IDprogrammation_structure)
        if not programmation:
            raise ValueError("Programmation introuvable")
        occurrences = self.GenererApercuOccurrences(IDprogrammation_structure, calculateur_occurrences)
        lignes = []
        for index, occurrence in enumerate(occurrences, 1):
            date_obj = _date_obj(occurrence["date"], "date")
            lignes.append({
                "numero": index,
                "uid": occurrence["uid"],
                "date": occurrence["date"],
                "jour": JOURS[date_obj.weekday()],
                "heure_debut": occurrence["heure_debut"],
                "heure_fin": occurrence["heure_fin"],
                "duree_minutes": occurrence["duree_minutes"],
                "IDgroupe_structure": occurrence["IDgroupe_structure"],
                "IDlieu": occurrence["IDlieu"],
                "libelle": occurrence["libelle"],
            })
        total = sum(ligne["duree_minutes"] for ligne in lignes)
        return {
            "uid_programmation": programmation["uid"],
            "saison": programmation["saison"],
            "date_debut": programmation["date_debut"],
            "date_fin": programmation["date_fin"],
            "nb_seances": len(lignes),
            "duree_totale_minutes": total,
            "lignes": lignes,
        }
