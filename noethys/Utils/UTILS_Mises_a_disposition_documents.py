#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Licence :         GNU GPL
#------------------------------------------------------------------------

"""Adaptation documentaire des mises à disposition.

Le module reste volontairement sans wxPython, GestionDB ni moteur PDF.
Il transforme la programmation canonique en contrat d'appel compatible avec
le calculateur de récurrence historique de Noethys, puis prépare les champs
et lignes nécessaires aux modèles documentaires existants.

Le calcul des vacances, jours fériés et fréquences n'est jamais réimplémenté
ici : il est fourni par ``calculateur_occurences``.
"""

import copy
import datetime
import hashlib
import json
import uuid
from decimal import Decimal


DOCUMENT_CONVENTION = "convention"
DOCUMENT_AVENANT = "avenant"
DOCUMENT_ANNEXE = "annexe"

TYPES_DOCUMENT = (
    DOCUMENT_CONVENTION,
    DOCUMENT_AVENANT,
    DOCUMENT_ANNEXE,
)

FREQUENCE_TOUTES_LES_SEMAINES = 1
FREQUENCE_UNE_SUR_DEUX = 2
FREQUENCE_UNE_SUR_TROIS = 3
FREQUENCE_UNE_SUR_QUATRE = 4
FREQUENCE_SEMAINES_PAIRES = 5
FREQUENCE_SEMAINES_IMPAIRES = 6

JOURS_SEMAINE_FR = (
    "lundi",
    "mardi",
    "mercredi",
    "jeudi",
    "vendredi",
    "samedi",
    "dimanche",
)

UUID_NAMESPACE_MAD = uuid.UUID("4b8744bd-e1a2-46a9-a4db-c68c72fd92d3")

