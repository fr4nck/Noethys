#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Activation additive de l'inbox du réalisé canonique de séance.

Le socle Noe-062C doit déjà être présent et conforme. Cette activation ne crée
que ``interventions_execution_inbox`` et ne modifie aucune table existante.
"""
from __future__ import unicode_literals

import re

from Data import DATA_Interventions_Actual_Inbox
from Data import DATA_Structures


TABLE_INBOX = DATA_Interventions_Actual_Inbox.TABLE_INBOX
PREREQUIS = ("interventions", "lieux", "interventions_execution")


def _description(nom_table):
    if nom_table == TABLE_INBOX:
        return tuple(DATA_Interventions_Actual_Inbox.DB_INTERVENTIONS_ACTUAL_INBOX[nom_table])
    return tuple(DATA_Structures.DB_STRUCTURES[nom_table])


def _chaine(valeur):
    if isinstance(valeur, bytes):
        return valeur.decode("ascii", "ignore")
    return str(valeur)


def _categorie_type(type_sql):
    valeur = _chaine(type_sql or "").strip().lower()
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
    if type_decl in ("DATE", "DATETIME"):
        return "VARCHAR(10)" if type_decl == "DATE" else "DATETIME"
    if type_decl.startswith("VARCHAR"):
        match = re.search(r"\((\d+)\)", type_decl)
        if match:
            taille = int(match.group(1))
            if taille > 20000:
                return "MEDIUMTEXT"
            if taille > 255:
                return "TEXT(%d)" % taille
    return type_decl


def _metadata_table(db, nom_table):
    is_network = bool(getattr(db, "isNetwork", False))
    colonnes = {}
    if not is_network:
        if db.ExecuterReq("PRAGMA table_info('%s');" % nom_table) != 1:
            return None
        for cid, nom, type_sql, notnull, valeur_defaut, pk in db.ResultatReq():
            colonnes[_chaine(nom)] = {
                "type": type_sql,
                "pk": bool(pk),
                "auto": bool(pk) and _categorie_type(type_sql) == "integer",
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


def _inspecter_table(db, nom_table):
    existe = bool(db.IsTableExists(nom_table))
    description = _description(nom_table)
    attendus = tuple(champ[0] for champ in description)
    rapport = {
        "existe": existe,
        "champs_attendus": attendus,
        "champs_presents": (),
        "champs_manquants": attendus,
        "champs_incompatibles": (),
        "conforme": False,
    }
    if not existe:
        return rapport
    metadata = _metadata_table(db, nom_table)
    if metadata is None:
        return rapport
    rapport["champs_presents"] = tuple(metadata.keys())
    rapport["champs_manquants"] = tuple(champ for champ in attendus if champ not in metadata)
    incompatibles = []
    is_network = bool(getattr(db, "isNetwork", False))
    for nom, type_decl, info in description:
        if nom not in metadata:
            continue
        attendu = _type_attendu(type_decl, is_network)
        present = metadata[nom]
        if _categorie_type(attendu) != _categorie_type(present["type"]):
            incompatibles.append(nom)
        elif "PRIMARY KEY" in attendu and not present["pk"]:
            incompatibles.append(nom)
        elif "AUTO_INCREMENT" in attendu and not present["auto"]:
            incompatibles.append(nom)
    rapport["champs_incompatibles"] = tuple(incompatibles)
    rapport["conforme"] = not rapport["champs_manquants"] and not rapport["champs_incompatibles"]
    return rapport


def InspecterSchemaInboxRealise(db):
    noms = PREREQUIS + (TABLE_INBOX,)
    return dict((nom, _inspecter_table(db, nom)) for nom in noms)


def AssurerSchemaInboxRealise(db, appliquer=False):
    """Crée uniquement l'inbox après préflight complet du socle Noe-062C."""
    avant = InspecterSchemaInboxRealise(db)
    prerequis_absents = tuple(nom for nom in PREREQUIS if not avant[nom]["existe"])
    incoherentes = tuple(
        nom for nom, rapport in avant.items()
        if rapport["existe"] and not rapport["conforme"]
    )
    if prerequis_absents or incoherentes:
        return {
            "ok": False,
            "appliquer": bool(appliquer),
            "tables_creees": (),
            "prerequis_absents": prerequis_absents,
            "tables_incoherentes": incoherentes,
            "rapport": avant,
        }
    creees = []
    if appliquer and not avant[TABLE_INBOX]["existe"]:
        db.CreationTable(
            TABLE_INBOX,
            DATA_Interventions_Actual_Inbox.DB_INTERVENTIONS_ACTUAL_INBOX,
        )
        db.Commit()
        creees.append(TABLE_INBOX)
    apres = InspecterSchemaInboxRealise(db)
    return {
        "ok": all(apres[nom]["conforme"] for nom in PREREQUIS) and (
            apres[TABLE_INBOX]["conforme"] if appliquer else True
        ),
        "appliquer": bool(appliquer),
        "tables_creees": tuple(creees),
        "prerequis_absents": (),
        "tables_incoherentes": tuple(
            nom for nom, rapport in apres.items()
            if rapport["existe"] and not rapport["conforme"]
        ),
        "rapport": apres,
    }
