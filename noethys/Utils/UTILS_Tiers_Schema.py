#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Activation additive contrôlée du schéma tiers Noe-062.

Ce module ne s'exécute jamais au simple import. L'appelant choisit explicitement
``appliquer=True`` pour créer les tables manquantes. Une table déjà existante
mais incohérente n'est jamais réparée silencieusement et bloque toute activation
afin de ne pas laisser un schéma partiellement créé.
"""

from __future__ import unicode_literals

import re

from Data import DATA_Structures


TABLES_062A = ("structures", "structures_contacts")
TABLES_062B = ("interventions",)
TABLES_062B_COMPLET = TABLES_062A + TABLES_062B


def _descriptions_attendues(nom_table):
    return tuple(DATA_Structures.DB_STRUCTURES[nom_table])


def _champs_attendus(nom_table):
    return tuple(champ[0] for champ in _descriptions_attendues(nom_table))


def _type_attendu(type_decl, is_network):
    """Reproduit les adaptations utiles de GestionDB.CreationTable."""
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


def _chaine(valeur):
    if isinstance(valeur, bytes):
        return valeur.decode("ascii", "ignore")
    return str(valeur)


def _categorie_type(type_sql):
    """Normalise les variantes SQLite/MySQL en familles compatibles."""
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
    """Retourne types + métadonnées PK/autoincrement sans écrire en base."""
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
                # En SQLite, INTEGER PRIMARY KEY est l'alias du rowid ;
                # AUTOINCREMENT n'est pas nécessaire à l'identité du champ mais
                # le contrat Noethys le déclare pour éviter la réutilisation.
                "auto": bool(pk) and _categorie_type(type_sql) == "integer",
            }
    else:
        if db.ExecuterReq("SHOW COLUMNS FROM %s;" % nom_table) != 1:
            return None
        for valeurs in db.ResultatReq():
            nom = _chaine(valeurs[0])
            type_sql = valeurs[1]
            cle = _chaine(valeurs[3] if len(valeurs) > 3 else "")
            extra = _chaine(valeurs[5] if len(valeurs) > 5 else "")
            colonnes[nom] = {
                "type": type_sql,
                "pk": cle.upper() == "PRI",
                "auto": "auto_increment" in extra.lower(),
            }
    return colonnes


def InspecterSchema(db, tables=TABLES_062A):
    """Retourne un rapport déterministe sans modifier la base."""
    rapport = {}
    is_network = bool(getattr(db, "isNetwork", False))

    for nom_table in tuple(tables):
        existe = bool(db.IsTableExists(nom_table))
        descriptions = _descriptions_attendues(nom_table)
        champs_attendus = tuple(champ[0] for champ in descriptions)
        champs_presents = ()
        champs_manquants = champs_attendus
        champs_incompatibles = ()
        metadata_ok = False

        if existe:
            metadata = _metadata_table(db, nom_table)
            if metadata is not None:
                champs_presents = tuple(metadata.keys())
                champs_manquants = tuple(champ for champ in champs_attendus if champ not in metadata)
                incompatibles = []
                for nom_champ, type_decl, info in descriptions:
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
                champs_incompatibles = tuple(incompatibles)
                metadata_ok = True

        conforme = existe and metadata_ok and not champs_manquants and not champs_incompatibles
        rapport[nom_table] = {
            "existe": existe,
            "champs_attendus": champs_attendus,
            "champs_presents": champs_presents,
            "champs_manquants": champs_manquants,
            "champs_incompatibles": champs_incompatibles,
            "metadata_ok": metadata_ok,
            "conforme": conforme,
        }
    return rapport


def _resultat(rapport, appliquer, creees=(), tables=TABLES_062A):
    tables = tuple(tables)
    incoherentes = tuple(
        nom_table for nom_table in tables
        if rapport[nom_table]["existe"] and not rapport[nom_table]["conforme"]
    )
    absentes = tuple(
        nom_table for nom_table in tables
        if not rapport[nom_table]["existe"]
    )
    return {
        "ok": not incoherentes and (not appliquer or not absentes),
        "appliquer": bool(appliquer),
        "tables_creees": tuple(creees),
        "tables_absentes": absentes,
        "tables_incoherentes": incoherentes,
        "rapport": rapport,
    }


def _assurer_schema(db, tables, appliquer=False):
    """Implémentation commune : préflight complet avant la première écriture."""
    tables = tuple(tables)
    avant = InspecterSchema(db, tables=tables)
    preflight = _resultat(avant, appliquer=False, tables=tables)

    if preflight["tables_incoherentes"]:
        return {
            "ok": False,
            "appliquer": bool(appliquer),
            "tables_creees": (),
            "tables_absentes": preflight["tables_absentes"],
            "tables_incoherentes": preflight["tables_incoherentes"],
            "rapport": avant,
        }

    creees = []
    if appliquer:
        for nom_table in tables:
            if not avant[nom_table]["existe"]:
                db.CreationTable(nom_table, DATA_Structures.DB_STRUCTURES)
                db.Commit()
                creees.append(nom_table)

    apres = InspecterSchema(db, tables=tables)
    return _resultat(apres, appliquer=appliquer, creees=creees, tables=tables)


def AssurerSchema(db, appliquer=False):
    """Conserve le contrat 062A : structures + contacts uniquement."""
    return _assurer_schema(db, TABLES_062A, appliquer=appliquer)


def InspecterSchema062B(db):
    """Inspecte le socle complet nécessaire aux séances école/sport."""
    return InspecterSchema(db, tables=TABLES_062B_COMPLET)


def AssurerSchema062B(db, appliquer=False):
    """Active explicitement structures, contacts et interventions.

    Aucun groupe ni convention n'est exigé pour saisir une première séance :
    ces liens restent optionnels et pourront être enrichis ensuite.
    """
    return _assurer_schema(db, TABLES_062B_COMPLET, appliquer=appliquer)