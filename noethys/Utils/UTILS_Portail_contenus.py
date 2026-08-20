#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Licence:          GNU GPL
#------------------------------------------------------------------------

"""Helpers purs pour les contenus dynamiques du portail Connecthys.

Le premier objectif est volontairement limité : permettre à Noethys de
conserver une configuration enrichie localement tout en exportant vers un
Connecthys historique un bloc texte HTML parfaitement compatible.

Ce module ne dépend ni de wxPython, ni de la base de données, ni du réseau.
"""

import html
import json
from urllib.parse import urlparse


CATEGORIE_CONTENU_EXTERNE = "bloc_contenu_externe"
CATEGORIE_CONNECTHYS_TEXTE = "bloc_texte"
MARQUEUR_CONTENU_EXTERNE = "noethys_portail_contenu_externe"

HAUTEUR_MIN = 120
HAUTEUR_MAX = 3000
HAUTEUR_DEFAUT = 600


def normaliser_url(url):
    """Retourne une URL externe nettoyée sans tenter de la télécharger."""
    if url is None:
        return ""
    return str(url).strip()


def url_externe_valide(url):
    """Accepte uniquement les URL HTTP(S) absolues pour un contenu embarqué."""
    url = normaliser_url(url)
    if not url:
        return False
    try:
        parsed = urlparse(url)
    except (TypeError, ValueError):
        return False
    return parsed.scheme.lower() in ("http", "https") and bool(parsed.netloc)


def normaliser_hauteur(hauteur):
    """Normalise la hauteur d'un iframe dans une plage raisonnable."""
    try:
        valeur = int(hauteur)
    except (TypeError, ValueError):
        valeur = HAUTEUR_DEFAUT
    return max(HAUTEUR_MIN, min(HAUTEUR_MAX, valeur))


def normaliser_parametres(parametres=None):
    """Retourne la configuration canonique d'un bloc de contenu externe."""
    source = dict(parametres or {})
    return {
        "source": MARQUEUR_CONTENU_EXTERNE,
        "version": 1,
        "type": source.get("type", "iframe"),
        "url": normaliser_url(source.get("url", "")),
        "hauteur": normaliser_hauteur(source.get("hauteur", HAUTEUR_DEFAUT)),
        "defilement": bool(source.get("defilement", False)),
        "plein_ecran": bool(source.get("plein_ecran", True)),
        "titre": str(source.get("titre", "") or "").strip(),
    }


def serialiser_parametres(parametres=None):
    """Sérialise la configuration locale dans le champ parametres existant."""
    return json.dumps(
        normaliser_parametres(parametres),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _charger_json(valeur):
    if not valeur:
        return {}
    if isinstance(valeur, bytes):
        valeur = valeur.decode("utf-8")
    try:
        donnees = json.loads(valeur)
    except (TypeError, ValueError):
        return {}
    return donnees if isinstance(donnees, dict) else {}


def est_configuration_contenu_externe(valeur):
    """Détecte uniquement les paramètres écrits par ce moteur, sans faux positif."""
    return _charger_json(valeur).get("source") == MARQUEUR_CONTENU_EXTERNE


def deserialiser_parametres(valeur):
    """Lit une configuration sauvegardée et retombe sur les valeurs par défaut."""
    return normaliser_parametres(_charger_json(valeur))


def construire_iframe(parametres=None):
    """Construit le HTML compatible avec un bloc texte Connecthys historique."""
    config = normaliser_parametres(parametres)
    if config["type"] != "iframe":
        raise ValueError("Type de contenu externe non pris en charge : %s" % config["type"])
    if not url_externe_valide(config["url"]):
        raise ValueError("URL externe invalide")

    attributs = [
        ("src", config["url"]),
        ("width", "100%"),
        ("height", "%d" % config["hauteur"]),
        ("loading", "lazy"),
        ("scrolling", "yes" if config["defilement"] else "no"),
        ("frameborder", "0"),
    ]
    if config["titre"]:
        attributs.append(("title", config["titre"]))

    texte_attributs = " ".join(
        '%s="%s"' % (nom, html.escape(str(valeur), quote=True))
        for nom, valeur in attributs
    )
    if config["plein_ecran"]:
        texte_attributs += " allowfullscreen"

    return '<iframe %s></iframe>' % texte_attributs


def categorie_pour_connecthys(categorie):
    """Mappe les catégories enrichies locales vers le vocabulaire Connecthys stable."""
    if categorie == CATEGORIE_CONTENU_EXTERNE:
        return CATEGORIE_CONNECTHYS_TEXTE
    return categorie
