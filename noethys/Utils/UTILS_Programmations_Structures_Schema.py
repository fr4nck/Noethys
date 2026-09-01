#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Activation additive contrôlée des programmations Noe-062E."""
from __future__ import unicode_literals

import re

from Data import DATA_Programmations_Structures
from Data import DATA_Structures


TABLE_RELATIONS = "structures_relations"
TABLES_PROGRAMMATION = (
    "structures_programmations",
    "structures_programmations_creneaux",
)


def _description(nom_table):
    if nom_table in DATA_Programmations_Structures.DB_PROGRAMMATIONS_STRUCTURES:
        return tuple(DATA_Programmations_Structures.DB_PROGRAMMATIONS_STRUCTURES[nom_table])
    return tuple(DATA_Structures.DB_STRUCTURES[nom_table])


def _dico_creation(nom_table):
    if nom_table in DATA_Programmations_Structures.DB_PROGRAMMATIONS_STRUCTURES:
        return DATA_Programmations_Structures.DB_PROGRAMMATIONS_STRUCTURES
    return DATA_Structures.DB_STRUCTURES


def _chaine(valeur):
    if isinstance(valeur, bytes):
        return valeur.decode("ascii", "ignore")
    return str(valeur)


def _categorie(type_sql):
    if type_sql is None:
        return ""
    base = _chaine(type_sql).strip().lower().split("(", 1)[0].strip()
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


def _metadata(db, nom_table):
    colonnes = {}
    is_network = bool(getattr(db, "isNetwork", False))
    if not is_network:
        if db.ExecuterReq("PRAGMA table_info('%s');" % nom_table) != 1:
            return None
        for cid, nom, type_sql, notnull, default, pk in db.ResultatReq():
            colonnes[_chaine(nom)] = {
                "type": type_sql,
                "pk": bool(pk),
                "auto": bool(pk) and _categorie(type_sql) == "integer",
            }
    else:
        if db.ExecuterReq("SHOW COLUMNS FROM %s;" % nom_table) != 1:
            return None
        for valeurs in db.ResultatReq():
            colonnes[_chaine(valeurs[0])] = {
                "type": valeurs[1],
                "pk": _chaine(valeurs[3] if len(valeurs) > 3 else "").upper() == "PRI",
                "auto": "auto_increment" in _chaine(valeurs[5] if len(valeurs) > 5 else "").lower(),
            }
    return colonnes


def _inspecter(db, nom_table):
    existe = bool(db.IsTableExists(nom_table))
    description = _description(nom_table)
    attendus = tuple(item[0] for item in description)
    rapport = {
        "existe": existe,
        "champs_attendus": attendus,
        "champs_presents": (),
        "champs_manquants": attendus,
        "champs_incompatibles": (),
        "metadata_ok": False,
        "conforme": False,
    }
    if not existe:
        return rapport
    metadata = _metadata(db, nom_table)
    if metadata is None:
        return rapport
    rapport["metadata_ok"] = True
    rapport["champs_presents"] = tuple(metadata.keys())
    rapport["champs_manquants"] = tuple(x for x in attendus if x not in metadata)
    incompatibles = []
    is_network = bool(getattr(db, "isNetwork", False))
    for nom, type_decl, info in description:
        if nom not in metadata:
            continue
        attendu = _type_attendu(type_decl, is_network)
        present = metadata[nom]
        if _categorie(attendu) != _categorie(present["type"]):
            incompatibles.append(nom)
        elif "PRIMARY KEY" in attendu and not present["pk"]:
            incompatibles.append(nom)
        elif "AUTO_INCREMENT" in attendu and not present["auto"]:
            incompatibles.append(nom)
    rapport["champs_incompatibles"] = tuple(incompatibles)
    rapport["conforme"] = not rapport["champs_manquants"] and not incompatibles
    return rapport


def InspecterSchemaProgrammations(db):
    noms = (TABLE_RELATIONS,) + TABLES_PROGRAMMATION
    return dict((nom, _inspecter(db, nom)) for nom in noms)


def AssurerSchemaProgrammations(db, appliquer=False):
    """Crée uniquement les deux tables de programmation.

    ``structures_relations`` doit déjà exister et être conforme. Le préflight
    vérifie toutes les tables avant la première écriture.
    """
    avant = InspecterSchemaProgrammations(db)
    relation = avant[TABLE_RELATIONS]
    incoherentes = tuple(
        nom for nom, rapport in avant.items()
        if rapport["existe"] and not rapport["conforme"]
    )
    if not relation["existe"] or not relation["conforme"] or incoherentes:
        return {
            "ok": False,
            "appliquer": bool(appliquer),
            "tables_creees": (),
            "tables_absentes": tuple(n for n, r in avant.items() if not r["existe"]),
            "tables_incoherentes": incoherentes,
            "prerequis_absents": () if relation["existe"] else (TABLE_RELATIONS,),
            "rapport": avant,
        }

    creees = []
    if appliquer:
        for nom in TABLES_PROGRAMMATION:
            if not avant[nom]["existe"]:
                db.CreationTable(nom, _dico_creation(nom))
                db.Commit()
                creees.append(nom)

    apres = InspecterSchemaProgrammations(db)
    absentes = tuple(n for n, r in apres.items() if not r["existe"])
    incoherentes = tuple(n for n, r in apres.items() if r["existe"] and not r["conforme"])
    return {
        "ok": not incoherentes and (not appliquer or not absentes),
        "appliquer": bool(appliquer),
        "tables_creees": tuple(creees),
        "tables_absentes": absentes,
        "tables_incoherentes": incoherentes,
        "prerequis_absents": (),
        "rapport": apres,
    }
