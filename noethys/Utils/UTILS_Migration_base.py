#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Outils de préparation d'une migration d'une base Noethys vers une base neuve.

Ce module est volontairement non destructif pour sa première étape : il analyse
une base source et une base cible, compare leurs schémas et compte les lignes.
Il servira ensuite de socle à l'assistant de migration DB -> DB.
"""

from __future__ import unicode_literals


class AnalyseMigration(object):
    """Construit un état des lieux source/cible sans modifier les bases."""

    def __init__(self, DBsource, DBcible=None):
        self.DBsource = DBsource
        self.DBcible = DBcible

    def _liste_tables(self, DB):
        if DB is None:
            return []
        return sorted([ligne[0] for ligne in DB.GetListeTables()])

    def _liste_champs(self, DB, table):
        return [nom for nom, _type in DB.GetListeChamps2(table)]

    def _compte_lignes(self, DB, table):
        if not DB.ExecuterReq("SELECT COUNT(*) FROM %s;" % table):
            return None
        resultat = DB.ResultatReq()
        if not resultat:
            return 0
        return int(resultat[0][0])

    def Inventaire(self, inclure_vides=True):
        """Retourne l'inventaire de la base source, sans aucune écriture."""
        inventaire = []
        for table in self._liste_tables(self.DBsource):
            nbre = self._compte_lignes(self.DBsource, table)
            if inclure_vides or nbre:
                inventaire.append({
                    "table": table,
                    "nbre": nbre,
                    "champs": self._liste_champs(self.DBsource, table),
                })
        return inventaire

    def ComparerSchemas(self):
        """Compare les tables/champs de la source et de la cible.

        Le résultat permet de préparer ensuite un mapping explicite avant toute
        migration. Aucune transformation automatique silencieuse n'est faite.
        """
        if self.DBcible is None:
            return {
                "tables_source": self._liste_tables(self.DBsource),
                "tables_cible": [],
                "tables_communes": [],
                "tables_source_uniquement": self._liste_tables(self.DBsource),
                "tables_cible_uniquement": [],
                "champs": {},
            }

        source = set(self._liste_tables(self.DBsource))
        cible = set(self._liste_tables(self.DBcible))
        communes = sorted(source & cible)
        details = {}
        for table in communes:
            champs_source = set(self._liste_champs(self.DBsource, table))
            champs_cible = set(self._liste_champs(self.DBcible, table))
            details[table] = {
                "communs": sorted(champs_source & champs_cible),
                "source_uniquement": sorted(champs_source - champs_cible),
                "cible_uniquement": sorted(champs_cible - champs_source),
            }

        return {
            "tables_source": sorted(source),
            "tables_cible": sorted(cible),
            "tables_communes": communes,
            "tables_source_uniquement": sorted(source - cible),
            "tables_cible_uniquement": sorted(cible - source),
            "champs": details,
        }

    def Resume(self):
        """Retourne un résumé exploitable par une future interface d'assistant."""
        inventaire = self.Inventaire(inclure_vides=False)
        comparaison = self.ComparerSchemas()
        return {
            "tables_non_vides": len(inventaire),
            "lignes_source": sum(item["nbre"] for item in inventaire if item["nbre"] is not None),
            "inventaire": inventaire,
            "schema": comparaison,
        }
