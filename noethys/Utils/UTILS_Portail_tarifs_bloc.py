#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Licence:          GNU GPL
#------------------------------------------------------------------------

"""Configuration locale du bloc de tarifs publié dans Connecthys.

Le bloc est enregistré côté Connecthys comme un banal ``bloc_texte``. La
configuration enrichie reste dans ``portail_elements.parametres`` afin que
Noethys puisse régénérer le HTML à chaque synchronisation sans introduire de
nouvelle dépendance côté serveur.
"""

import json


MARQUEUR_BLOC_TARIFS = "noethys_portail_tarifs"
VERSION_CONFIGURATION = 1
MODE_AUTOMATIQUE = "automatique"
MODE_SELECTION = "selection"
TITRE_DEFAUT = "Tarifs des activités"


def _liste_ids(valeurs):
    resultat = []
    for valeur in valeurs or []:
        try:
            valeur = int(valeur)
        except (TypeError, ValueError):
            continue
        if valeur not in resultat:
            resultat.append(valeur)
    return sorted(resultat)


def normaliser_configuration(configuration=None):
    source = dict(configuration or {})
    mode = str(source.get("mode") or MODE_AUTOMATIQUE).strip().lower()
    if mode not in (MODE_AUTOMATIQUE, MODE_SELECTION):
        mode = MODE_AUTOMATIQUE
    return {
        "source": MARQUEUR_BLOC_TARIFS,
        "version": VERSION_CONFIGURATION,
        "mode": mode,
        "IDsactivites": _liste_ids(source.get("IDsactivites")),
        "IDsactivites_exclues": _liste_ids(source.get("IDsactivites_exclues")),
        "titre": str(source.get("titre") or TITRE_DEFAUT).strip() or TITRE_DEFAUT,
    }


def serialiser_configuration(configuration=None):
    return json.dumps(
        normaliser_configuration(configuration),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _charger_json(valeur):
    if not valeur:
        return {}
    if isinstance(valeur, bytes):
        valeur = valeur.decode("utf-8", "replace")
    try:
        donnees = json.loads(valeur)
    except (TypeError, ValueError):
        return {}
    return donnees if isinstance(donnees, dict) else {}


def est_configuration_bloc_tarifs(valeur):
    return _charger_json(valeur).get("source") == MARQUEUR_BLOC_TARIFS


def deserialiser_configuration(valeur):
    return normaliser_configuration(_charger_json(valeur))


def politique_depuis_configuration(configuration=None):
    config = normaliser_configuration(configuration)
    return {
        "mode": config["mode"],
        "IDsactivites": list(config["IDsactivites"]),
        "IDsactivites_exclues": list(config["IDsactivites_exclues"]),
    }


def fusionner_choix_catalogue(configuration, IDs_catalogue, IDs_coches, mode=None):
    """Fusionne les choix visibles sans perdre ceux temporairement invisibles.

    Une activité peut sortir momentanément du catalogue parce qu'elle n'a plus
    de tarif courant/futur, puis redevenir publiable plus tard. Réenregistrer
    le bloc pendant cette période ne doit ni effacer une exclusion explicite,
    ni oublier une sélection manuelle historique.
    """
    config = normaliser_configuration(configuration)
    mode = str(mode or config["mode"]).strip().lower()
    if mode not in (MODE_AUTOMATIQUE, MODE_SELECTION):
        mode = MODE_AUTOMATIQUE

    catalogue = set(_liste_ids(IDs_catalogue))
    coches = set(_liste_ids(IDs_coches))

    if mode == MODE_SELECTION:
        invisibles = set(config["IDsactivites"]) - catalogue
        return {
            "mode": MODE_SELECTION,
            "IDsactivites": sorted(coches | invisibles),
            "IDsactivites_exclues": [],
        }

    exclusions_invisibles = set(config["IDsactivites_exclues"]) - catalogue
    exclusions_visibles = catalogue - coches
    return {
        "mode": MODE_AUTOMATIQUE,
        "IDsactivites": [],
        "IDsactivites_exclues": sorted(exclusions_invisibles | exclusions_visibles),
    }
