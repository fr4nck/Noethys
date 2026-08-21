#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Licence :        GNU GPL
#------------------------------------------------------------------------

"""Programmation annuelle pure des mises à disposition.

Ce module décrit les créneaux contractuels et leur renouvellement N-1. Il ne
calcule volontairement aucune occurrence datée : vacances, jours fériés et
récurrences restent du ressort du moteur calendrier historique de Noethys.
"""

import datetime
import uuid


STATUT_PROGRAMMATION_BROUILLON = "brouillon"
STATUT_PROGRAMMATION_SOUMISE = "soumise"
STATUT_PROGRAMMATION_VALIDEE = "validee"
STATUT_PROGRAMMATION_ANNULEE = "annulee"

STATUTS_PROGRAMMATION = (
    STATUT_PROGRAMMATION_BROUILLON,
    STATUT_PROGRAMMATION_SOUMISE,
    STATUT_PROGRAMMATION_VALIDEE,
    STATUT_PROGRAMMATION_ANNULEE,
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

JOURS_SEMAINE = (
    "lundi",
    "mardi",
    "mercredi",
    "jeudi",
    "vendredi",
    "samedi",
    "dimanche",
)


def _GetUUID(valeur, nom_champ, obligatoire=True):
    if valeur in (None, ""):
        if obligatoire:
            return str(uuid.uuid4())
        return None
    try:
        return str(uuid.UUID(str(valeur)))
    except (ValueError, AttributeError, TypeError):
        raise ValueError("%s doit être un UUID valide" % nom_champ)


def _GetDate(valeur, nom_champ):
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


def _GetHeure(valeur, nom_champ):
    if isinstance(valeur, datetime.datetime):
        return valeur.time().replace(second=0, microsecond=0)
    if isinstance(valeur, datetime.time):
        return valeur.replace(second=0, microsecond=0)
    if isinstance(valeur, str):
        for format_heure in ("%H:%M", "%Hh%M"):
            try:
                return datetime.datetime.strptime(valeur, format_heure).time()
            except ValueError:
                pass
    raise ValueError("%s doit être une heure HH:MM" % nom_champ)


def _FormatDate(valeur):
    return valeur.isoformat() if valeur else None


def _FormatHeure(valeur):
    return valeur.strftime("%H:%M")


class CreneauProgrammation(object):
    """Créneau hebdomadaire canonique d'une programmation annuelle."""

    CHAMPS_MODIFIABLES = (
        "jour_semaine",
        "heure_debut",
        "heure_fin",
        "date_debut",
        "date_fin",
        "groupe",
        "lieu",
        "observations",
    )

    def __init__(
        self,
        identifiant_relation,
        jour_semaine,
        heure_debut,
        heure_fin,
        date_debut=None,
        date_fin=None,
        groupe="",
        lieu="",
        observations="",
        identifiant_stable=None,
        identifiant_source=None,
        etat_renouvellement=RENOUVELLEMENT_AJOUTE,
    ):
        self.identifiant_relation = _GetUUID(
            identifiant_relation, "identifiant_relation", obligatoire=True
        )
        self.identifiant_stable = _GetUUID(
            identifiant_stable, "identifiant_stable", obligatoire=True
        )
        self.identifiant_source = _GetUUID(
            identifiant_source, "identifiant_source", obligatoire=False
        )
        try:
            self.jour_semaine = int(jour_semaine)
        except (TypeError, ValueError):
            raise ValueError("jour_semaine doit être compris entre 0 et 6")
        self.heure_debut = _GetHeure(heure_debut, "heure_debut")
        self.heure_fin = _GetHeure(heure_fin, "heure_fin")
        self.date_debut = _GetDate(date_debut, "date_debut")
        self.date_fin = _GetDate(date_fin, "date_fin")
        self.groupe = (groupe or "").strip()
        self.lieu = (lieu or "").strip()
        self.observations = (observations or "").strip()
        self.etat_renouvellement = etat_renouvellement
        self.Validation()

    def Validation(self):
        if self.jour_semaine < 0 or self.jour_semaine > 6:
            raise ValueError("jour_semaine doit être compris entre 0 et 6")
        if self.heure_fin <= self.heure_debut:
            raise ValueError("heure_fin doit être postérieure à heure_debut")
        if self.date_debut and self.date_fin and self.date_fin < self.date_debut:
            raise ValueError("date_fin ne peut pas précéder date_debut")
        if self.identifiant_source == self.identifiant_stable:
            raise ValueError("un créneau ne peut pas être sa propre source")
        if self.etat_renouvellement not in ETATS_RENOUVELLEMENT:
            raise ValueError(
                "état de renouvellement inconnu : %s" % self.etat_renouvellement
            )
        if (
            self.etat_renouvellement
            in (RENOUVELLEMENT_INCHANGE, RENOUVELLEMENT_MODIFIE, RENOUVELLEMENT_SUPPRIME)
            and self.identifiant_source is None
        ):
            raise ValueError(
                "un créneau renouvelé doit conserver l'identifiant de sa source"
            )
        return True

    def DureePrevueMinutes(self):
        debut = datetime.datetime.combine(datetime.date.today(), self.heure_debut)
        fin = datetime.datetime.combine(datetime.date.today(), self.heure_fin)
        return int((fin - debut).total_seconds() // 60)

    def EstConserve(self):
        return self.etat_renouvellement != RENOUVELLEMENT_SUPPRIME

    def Renouveler(self, identifiant_relation, date_debut=None, date_fin=None):
        """Copie un créneau vers une nouvelle relation en conservant sa filiation.

        Les dates ne sont jamais transposées implicitement d'une année à l'autre :
        l'appelant fournit la nouvelle période si le créneau en a une.
        """
        return CreneauProgrammation(
            identifiant_relation=identifiant_relation,
            jour_semaine=self.jour_semaine,
            heure_debut=self.heure_debut,
            heure_fin=self.heure_fin,
            date_debut=date_debut,
            date_fin=date_fin,
            groupe=self.groupe,
            lieu=self.lieu,
            observations=self.observations,
            identifiant_source=self.identifiant_stable,
            etat_renouvellement=RENOUVELLEMENT_INCHANGE,
        )

    def AvecModifications(self, **modifications):
        inconnus = set(modifications) - set(self.CHAMPS_MODIFIABLES)
        if inconnus:
            raise ValueError(
                "champ(s) de créneau non modifiable(s) : %s"
                % ", ".join(sorted(inconnus))
            )

        donnees = self.GetDonnees()
        for cle, valeur in modifications.items():
            donnees[cle] = valeur

        if self.identifiant_source is not None:
            donnees["etat_renouvellement"] = RENOUVELLEMENT_MODIFIE
        else:
            donnees["etat_renouvellement"] = RENOUVELLEMENT_AJOUTE

        return CreneauProgrammation(**donnees)

    def MarquerSupprime(self):
        if self.identifiant_source is None:
            raise ValueError(
                "un créneau ajouté dans la saison doit être retiré, pas marqué supprimé"
            )
        donnees = self.GetDonnees()
        donnees["etat_renouvellement"] = RENOUVELLEMENT_SUPPRIME
        return CreneauProgrammation(**donnees)

    def GetChampsFusion(self, prefixe="CRENEAU"):
        prefixe = (prefixe or "CRENEAU").strip().upper()
        return {
            "{%s_ID_STABLE}" % prefixe: self.identifiant_stable,
            "{%s_SOURCE_ID_STABLE}" % prefixe: self.identifiant_source or "",
            "{%s_RELATION_ID_STABLE}" % prefixe: self.identifiant_relation,
            "{%s_JOUR}" % prefixe: JOURS_SEMAINE[self.jour_semaine],
            "{%s_JOUR_INDEX}" % prefixe: str(self.jour_semaine),
            "{%s_HEURE_DEBUT}" % prefixe: _FormatHeure(self.heure_debut),
            "{%s_HEURE_FIN}" % prefixe: _FormatHeure(self.heure_fin),
            "{%s_DUREE_MINUTES}" % prefixe: str(self.DureePrevueMinutes()),
            "{%s_DATE_DEBUT}" % prefixe: _FormatDate(self.date_debut) or "",
            "{%s_DATE_FIN}" % prefixe: _FormatDate(self.date_fin) or "",
            "{%s_GROUPE}" % prefixe: self.groupe,
            "{%s_LIEU}" % prefixe: self.lieu,
            "{%s_OBSERVATIONS}" % prefixe: self.observations,
            "{%s_RENOUVELLEMENT}" % prefixe: self.etat_renouvellement,
        }

    def GetDonnees(self):
        return {
            "identifiant_relation": self.identifiant_relation,
            "jour_semaine": self.jour_semaine,
            "heure_debut": _FormatHeure(self.heure_debut),
            "heure_fin": _FormatHeure(self.heure_fin),
            "date_debut": _FormatDate(self.date_debut),
            "date_fin": _FormatDate(self.date_fin),
            "groupe": self.groupe,
            "lieu": self.lieu,
            "observations": self.observations,
            "identifiant_stable": self.identifiant_stable,
            "identifiant_source": self.identifiant_source,
            "etat_renouvellement": self.etat_renouvellement,
        }


class ProgrammationAnnuelle(object):
    """Ensemble cohérent de créneaux rattachés à une relation contractuelle."""

    def __init__(
        self,
        identifiant_relation,
        saison,
        statut=STATUT_PROGRAMMATION_BROUILLON,
        creneaux=None,
        identifiant_stable=None,
        identifiant_source=None,
    ):
        self.identifiant_relation = _GetUUID(
            identifiant_relation, "identifiant_relation", obligatoire=True
        )
        self.identifiant_stable = _GetUUID(
            identifiant_stable, "identifiant_stable", obligatoire=True
        )
        self.identifiant_source = _GetUUID(
            identifiant_source, "identifiant_source", obligatoire=False
        )
        self.saison = (saison or "").strip()
        self.statut = statut
        self.creneaux = []
        self.Validation()
        for creneau in creneaux or ():
            self.AjouterCreneau(creneau)

    def Validation(self):
        if not self.saison:
            raise ValueError("saison obligatoire")
        if self.statut not in STATUTS_PROGRAMMATION:
            raise ValueError("statut de programmation inconnu : %s" % self.statut)
        if self.identifiant_source == self.identifiant_stable:
            raise ValueError("une programmation ne peut pas être sa propre source")
        return True

    def AjouterCreneau(self, creneau):
        if not isinstance(creneau, CreneauProgrammation):
            raise TypeError("creneau doit être un CreneauProgrammation")
        if creneau.identifiant_relation != self.identifiant_relation:
            raise ValueError("le créneau appartient à une autre relation")
        if any(
            existant.identifiant_stable == creneau.identifiant_stable
            for existant in self.creneaux
        ):
            raise ValueError("identifiant de créneau déjà présent")
        self.creneaux.append(creneau)
        return creneau

    def GetCreneau(self, identifiant_stable):
        identifiant_stable = _GetUUID(
            identifiant_stable, "identifiant_stable", obligatoire=True
        )
        for creneau in self.creneaux:
            if creneau.identifiant_stable == identifiant_stable:
                return creneau
        raise KeyError(identifiant_stable)

    def ModifierCreneau(self, identifiant_stable, **modifications):
        creneau = self.GetCreneau(identifiant_stable)
        nouveau = creneau.AvecModifications(**modifications)
        index = self.creneaux.index(creneau)
        self.creneaux[index] = nouveau
        return nouveau

    def SupprimerCreneau(self, identifiant_stable):
        creneau = self.GetCreneau(identifiant_stable)
        index = self.creneaux.index(creneau)
        if creneau.identifiant_source is None:
            del self.creneaux[index]
            return None
        supprime = creneau.MarquerSupprime()
        self.creneaux[index] = supprime
        return supprime

    def GetCreneauxConserves(self):
        return [creneau for creneau in self.creneaux if creneau.EstConserve()]

    def GetSyntheseRenouvellement(self):
        synthese = dict((etat, 0) for etat in ETATS_RENOUVELLEMENT)
        for creneau in self.creneaux:
            synthese[creneau.etat_renouvellement] += 1
        return synthese

    def Renouveler(
        self,
        identifiant_relation,
        saison,
        date_debut=None,
        date_fin=None,
    ):
        """Crée une nouvelle programmation depuis les lignes conservées de N-1."""
        nouvelle = ProgrammationAnnuelle(
            identifiant_relation=identifiant_relation,
            saison=saison,
            statut=STATUT_PROGRAMMATION_BROUILLON,
            identifiant_source=self.identifiant_stable,
        )
        for creneau in self.GetCreneauxConserves():
            nouvelle.AjouterCreneau(
                creneau.Renouveler(
                    identifiant_relation=identifiant_relation,
                    date_debut=date_debut,
                    date_fin=date_fin,
                )
            )
        return nouvelle

    def GetChampsFusion(self):
        synthese = self.GetSyntheseRenouvellement()
        return {
            "{PROGRAMMATION_ID_STABLE}": self.identifiant_stable,
            "{PROGRAMMATION_SOURCE_ID_STABLE}": self.identifiant_source or "",
            "{PROGRAMMATION_RELATION_ID_STABLE}": self.identifiant_relation,
            "{PROGRAMMATION_SAISON}": self.saison,
            "{PROGRAMMATION_STATUT}": self.statut,
            "{PROGRAMMATION_NB_CRENEAUX}": str(len(self.GetCreneauxConserves())),
            "{PROGRAMMATION_NB_INCHANGES}": str(synthese[RENOUVELLEMENT_INCHANGE]),
            "{PROGRAMMATION_NB_MODIFIES}": str(synthese[RENOUVELLEMENT_MODIFIE]),
            "{PROGRAMMATION_NB_SUPPRIMES}": str(synthese[RENOUVELLEMENT_SUPPRIME]),
            "{PROGRAMMATION_NB_AJOUTES}": str(synthese[RENOUVELLEMENT_AJOUTE]),
        }

    def GetDonnees(self):
        return {
            "identifiant_relation": self.identifiant_relation,
            "saison": self.saison,
            "statut": self.statut,
            "identifiant_stable": self.identifiant_stable,
            "identifiant_source": self.identifiant_source,
            "creneaux": [creneau.GetDonnees() for creneau in self.creneaux],
        }
