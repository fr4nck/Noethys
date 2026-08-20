#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Licence :        GNU GPL
#------------------------------------------------------------------------
"""Lecture seule du planning Teamworks pour le dashboard Noethys.

Le lecteur ne duplique aucune donnée dans Noethys. Il ouvre la base Teamworks
en SQLite ``mode=ro`` et lit la table historique ``presences`` avec les noms de
personnes et catégories. Une base explicitement configurée est prioritaire ; à
défaut, le fichier Teamworks standard est recherché via ``Config.json``.
"""

import datetime
import json
import os
import sqlite3
import sys

from Utils import UTILS_Config

try:
    import appdirs
except Exception:
    appdirs = None


PARAMETRE_BASE = "teamworks_planning_database"


def _normalise_chemin(path):
    if not path:
        return None
    return os.path.abspath(os.path.expanduser(str(path)))


def _config_teamworks_standard():
    if appdirs is None:
        return None
    try:
        rep = appdirs.user_config_dir(appname=None, appauthor=False, roaming=True)
    except Exception:
        return None
    return os.path.join(rep, "teamworks", "Config.json")


def _rep_data_teamworks_standard():
    if appdirs is None:
        return None
    try:
        if sys.platform == "win32":
            rep = appdirs.site_data_dir(appname=None, appauthor=False)
            return os.path.join(rep, "teamworks")
        rep = appdirs.user_data_dir(appname=None, appauthor=False)
        return os.path.join(rep, "teamworks", "Data")
    except Exception:
        return None


def _base_depuis_config_teamworks():
    fichier_config = _config_teamworks_standard()
    if not fichier_config or not os.path.isfile(fichier_config):
        return None
    try:
        with open(fichier_config, "r", encoding="utf-8") as fichier:
            config = json.load(fichier)
    except Exception:
        return None

    nom = config.get("nomFichier")
    if not nom or "[RESEAU]" in str(nom):
        # Le connecteur lecture seule réseau/MySQL sera traité séparément.
        return None

    nom = str(nom)
    if os.path.isfile(nom):
        return _normalise_chemin(nom)

    # GestionDB Teamworks ajoute _TDATA.dat au nom logique du dossier.
    if nom.lower().endswith("_tdata.dat"):
        fichier = nom
    elif nom.lower().endswith(".dat"):
        fichier = nom[:-4] + "_TDATA.dat"
    else:
        fichier = nom + "_TDATA.dat"

    rep = _rep_data_teamworks_standard()
    if not rep:
        return None
    return _normalise_chemin(os.path.join(rep, fichier))


def GetCheminBase():
    """Retourne la base Teamworks locale à consulter, ou ``None``."""
    explicite = _normalise_chemin(UTILS_Config.GetParametre(PARAMETRE_BASE, None))
    if explicite and os.path.isfile(explicite):
        return explicite

    auto = _base_depuis_config_teamworks()
    if auto and os.path.isfile(auto):
        return auto
    return None


def SetCheminBase(path):
    path = _normalise_chemin(path)
    UTILS_Config.SetParametre(PARAMETRE_BASE, path)
    return path


def EstDisponible():
    return GetCheminBase() is not None


def _date_sql(date_dd):
    if isinstance(date_dd, datetime.datetime):
        date_dd = date_dd.date()
    return date_dd.strftime("%Y-%m-%d")


def GetSemaine(date_reference=None):
    """Lit les présences Teamworks du lundi au dimanche.

    Retourne ``(date_lundi, liste)``. Chaque élément expose : ``IDpersonne``,
    ``nom``, ``prenom``, ``date``, ``heure_debut``, ``heure_fin``, ``categorie``,
    ``couleur`` et ``intitule``.
    """
    if date_reference is None:
        date_reference = datetime.date.today()
    if isinstance(date_reference, datetime.datetime):
        date_reference = date_reference.date()

    lundi = date_reference - datetime.timedelta(days=date_reference.weekday())
    dimanche = lundi + datetime.timedelta(days=6)
    chemin = GetCheminBase()
    if chemin is None:
        return lundi, []

    # URI SQLite en lecture seule : aucune écriture accidentelle dans Teamworks.
    uri = "file:%s?mode=ro" % chemin.replace("\\", "/")
    connexion = sqlite3.connect(uri, uri=True, timeout=2.0)
    try:
        curseur = connexion.cursor()
        requete = """
            SELECT p.IDpersonne, pe.nom, pe.prenom,
                   p.date, p.heure_debut, p.heure_fin,
                   c.nom_categorie, c.couleur, p.intitule
            FROM presences AS p
            LEFT JOIN personnes AS pe ON pe.IDpersonne = p.IDpersonne
            LEFT JOIN cat_presences AS c ON c.IDcategorie = p.IDcategorie
            WHERE p.date >= ? AND p.date <= ?
            ORDER BY p.date, p.heure_debut, pe.nom, pe.prenom
        """
        curseur.execute(requete, (_date_sql(lundi), _date_sql(dimanche)))
        lignes = curseur.fetchall()
    finally:
        connexion.close()

    presences = []
    for ligne in lignes:
        (id_personne, nom, prenom, date_texte, heure_debut, heure_fin,
         categorie, couleur, intitule) = ligne
        try:
            date_dd = datetime.datetime.strptime(str(date_texte)[:10], "%Y-%m-%d").date()
        except Exception:
            continue
        presences.append({
            "IDpersonne": id_personne,
            "nom": nom or "",
            "prenom": prenom or "",
            "date": date_dd,
            "heure_debut": str(heure_debut or "")[:5],
            "heure_fin": str(heure_fin or "")[:5],
            "categorie": categorie or "",
            "couleur": couleur or "",
            "intitule": intitule or "",
        })
    return lundi, presences