FREQUENCES_HISTORIQUES = (
    FREQUENCE_TOUTES_LES_SEMAINES,
    FREQUENCE_UNE_SUR_DEUX,
    FREQUENCE_UNE_SUR_TROIS,
    FREQUENCE_UNE_SUR_QUATRE,
    FREQUENCE_SEMAINES_PAIRES,
    FREQUENCE_SEMAINES_IMPAIRES,
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


def _GetDatetime(valeur, nom_champ):
    if isinstance(valeur, datetime.datetime):
        return valeur.replace(second=0, microsecond=0)
    if isinstance(valeur, str):
        for format_dt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                return datetime.datetime.strptime(valeur, format_dt)
            except ValueError:
                pass
    raise ValueError("%s doit être un datetime ou une chaîne ISO" % nom_champ)


def _FormatDateFr(valeur):
    return valeur.strftime("%d/%m/%Y") if valeur else ""


def _FormatHeure(valeur):
    return valeur.strftime("%H:%M")


def _FormatDureeMinutes(minutes):
    heures = int(minutes) // 60
    reste = int(minutes) % 60
    if reste == 0:
        return "%dh" % heures
    return "%dh%02d" % (heures, reste)


def _SerialiserValeur(valeur):
    if isinstance(valeur, datetime.datetime):
        return valeur.isoformat()
    if isinstance(valeur, datetime.date):
        return valeur.isoformat()
    if isinstance(valeur, Decimal):
        return format(valeur, "f")
    if isinstance(valeur, tuple):
        return [_SerialiserValeur(item) for item in valeur]
    if isinstance(valeur, list):
        return [_SerialiserValeur(item) for item in valeur]
    if isinstance(valeur, dict):
        return dict(
            (str(cle), _SerialiserValeur(item))
            for cle, item in valeur.items()
        )
    return valeur


class RegleCalendrierMiseADisposition(object):
    """Paramètres contractuels traduits vers le moteur de récurrence historique."""

    def __init__(
        self,
        appliquer_scolaire=True,
        appliquer_vacances=False,
        inclure_feries=False,
        frequence=FREQUENCE_TOUTES_LES_SEMAINES,
    ):
        self.appliquer_scolaire = bool(appliquer_scolaire)
        self.appliquer_vacances = bool(appliquer_vacances)
        self.inclure_feries = bool(inclure_feries)
        try:
            self.frequence = int(frequence)
        except (TypeError, ValueError):
            raise ValueError("fréquence historique invalide")
        self.Validation()

    def Validation(self):
        if self.frequence not in FREQUENCES_HISTORIQUES:
            raise ValueError("fréquence historique inconnue : %s" % self.frequence)
        if not self.appliquer_scolaire and not self.appliquer_vacances:
            raise ValueError(
                "la règle doit s'appliquer au scolaire, aux vacances ou aux deux"
            )
        return True

    def GetParametresRecurrence(self, creneau, date_debut, date_fin):
        date_debut = _GetDate(date_debut, "date_debut")
        date_fin = _GetDate(date_fin, "date_fin")
        if date_debut is None or date_fin is None:
            raise ValueError("la période de génération est obligatoire")
        if date_fin < date_debut:
            raise ValueError("date_fin ne peut pas précéder date_debut")
        if getattr(creneau, "date_debut", None):
            date_debut = max(date_debut, creneau.date_debut)
        if getattr(creneau, "date_fin", None):
            date_fin = min(date_fin, creneau.date_fin)
        if date_fin < date_debut:
            return None

        jour = int(creneau.jour_semaine)
        return {
            "date_debut": date_debut,
            "date_fin": date_fin,
            "heure_debut": _FormatHeure(creneau.heure_debut),
            "heure_fin": _FormatHeure(creneau.heure_fin),
            "jours_vacances": [jour] if self.appliquer_vacances else [],
            "jours_scolaires": [jour] if self.appliquer_scolaire else [],
            "semaines": self.frequence,
            "feries": self.inclure_feries,
        }

    def GetDonnees(self):
        return {
            "appliquer_scolaire": self.appliquer_scolaire,
            "appliquer_vacances": self.appliquer_vacances,
            "inclure_feries": self.inclure_feries,
            "frequence": self.frequence,
        }


class OccurrenceMiseADisposition(object):
    """Occurrence datée destinée à l'annexe et au futur réalisé."""

    def __init__(
        self,
        creneau,
        date_debut,
        date_fin,
        identifiant_stable=None,
    ):
        self.identifiant_creneau = _GetUUID(
            creneau.identifiant_stable, "identifiant_creneau", obligatoire=True
        )
        self.identifiant_relation = _GetUUID(
            creneau.identifiant_relation, "identifiant_relation", obligatoire=True
        )
        self.date_debut = _GetDatetime(date_debut, "date_debut")
        self.date_fin = _GetDatetime(date_fin, "date_fin")
        if identifiant_stable in (None, ""):
            identifiant_stable = str(
                uuid.uuid5(
                    UUID_NAMESPACE_MAD,
                    "%s|%s|%s"
                    % (
                        self.identifiant_creneau,
                        self.date_debut.isoformat(),
                        self.date_fin.isoformat(),
                    ),
                )
            )
        self.identifiant_stable = _GetUUID(
            identifiant_stable, "identifiant_stable", obligatoire=True
        )
        self.groupe = (getattr(creneau, "groupe", "") or "").strip()
        self.lieu = (getattr(creneau, "lieu", "") or "").strip()
        self.observations = (getattr(creneau, "observations", "") or "").strip()
        self.Validation()

    def Validation(self):
        if self.date_fin <= self.date_debut:
            raise ValueError("date_fin doit être postérieure à date_debut")
        return True

    def DureeMinutes(self):
        return int((self.date_fin - self.date_debut).total_seconds() // 60)

    def GetLigneAnnexe(self, index=None):
        ligne = {
            "identifiant_stable": self.identifiant_stable,
            "identifiant_creneau": self.identifiant_creneau,
            "date": _FormatDateFr(self.date_debut.date()),
            "jour": JOURS_SEMAINE_FR[self.date_debut.weekday()],
            "heure_debut": _FormatHeure(self.date_debut.time()),
            "heure_fin": _FormatHeure(self.date_fin.time()),
            "duree_minutes": self.DureeMinutes(),
            "duree": _FormatDureeMinutes(self.DureeMinutes()),
            "groupe": self.groupe,
            "lieu": self.lieu,
            "observations": self.observations,
        }
        if index is not None:
            ligne["numero"] = int(index)
        return ligne

    def GetDonnees(self):
        return {
            "identifiant_stable": self.identifiant_stable,
            "identifiant_creneau": self.identifiant_creneau,
            "identifiant_relation": self.identifiant_relation,
            "date_debut": self.date_debut.isoformat(),
            "date_fin": self.date_fin.isoformat(),
            "groupe": self.groupe,
            "lieu": self.lieu,
            "observations": self.observations,
        }


class AnnexePrevisionnelleMiseADisposition(object):
    """Liste canonique date par date issue d'une programmation annuelle."""

    def __init__(
        self,
        identifiant_programmation,
        identifiant_relation,
        date_debut,
        date_fin,
        occurrences=None,
        identifiant_stable=None,
    ):
        self.identifiant_programmation = _GetUUID(
            identifiant_programmation, "identifiant_programmation", obligatoire=True
        )
        self.identifiant_relation = _GetUUID(
            identifiant_relation, "identifiant_relation", obligatoire=True
        )
        self.date_debut = _GetDate(date_debut, "date_debut")
        self.date_fin = _GetDate(date_fin, "date_fin")
        if identifiant_stable in (None, ""):
            identifiant_stable = str(
                uuid.uuid5(
                    UUID_NAMESPACE_MAD,
                    "%s|%s|%s"
                    % (
                        self.identifiant_programmation,
                        self.date_debut.isoformat() if self.date_debut else "",
                        self.date_fin.isoformat() if self.date_fin else "",
                    ),
                )
            )
        self.identifiant_stable = _GetUUID(
            identifiant_stable, "identifiant_stable", obligatoire=True
        )
        self.occurrences = list(occurrences or ())
        self.Validation()

    def Validation(self):
        if self.date_debut is None or self.date_fin is None:
            raise ValueError("la période d'annexe est obligatoire")
        if self.date_fin < self.date_debut:
            raise ValueError("date_fin ne peut pas précéder date_debut")
        for occurrence in self.occurrences:
            if occurrence.identifiant_relation != self.identifiant_relation:
                raise ValueError("une occurrence appartient à une autre relation")
        return True

    def GetOccurrencesTriees(self):
        return sorted(
            self.occurrences,
            key=lambda item: (
                item.date_debut,
                item.date_fin,
                item.identifiant_creneau,
            ),
        )

    def GetLignes(self):
        return [
            occurrence.GetLigneAnnexe(index + 1)
            for index, occurrence in enumerate(self.GetOccurrencesTriees())
        ]

    def DureeTotaleMinutes(self):
        return sum(
            occurrence.DureeMinutes()
            for occurrence in self.GetOccurrencesTriees()
        )

    def GetTexteLignes(self):
        lignes = []
        for ligne in self.GetLignes():
            morceaux = [
                "%s %s-%s" % (
                    ligne["date"],
                    ligne["heure_debut"],
                    ligne["heure_fin"],
                )
            ]
            if ligne["groupe"]:
                morceaux.append(ligne["groupe"])
            if ligne["lieu"]:
                morceaux.append(ligne["lieu"])
            lignes.append(" | ".join(morceaux))
        return "\n".join(lignes)

    def GetChampsFusion(self):
        duree_minutes = self.DureeTotaleMinutes()
        return {
            "{ANNEXE_ID_STABLE}": self.identifiant_stable,
            "{ANNEXE_PROGRAMMATION_ID_STABLE}": self.identifiant_programmation,
            "{ANNEXE_RELATION_ID_STABLE}": self.identifiant_relation,
            "{ANNEXE_DATE_DEBUT}": _FormatDateFr(self.date_debut),
            "{ANNEXE_DATE_FIN}": _FormatDateFr(self.date_fin),
            "{ANNEXE_NB_SEANCES}": str(len(self.occurrences)),
            "{ANNEXE_DUREE_TOTALE_MINUTES}": str(duree_minutes),
            "{ANNEXE_DUREE_TOTALE}": _FormatDureeMinutes(duree_minutes),
            "{ANNEXE_LIGNES_TEXTE}": self.GetTexteLignes(),
        }

    def GetDonnees(self):
        return {
            "identifiant_stable": self.identifiant_stable,
            "identifiant_programmation": self.identifiant_programmation,
            "identifiant_relation": self.identifiant_relation,
            "date_debut": self.date_debut.isoformat(),
            "date_fin": self.date_fin.isoformat(),
            "occurrences": [
                occurrence.GetDonnees()
                for occurrence in self.GetOccurrencesTriees()
            ],
        }


def GenererAnnexeDepuisProgrammation(
    programmation,
    date_debut,
    date_fin,
    calculateur_occurences,
    regles_par_creneau=None,
    regle_defaut=None,
):
    """Génère l'annexe via le calculateur historique injecté.

    ``calculateur_occurences`` doit accepter exactement le dictionnaire utilisé
    par ``DLG_Saisie_location.Calcule_occurences`` et retourner des dictionnaires
    ``date_debut`` / ``date_fin``.
    """
    if not callable(calculateur_occurences):
        raise TypeError("calculateur_occurences doit être appelable")

    date_debut = _GetDate(date_debut, "date_debut")
    date_fin = _GetDate(date_fin, "date_fin")
    if date_debut is None or date_fin is None:
        raise ValueError("la période de génération est obligatoire")
    if date_fin < date_debut:
        raise ValueError("date_fin ne peut pas précéder date_debut")

    regles_par_creneau = regles_par_creneau or {}
    if regle_defaut is None:
        regle_defaut = RegleCalendrierMiseADisposition()

    occurrences = []
    deja_vues = set()
    for creneau in programmation.GetCreneauxConserves():
        regle = regles_par_creneau.get(creneau.identifiant_stable, regle_defaut)
        if not isinstance(regle, RegleCalendrierMiseADisposition):
            raise TypeError("règle calendrier invalide pour le créneau")
        parametres = regle.GetParametresRecurrence(
            creneau, date_debut, date_fin
        )
        if parametres is None:
            continue

        for donnee in calculateur_occurences(parametres) or ():
            occurrence = OccurrenceMiseADisposition(
                creneau=creneau,
                date_debut=donnee["date_debut"],
                date_fin=donnee["date_fin"],
            )
            signature = (
                occurrence.identifiant_creneau,
                occurrence.date_debut,
                occurrence.date_fin,
            )
            if signature in deja_vues:
                continue
            deja_vues.add(signature)
            occurrences.append(occurrence)

    return AnnexePrevisionnelleMiseADisposition(
        identifiant_programmation=programmation.identifiant_stable,
        identifiant_relation=programmation.identifiant_relation,
        date_debut=date_debut,
        date_fin=date_fin,
        occurrences=occurrences,
    )


def _FusionnerChamps(cible, source):
    for cle, valeur in source.items():
        if cle in cible and cible[cle] != valeur:
            raise ValueError("collision de champ de fusion : %s" % cle)
        cible[cle] = valeur


def _ChampsContactVide(prefixe):
    prefixe = (prefixe or "CONTACT_CONVENTION").strip().upper()
    suffixes = (
        "ID_STABLE",
        "STRUCTURE_ID_STABLE",
        "NOM",
        "PRENOM",
        "NOM_COMPLET",
        "FONCTION",
        "MAIL",
        "TELEPHONE",
        "ROLES",
    )
    return dict(("{%s_%s}" % (prefixe, suffixe), "") for suffixe in suffixes)


class DossierDocumentaireMiseADisposition(object):
    """Paquet documentaire canonique consommable par les modèles Noethys."""

    def __init__(
        self,
        convention,
        relation,
        beneficiaire,
        payeur,
        programmation,
        annexe,
        contact_convention=None,
    ):
        self.convention = convention
        self.relation = relation
        self.beneficiaire = beneficiaire
        self.payeur = payeur
        self.programmation = programmation
        self.annexe = annexe
        self.contact_convention = contact_convention
        self.Validation()

    def Validation(self):
        relation_id = self.relation.identifiant_stable
        if self.convention.identifiant_relation not in (None, relation_id):
            raise ValueError("la convention appartient à une autre relation")
        if self.programmation.identifiant_relation != relation_id:
            raise ValueError("la programmation appartient à une autre relation")
        if self.annexe.identifiant_relation != relation_id:
            raise ValueError("l'annexe appartient à une autre relation")
        if self.annexe.identifiant_programmation != self.programmation.identifiant_stable:
            raise ValueError("l'annexe appartient à une autre programmation")
        if self.beneficiaire.identifiant_stable != self.relation.identifiant_beneficiaire:
            raise ValueError("le bénéficiaire ne correspond pas à la relation")
        if self.payeur.identifiant_stable != self.relation.identifiant_payeur:
            raise ValueError("le payeur ne correspond pas à la relation")
        if (
            self.contact_convention is not None
            and self.contact_convention.identifiant_structure
            not in (
                self.beneficiaire.identifiant_stable,
                self.payeur.identifiant_stable,
            )
        ):
            raise ValueError("le contact convention appartient à une autre structure")
        return True

    def GetTypeDocument(self):
        if self.convention.EstAvenant():
            return DOCUMENT_AVENANT
        return DOCUMENT_CONVENTION

    def GetChampsFusion(self):
        champs = {}
        _FusionnerChamps(champs, self.convention.GetChampsFusion())
        _FusionnerChamps(champs, self.relation.GetChampsFusion())
        _FusionnerChamps(champs, self.beneficiaire.GetChampsFusion("BENEFICIAIRE"))
        _FusionnerChamps(champs, self.payeur.GetChampsFusion("PAYEUR"))
        _FusionnerChamps(champs, self.programmation.GetChampsFusion())
        _FusionnerChamps(champs, self.annexe.GetChampsFusion())

        if self.contact_convention is None:
            _FusionnerChamps(champs, _ChampsContactVide("CONTACT_CONVENTION"))
        else:
            _FusionnerChamps(
                champs,
                self.contact_convention.GetChampsFusion("CONTACT_CONVENTION"),
            )

        type_document = self.GetTypeDocument()
        _FusionnerChamps(
            champs,
            {
                "{DOCUMENT_TYPE}": type_document,
                "{DOCUMENT_EST_AVENANT}": "1" if type_document == DOCUMENT_AVENANT else "0",
            },
        )
        return champs

    def GetPaquetModele(self):
        return {
            "type_document": self.GetTypeDocument(),
            "champs": self.GetChampsFusion(),
            "lignes_annexe": self.annexe.GetLignes(),
        }

    def Figer(self, date_generation=None, identifiant_stable=None):
        return SnapshotDocumentContractuel(
            type_document=self.GetTypeDocument(),
            identifiant_convention=self.convention.identifiant_stable,
            paquet_modele=self.GetPaquetModele(),
            date_generation=date_generation,
            identifiant_stable=identifiant_stable,
        )


class SnapshotDocumentContractuel(object):
    """Instantané auditable d'un document validé.

    Le stockage futur devra créer un nouvel instantané au lieu de modifier un
    instantané déjà figé. Le hash permet de vérifier qu'un document officiel
    n'a pas été recalculé silencieusement après validation.
    """

    def __init__(
        self,
        type_document,
        identifiant_convention,
        paquet_modele,
        date_generation=None,
        identifiant_stable=None,
    ):
        if type_document not in TYPES_DOCUMENT:
            raise ValueError("type de document inconnu : %s" % type_document)
        self.identifiant_stable = _GetUUID(
            identifiant_stable, "identifiant_stable", obligatoire=True
        )
        self.identifiant_convention = _GetUUID(
            identifiant_convention, "identifiant_convention", obligatoire=True
        )
        self.type_document = type_document
        if date_generation is None:
            date_generation = datetime.datetime.now()
        self.date_generation = _GetDatetime(date_generation, "date_generation")
        self.paquet_modele = copy.deepcopy(_SerialiserValeur(paquet_modele))
        self.empreinte = self._CalculerEmpreinte()

    def _CalculerEmpreinte(self):
        contenu = json.dumps(
            self.paquet_modele,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(contenu).hexdigest()

    def VerifierIntegrite(self):
        return self.empreinte == self._CalculerEmpreinte()

    def GetDonnees(self):
        return {
            "identifiant_stable": self.identifiant_stable,
            "identifiant_convention": self.identifiant_convention,
            "type_document": self.type_document,
            "date_generation": self.date_generation.isoformat(),
            "empreinte_sha256": self.empreinte,
            "paquet_modele": copy.deepcopy(self.paquet_modele),
        }
