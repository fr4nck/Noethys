#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Licence :        GNU GPL
#------------------------------------------------------------------------

"""Règles métier pures pour les conventions de mise à disposition.

Ce module ne dépend volontairement ni de wxPython ni de GestionDB. Il sert de
noyau commun aux écrans, aux éditions de conventions/avenants, au reporting et
aux futurs échanges avec PMSL-Équipe.
"""

import datetime
import uuid


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

FACTURATION_MANUELLE = "manuelle"
FACTURATION_MENSUELLE = "mensuelle"
FACTURATION_TRIMESTRIELLE = "trimestrielle"
FACTURATION_APRES_REALISE = "apres_realise"

MODES_FACTURATION = (
    FACTURATION_MANUELLE,
    FACTURATION_MENSUELLE,
    FACTURATION_TRIMESTRIELLE,
    FACTURATION_APRES_REALISE,
)


def _GetDate(valeur, nom_champ):
    """Retourne une date à partir d'une date, datetime ou chaîne ISO."""
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


def _GetUUID(valeur, nom_champ, obligatoire=True):
    """Normalise un identifiant stable UUID sous forme de chaîne."""
    if valeur in (None, ""):
        if obligatoire:
            return str(uuid.uuid4())
        return None
    try:
        return str(uuid.UUID(str(valeur)))
    except (ValueError, AttributeError, TypeError):
        raise ValueError("%s doit être un UUID valide" % nom_champ)


def _FormatDate(valeur):
    if valeur is None:
        return ""
    return valeur.strftime("%d/%m/%Y")


class ConventionMiseADisposition(object):
    """Représentation canonique d'une convention ou d'un avenant.

    L'identifiant stable est indépendant des futures clés primaires de base de
    données. Il pourra être partagé avec PMSL-Équipe et survivre à un export,
    une réplication de paramétrage ou une migration de base.
    """

    def __init__(
        self,
        date_debut,
        date_fin=None,
        reference="",
        statut=STATUT_BROUILLON,
        mode_facturation=FACTURATION_MANUELLE,
        version=1,
        identifiant_stable=None,
        identifiant_parent=None,
    ):
        self.date_debut = _GetDate(date_debut, "date_debut")
        self.date_fin = _GetDate(date_fin, "date_fin")
        self.reference = (reference or "").strip()
        self.statut = statut
        self.mode_facturation = mode_facturation
        self.version = int(version)
        self.identifiant_stable = _GetUUID(
            identifiant_stable, "identifiant_stable", obligatoire=True
        )
        self.identifiant_parent = _GetUUID(
            identifiant_parent, "identifiant_parent", obligatoire=False
        )
        self.Validation()

    def Validation(self):
        if self.date_debut is None:
            raise ValueError("date_debut est obligatoire")
        if self.date_fin is not None and self.date_fin < self.date_debut:
            raise ValueError("date_fin ne peut pas précéder date_debut")
        if self.statut not in STATUTS:
            raise ValueError("statut de convention inconnu : %s" % self.statut)
        if self.mode_facturation not in MODES_FACTURATION:
            raise ValueError(
                "mode de facturation inconnu : %s" % self.mode_facturation
            )
        if self.version < 1:
            raise ValueError("version doit être supérieure ou égale à 1")
        if self.identifiant_parent == self.identifiant_stable:
            raise ValueError("une convention ne peut pas être son propre parent")
        if self.identifiant_parent is not None and self.version < 2:
            raise ValueError("un avenant doit avoir une version supérieure à 1")
        return True

    def EstAvenant(self):
        return self.identifiant_parent is not None

    def EstActiveA(self, date_reference):
        """Indique si la période contractuelle couvre une date donnée.

        Le statut n'est volontairement pas utilisé ici : période de validité et
        état de traitement sont deux informations distinctes.
        """
        date_reference = _GetDate(date_reference, "date_reference")
        if date_reference < self.date_debut:
            return False
        if self.date_fin is not None and date_reference > self.date_fin:
            return False
        return True

    def GetChampsFusion(self):
        """Retourne les champs canoniques utilisables par le moteur documentaire."""
        return {
            "{CONVENTION_ID_STABLE}": self.identifiant_stable,
            "{CONVENTION_REFERENCE}": self.reference,
            "{CONVENTION_VERSION}": str(self.version),
            "{CONVENTION_STATUT}": self.statut,
            "{CONVENTION_DATE_DEBUT}": _FormatDate(self.date_debut),
            "{CONVENTION_DATE_FIN}": _FormatDate(self.date_fin),
            "{CONVENTION_MODE_FACTURATION}": self.mode_facturation,
            "{CONVENTION_PARENT_ID_STABLE}": self.identifiant_parent or "",
            "{CONVENTION_EST_AVENANT}": "1" if self.EstAvenant() else "0",
        }

    def GetDonnees(self):
        """Retourne un dictionnaire sérialisable sans dépendance de stockage."""
        return {
            "identifiant_stable": self.identifiant_stable,
            "identifiant_parent": self.identifiant_parent,
            "reference": self.reference,
            "version": self.version,
            "statut": self.statut,
            "mode_facturation": self.mode_facturation,
            "date_debut": self.date_debut.isoformat(),
            "date_fin": self.date_fin.isoformat() if self.date_fin else None,
        }
