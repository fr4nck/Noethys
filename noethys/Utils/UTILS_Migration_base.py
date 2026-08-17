#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Outils de préparation d'une migration d'une base Noethys vers une base neuve.

Le module sépare volontairement l'analyse, la planification et l'exécution.
Aucune écriture n'est réalisée par :class:`AnalyseMigration` ou
:class:`PlanMigration`. Le moteur d'écriture pourra ainsi être précédé d'une
simulation complète et explicite.
"""

from __future__ import unicode_literals


# Dépendances métier minimales du cœur Noethys. Les tables non décrites ici ne
# sont jamais copiées silencieusement : elles sont classées en ``revue``.
DEPENDANCES_COEUR = {
    "familles": [],
    "individus": [],
    "comptes_payeurs": ["familles"],
    "rattachements": ["familles", "individus"],
    "activites": [],
    "groupes": ["activites"],
    "categories_tarifs": ["activites"],
    "noms_tarifs": ["activites"],
    "tarifs": ["activites"],
    "tarifs_lignes": ["tarifs"],
    "inscriptions": ["familles", "individus", "activites", "groupes"],
    "consommations": ["familles", "individus", "activites", "groupes", "inscriptions"],
    "prestations": ["comptes_payeurs"],
    "factures": ["familles"],
    "reglements": ["comptes_payeurs"],
    "ventilation": ["reglements", "prestations", "comptes_payeurs"],
    "cotisations": ["familles", "individus"],
    "rattachements": ["familles", "individus"],
    "questionnaire_reponses": ["familles", "individus"],
    "contrats": ["familles", "individus"],
    "contrats_tarifs": ["contrats"],
}


# Clé primaire la plus courante des tables cœur. Elle permettra au moteur
# d'écriture de conserver un dictionnaire ancien ID -> nouvel ID.
CLES_PRIMAIRES_COEUR = {
    "familles": "IDfamille",
    "individus": "IDindividu",
    "comptes_payeurs": "IDcompte_payeur",
    "rattachements": "IDrattachement",
    "activites": "IDactivite",
    "groupes": "IDgroupe",
    "categories_tarifs": "IDcategorie_tarif",
    "noms_tarifs": "IDnom_tarif",
    "tarifs": "IDtarif",
    "tarifs_lignes": "IDligne",
    "inscriptions": "IDinscription",
    "consommations": "IDconso",
    "prestations": "IDprestation",
    "factures": "IDfacture",
    "reglements": "IDreglement",
    "ventilation": "IDventilation",
    "cotisations": "IDcotisation",
    "questionnaire_reponses": "IDreponse",
    "contrats": "IDcontrat",
    "contrats_tarifs": "IDcontrat_tarif",
}


class MappingIDs(object):
    """Conserve les correspondances d'identifiants pendant une migration."""

    def __init__(self):
        self._mapping = {}

    def Ajouter(self, table, ancien_id, nouvel_id):
        self._mapping.setdefault(table, {})[ancien_id] = nouvel_id

    def Get(self, table, ancien_id, defaut=None):
        return self._mapping.get(table, {}).get(ancien_id, defaut)

    def Existe(self, table, ancien_id):
        return ancien_id in self._mapping.get(table, {})

    def GetTable(self, table):
        return dict(self._mapping.get(table, {}))

    def Resume(self):
        return {table: len(valeurs) for table, valeurs in self._mapping.items()}


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
        """Compare les tables/champs de la source et de la cible."""
        if self.DBcible is None:
            tables_source = self._liste_tables(self.DBsource)
            return {
                "tables_source": tables_source,
                "tables_cible": [],
                "tables_communes": [],
                "tables_source_uniquement": tables_source,
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


class PlanMigration(object):
    """Prépare un ordre de migration et une simulation sans écriture."""

    def __init__(self, analyse, dependances=None, cles_primaires=None):
        self.analyse = analyse
        self.dependances = dependances or DEPENDANCES_COEUR
        self.cles_primaires = cles_primaires or CLES_PRIMAIRES_COEUR

    def _ordre_topologique(self, tables):
        tables = set(tables)
        ordre = []
        restant = set(tables)
        while restant:
            avances = []
            for table in sorted(restant):
                deps = [d for d in self.dependances.get(table, []) if d in tables]
                if all(dep in ordre for dep in deps):
                    avances.append(table)
            if not avances:
                # Ne jamais inventer un ordre en présence d'un cycle ou d'une
                # dépendance inconnue : le bloc est envoyé en revue manuelle.
                return ordre, sorted(restant)
            for table in avances:
                ordre.append(table)
                restant.remove(table)
        return ordre, []

    def Construire(self):
        inventaire = {item["table"]: item for item in self.analyse.Inventaire(inclure_vides=False)}
        schema = self.analyse.ComparerSchemas()
        tables_source = set(inventaire)
        tables_cible = set(schema["tables_cible"])

        migrables = []
        revue = []
        ignorees = []

        for table in sorted(tables_source):
            item = inventaire[table]
            if table not in tables_cible:
                revue.append({"table": table, "raison": "table_absente_cible", "nbre": item["nbre"]})
                continue
            if table not in self.dependances:
                revue.append({"table": table, "raison": "dependances_non_decrites", "nbre": item["nbre"]})
                continue

            details = schema["champs"].get(table, {})
            source_uniquement = details.get("source_uniquement", [])
            if source_uniquement:
                revue.append({
                    "table": table,
                    "raison": "champs_source_sans_cible",
                    "champs": source_uniquement,
                    "nbre": item["nbre"],
                })
                continue

            migrables.append(table)

        ordre, cycles = self._ordre_topologique(migrables)
        for table in cycles:
            revue.append({"table": table, "raison": "dependance_cyclique_ou_inconnue", "nbre": inventaire[table]["nbre"]})

        for table in sorted(tables_cible - tables_source):
            ignorees.append({"table": table, "raison": "absente_source"})

        return {
            "ordre": ordre,
            "tables_migrables": [
                {
                    "table": table,
                    "nbre": inventaire[table]["nbre"],
                    "cle_primaire": self.cles_primaires.get(table),
                    "dependances": list(self.dependances.get(table, [])),
                    "strategie": "remap_ids" if self.dependances.get(table) else "copie_controlee",
                }
                for table in ordre
            ],
            "tables_revue": revue,
            "tables_ignorees": ignorees,
        }

    def Simuler(self):
        """Retourne le bilan de faisabilité sans effectuer aucune écriture."""
        plan = self.Construire()
        total_migrable = sum(item["nbre"] for item in plan["tables_migrables"] if item["nbre"] is not None)
        total_revue = sum(item.get("nbre", 0) or 0 for item in plan["tables_revue"])
        return {
            "ecriture_effectuee": False,
            "pret": len(plan["tables_revue"]) == 0,
            "lignes_migrables": total_migrable,
            "lignes_a_revoir": total_revue,
            "plan": plan,
        }
