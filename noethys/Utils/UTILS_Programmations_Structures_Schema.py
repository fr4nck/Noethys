#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Activation additive contrôlée du schéma des programmations Noe-062E.

Le stockage de programmation est commun aux relations contractuelles et aux
activités internes Noethys. Son activation ne dépend donc d'aucune table de
relation : les prérequis propres à chaque ``type_source`` sont contrôlés par
le service métier au moment de créer une programmation.
"""
from __future__ import unicode_literals

import re

from Data import DATA_Programmations_Structures


TABLE_PROGRAMMATIONS = "structures_programmations"
TABLE_CRENEAUX = "structures_programmations_creneaux"
TABLES_CIBLES = (TABLE_PROGRAMMATIONS, TABLE_CRENEAUX)


def _description(nom_table):
    return tuple(DATA_Programmations_Structures.DB_PROGRAMMATIONS_STRUCTURES[nom_table])


def _chaine(valeur):
    if isinstance(valeur, bytes):
        return valeur.decode("ascii", "ignore")
    return str(valeur)


def _type_attendu(type_decl, is_network):
    type_decl = type_decl.upper().strip()
    if not is_network:
        if type_decl == "LONGBLOB":
            return "BLOB"
        if type_decl == "BIGINT":
            return "INTEGER"
        return type_decl
    if type_decl == "INTEGER PRIMARY KEY AUTOINCREMENT":
        return "INTEGER PRIMARY KEY AUTO_INCREMENT"
    if type_decl == "FLOAT":
        return "REAL"
    if type_decl == "DATE":
        return "VARCHAR(10)"
    if type_decl.startswith("VARCHAR"):
        match = re.search(r"\((\d+)\)", type_decl)
        if match:
            taille = int(match.group(1))
            if taille > 20000:
                return "MEDIUMTEXT"
            if taille > 255:
                return "TEXT(%d)" % taille
    return type_decl


def _categorie_type(type_sql):
    if type_sql is None:
        return ""
    valeur = _chaine(type_sql).strip().lower()
    base = valeur.split("(", 1)[0].strip()
    if "int" in base:
        return "integer"
    if base in ("float", "real", "double", "decimal", "numeric"):
        return "real"
    if base in ("char", "varchar", "text", "tinytext", "mediumtext", "longtext"):
        return "text"
    if base in ("blob", "tinyblob", "mediumblob", "longblob"):
        return "blob"
    if base in ("date", "datetime", "timestamp"):
        return "date"
    return base


def _metadata_table(db, nom_table):
    is_network = bool(getattr(db, "isNetwork", False))
    colonnes = {}
    if not is_network:
        if db.ExecuterReq("PRAGMA table_info('%s');" % nom_table) != 1:
            return None
        for cid, nom, type_sql, notnull, valeur_defaut, pk in db.ResultatReq():
            nom = _chaine(nom)
            colonnes[nom] = {
                "type": type_sql,
                "pk": bool(pk),
                "auto": bool(pk) and _categorie_type(type_sql) == "integer",
            }
    else:
        if db.ExecuterReq("SHOW COLUMNS FROM %s;" % nom_table) != 1:
            return None
        for valeurs in db.ResultatReq():
            nom = _chaine(valeurs[0])
            colonnes[nom] = {
                "type": valeurs[1],
                "pk": _chaine(valeurs[3] if len(valeurs) > 3 else "").upper() == "PRI",
                "auto": "auto_increment" in _chaine(valeurs[5] if len(valeurs) > 5 else "").lower(),
            }
    return colonnes


def _inspecter_table(db, nom_table):
    existe = bool(db.IsTableExists(nom_table))
    description = _description(nom_table)
    champs_attendus = tuple(champ[0] for champ in description)
    rapport = {
        "existe": existe,
        "champs_attendus": champs_attendus,
        "champs_presents": (),
        "champs_manquants": champs_attendus,
        "champs_incompatibles": (),
        "metadata_ok": False,
        "conforme": False,
    }
    if not existe:
        return rapport
    metadata = _metadata_table(db, nom_table)
    if metadata is None:
        return rapport
    rapport["metadata_ok"] = True
    rapport["champs_presents"] = tuple(metadata.keys())
    rapport["champs_manquants"] = tuple(
        champ for champ in champs_attendus if champ not in metadata
    )
    incompatibles = []
    is_network = bool(getattr(db, "isNetwork", False))
    for nom_champ, type_decl, info in description:
        if nom_champ not in metadata:
            continue
        attendu = _type_attendu(type_decl, is_network)
        present = metadata[nom_champ]
        if _categorie_type(attendu) != _categorie_type(present["type"]):
            incompatibles.append(nom_champ)
            continue
        if "PRIMARY KEY" in attendu and not present["pk"]:
            incompatibles.append(nom_champ)
            continue
        if "AUTO_INCREMENT" in attendu and not present["auto"]:
            incompatibles.append(nom_champ)
    rapport["champs_incompatibles"] = tuple(incompatibles)
    rapport["conforme"] = (
        rapport["metadata_ok"]
        and not rapport["champs_manquants"]
        and not rapport["champs_incompatibles"]
    )
    return rapport


def InspecterSchemaProgrammations(db):
    return dict((nom, _inspecter_table(db, nom)) for nom in TABLES_CIBLES)


def AssurerSchemaProgrammations(db, appliquer=False):
    """Crée uniquement les deux tables 062E après préflight complet."""
    avant = InspecterSchemaProgrammations(db)
    incoherentes = tuple(
        nom for nom, rapport in avant.items()
        if rapport["existe"] and not rapport["conforme"]
    )
    if incoherentes:
        return {
            "ok": False,
            "appliquer": bool(appliquer),
            "tables_creees": (),
            "tables_absentes": tuple(
                nom for nom, rapport in avant.items() if not rapport["existe"]
            ),
            "tables_incoherentes": incoherentes,
            "prerequis_absents": (),
            "rapport": avant,
        }

    creees = []
    if appliquer:
        for nom_table in TABLES_CIBLES:
            if not avant[nom_table]["existe"]:
                db.CreationTable(
                    nom_table,
                    DATA_Programmations_Structures.DB_PROGRAMMATIONS_STRUCTURES,
                )
                creees.append(nom_table)
        if creees:
            db.Commit()

    apres = InspecterSchemaProgrammations(db)
    absentes = tuple(
        nom for nom, rapport in apres.items() if not rapport["existe"]
    )
    incoherentes = tuple(
        nom for nom, rapport in apres.items()
        if rapport["existe"] and not rapport["conforme"]
    )
    return {
        "ok": not incoherentes and (not appliquer or not absentes),
        "appliquer": bool(appliquer),
        "tables_creees": tuple(creees),
        "tables_absentes": absentes,
        "tables_incoherentes": incoherentes,
        "prerequis_absents": (),
        "rapport": apres,
    }
