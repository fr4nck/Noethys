#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests synthétiques du migrateur DB -> DB, sans dépendance à wx."""

from __future__ import unicode_literals

import ast
import importlib.util
import pathlib
import re
import unittest


MODULE_PATH = pathlib.Path(__file__).parents[1] / "noethys" / "Utils" / "UTILS_Migration_base.py"
SPEC = importlib.util.spec_from_file_location("migration_base", str(MODULE_PATH))
migration = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(migration)


class ConnexionFactice(object):
    def __init__(self):
        self.rollback_effectue = False

    def rollback(self):
        self.rollback_effectue = True


class DBFactice(object):
    def __init__(self, schema, lignes=None):
        self.schema = schema
        self.lignes = lignes or {}
        self.resultat = []
        self.insertions = []
        self.mises_a_jour = []
        self.commits = 0
        self.prochain_id = 1000
        self.connexion = ConnexionFactice()

    def GetListeTables(self):
        return [(table,) for table in self.schema]

    def GetListeChamps2(self, table):
        return [(champ, "INTEGER") for champ in self.schema[table]]

    def ExecuterReq(self, requete):
        table = re.search(r"FROM ([A-Za-z0-9_]+)", requete).group(1)
        if requete.startswith("SELECT COUNT(*)"):
            self.resultat = [(len(self.lignes.get(table, [])),)]
        else:
            champs = requete.split(" FROM ")[0][7:].split(", ")
            self.resultat = [tuple(ligne.get(champ) for champ in champs)
                             for ligne in self.lignes.get(table, [])]
        return True

    def ResultatReq(self):
        return self.resultat

    def ReqInsert(self, table, donnees, commit=False):
        self.prochain_id += 1
        self.insertions.append((table, dict(donnees), commit, self.prochain_id))
        return self.prochain_id

    def ReqMAJ(self, table, donnees, champ_id, valeur_id, commit=False):
        self.mises_a_jour.append((table, dict(donnees), champ_id, valeur_id, commit))
        return True

    def Commit(self):
        self.commits += 1


class MigrationDossiersTest(unittest.TestCase):
    def test_toutes_les_references_potentielles_du_perimetre_sont_decrites(self):
        tables_path = pathlib.Path(__file__).parents[1] / "noethys" / "Data" / "DATA_Tables.py"
        arbre = ast.parse(tables_path.read_text(encoding="utf-8"))
        noeud = next(noeud.value for noeud in arbre.body
                     if isinstance(noeud, ast.Assign)
                     and any(isinstance(cible, ast.Name) and cible.id == "DB_DATA"
                             for cible in noeud.targets))
        schema_declare = ast.literal_eval(noeud)
        tables = set(migration.PERIMETRES_MIGRATION["dossiers"])
        a_traiter = list(tables)
        while a_traiter:
            table = a_traiter.pop()
            for dependance in migration.DEPENDANCES_COEUR.get(table, []):
                if dependance not in tables:
                    tables.add(dependance)
                    a_traiter.append(dependance)

        non_decrites = {}
        for table in tables:
            if table not in schema_declare:
                continue
            pk = migration.CLES_PRIMAIRES_COEUR.get(table)
            potentielles = set(champ for champ, _type, _description in schema_declare[table]
                               if champ != pk and (champ.startswith("ID") or
                                                   champ in migration.NOMS_REFERENCES_HISTORIQUES))
            connues = set(migration.REFERENCES_COEUR.get(table, {}))
            connues.update(migration.REFERENCES_PRESERVEES.get(table, set()))
            connues.update(migration.REFERENCES_POLYMORPHES.get(table, {}))
            if potentielles - connues:
                non_decrites[table] = sorted(potentielles - connues)
        self.assertEqual(non_decrites, {})

    def test_registre_metier_couvre_les_references_historiques(self):
        attendues = {
            "adresse_auto": "individus",
            "allocataire": "individus",
            "prelevement_banque": "banques",
            "prelevement_individu": "individus",
            "titulaire_helios": "individus",
            "tiers_solidaire": "individus",
        }
        for champ, cible in attendues.items():
            table = "individus" if champ == "adresse_auto" else "familles"
            self.assertEqual(migration.REFERENCES_COEUR[table][champ], cible)
        self.assertEqual(migration.REFERENCES_DIFFEREES["individus"]["adresse_auto"], "individus")
        self.assertEqual(migration.REFERENCES_DIFFEREES["familles"]["IDcompte_payeur"],
                         "comptes_payeurs")
        self.assertEqual(migration.REFERENCES_PRESERVEES["individus"],
                         {"IDcivilite", "IDnationalite", "IDpays_naiss"})

    def test_simulation_puis_migration_remappent_referentiels_et_cycles(self):
        schema = {
            "regimes": ["IDregime", "nom"],
            "caisses": ["IDcaisse", "IDregime", "nom"],
            "banques": ["IDbanque", "nom"],
            "secteurs": ["IDsecteur", "nom"],
            "categories_travail": ["IDcategorie", "nom"],
            "medecins": ["IDmedecin", "nom"],
            "types_sieste": ["IDtype_sieste", "nom"],
            "utilisateurs": ["IDutilisateur", "nom"],
            "restaurateurs": ["IDrestaurateur", "nom"],
            "individus": ["IDindividu", "IDcivilite", "IDnationalite", "IDpays_naiss",
                          "adresse_auto", "IDsecteur", "IDcategorie_travail", "IDmedecin",
                          "IDtype_sieste", "nom"],
            "familles": ["IDfamille", "IDcompte_payeur", "IDcaisse", "allocataire",
                         "prelevement_banque", "prelevement_individu", "titulaire_helios",
                         "tiers_solidaire", "nom"],
            "activites": ["IDactivite", "nom"],
            "groupes": ["IDgroupe", "IDactivite", "nom"],
            "unites": ["IDunite", "IDactivite", "IDrestaurateur", "nom"],
            "comptes_payeurs": ["IDcompte_payeur", "IDfamille", "IDindividu"],
            "inscriptions": ["IDinscription", "IDfamille", "IDindividu", "IDactivite",
                             "IDgroupe", "IDcompte_payeur"],
            "consommations": ["IDconso", "IDindividu", "IDinscription", "IDactivite",
                              "IDunite", "IDgroupe", "IDutilisateur", "IDcompte_payeur"],
        }
        lignes = {
            "regimes": [{"IDregime": 1, "nom": "General"}],
            "caisses": [{"IDcaisse": 2, "IDregime": 1, "nom": "CAF"}],
            "banques": [{"IDbanque": 3, "nom": "Banque"}],
            "secteurs": [{"IDsecteur": 4, "nom": "Nord"}],
            "categories_travail": [{"IDcategorie": 5, "nom": "Salarie"}],
            "medecins": [{"IDmedecin": 6, "nom": "Martin"}],
            "types_sieste": [{"IDtype_sieste": 7, "nom": "Courte"}],
            "utilisateurs": [{"IDutilisateur": 8, "nom": "Admin"}],
            "restaurateurs": [{"IDrestaurateur": 9, "nom": "Cuisine"}],
            "individus": [
                {"IDindividu": 10, "IDcivilite": 1, "IDnationalite": 2,
                 "IDpays_naiss": 3, "adresse_auto": 11, "IDsecteur": 4,
                 "IDcategorie_travail": 5, "IDmedecin": 6, "IDtype_sieste": 7,
                 "nom": "Alice"},
                {"IDindividu": 11, "IDcivilite": 1, "IDnationalite": 2,
                 "IDpays_naiss": 3, "adresse_auto": None, "IDsecteur": 4,
                 "IDcategorie_travail": 5, "IDmedecin": 6, "IDtype_sieste": 7,
                 "nom": "Bob"},
            ],
            "familles": [{"IDfamille": 20, "IDcompte_payeur": 30, "IDcaisse": 2,
                           "allocataire": 10, "prelevement_banque": 3,
                           "prelevement_individu": 10, "titulaire_helios": 10,
                           "tiers_solidaire": 11, "nom": "Famille"}],
            "activites": [{"IDactivite": 40, "nom": "Accueil"}],
            "groupes": [{"IDgroupe": 41, "IDactivite": 40, "nom": "Groupe"}],
            "unites": [{"IDunite": 42, "IDactivite": 40, "IDrestaurateur": 9,
                        "nom": "Journee"}],
            "comptes_payeurs": [{"IDcompte_payeur": 30, "IDfamille": 20,
                                  "IDindividu": 10}],
            "inscriptions": [{"IDinscription": 50, "IDfamille": 20, "IDindividu": 10,
                              "IDactivite": 40, "IDgroupe": 41, "IDcompte_payeur": 30}],
            "consommations": [{"IDconso": 60, "IDindividu": 10, "IDinscription": 50,
                               "IDactivite": 40, "IDunite": 42, "IDgroupe": 41,
                               "IDutilisateur": 8, "IDcompte_payeur": 30}],
        }
        source, cible = DBFactice(schema, lignes), DBFactice(schema)
        moteur = migration.MoteurMigration(source, cible, tables="dossiers")

        simulation = moteur.Simuler()
        self.assertTrue(simulation["pret"], simulation)
        self.assertEqual(cible.insertions, [])
        self.assertEqual(cible.mises_a_jour, [])
        self.assertEqual(cible.commits, 0)

        resultat = moteur.Executer()
        self.assertTrue(resultat["succes"], resultat)
        self.assertEqual(cible.commits, 1)
        self.assertEqual(len(cible.mises_a_jour), 2)
        famille = next(donnees for table, donnees, _commit, _id in cible.insertions
                       if table == "familles")
        individu = next(donnees for table, donnees, _commit, _id in cible.insertions
                        if table == "individus" and donnees["nom"] == "Alice")
        consommation = next(donnees for table, donnees, _commit, _id in cible.insertions
                            if table == "consommations")
        self.assertEqual(famille["allocataire"], moteur.mapping.Get("individus", 10))
        self.assertEqual(famille["prelevement_banque"], moteur.mapping.Get("banques", 3))
        self.assertEqual(consommation["IDutilisateur"], moteur.mapping.Get("utilisateurs", 8))
        self.assertEqual(individu["IDcivilite"], 1)
        self.assertTrue(all(not commit for _table, _donnees, commit, _id in cible.insertions))

    def test_reference_historique_omise_bloque_le_plan(self):
        schema = {"familles": ["IDfamille", "allocataire"]}
        source, cible = DBFactice(schema, {"familles": [{"IDfamille": 1, "allocataire": 2}]}), DBFactice(schema)
        analyse = migration.AnalyseMigration(source, cible)
        plan = migration.PlanMigration(
            analyse, dependances={"familles": []}, cles_primaires={"familles": "IDfamille"},
            references={"familles": {}}, references_preservees={}, tables=["familles"])
        resultat = plan.Simuler()
        self.assertFalse(resultat["pret"])
        self.assertEqual(resultat["plan"]["tables_revue"][0]["raison"],
                         "references_non_decrites")
        self.assertEqual(resultat["plan"]["tables_revue"][0]["champs"], ["allocataire"])

    def test_reference_orpheline_bloque_avant_toute_ecriture(self):
        schema = {
            "secteurs": ["IDsecteur", "nom"],
            "individus": ["IDindividu", "IDsecteur", "nom"],
        }
        lignes = {
            "secteurs": [{"IDsecteur": 4, "nom": "Nord"}],
            "individus": [{"IDindividu": 10, "IDsecteur": 999, "nom": "Alice"}],
        }
        source, cible = DBFactice(schema, lignes), DBFactice(schema)
        moteur = migration.MoteurMigration(source, cible, tables=["individus"])
        resultat = moteur.Executer()
        self.assertFalse(resultat["succes"])
        self.assertFalse(resultat["commit"])
        self.assertEqual(cible.insertions, [])
        self.assertTrue(any(erreur.get("erreur") == "reference_source_absente"
                            for erreur in resultat["simulation"]["erreurs"]))

    def test_reference_polymorphe_est_remappee_selon_son_type(self):
        schema = {
            "questionnaire_categories": ["IDcategorie", "nom"],
            "questionnaire_questions": ["IDquestion", "IDcategorie", "label"],
            "individus": ["IDindividu", "nom"],
            "questionnaire_reponses": ["IDreponse", "IDquestion", "IDindividu",
                                        "IDfamille", "reponse", "type", "IDdonnee"],
        }
        lignes = {
            "questionnaire_categories": [{"IDcategorie": 1, "nom": "Identite"}],
            "questionnaire_questions": [{"IDquestion": 2, "IDcategorie": 1,
                                          "label": "Allergies"}],
            "individus": [{"IDindividu": 10, "nom": "Alice"}],
            "questionnaire_reponses": [{"IDreponse": 20, "IDquestion": 2,
                                         "IDindividu": 10, "IDfamille": None,
                                         "reponse": "Aucune", "type": "individu",
                                         "IDdonnee": 10}],
        }
        source, cible = DBFactice(schema, lignes), DBFactice(schema)
        moteur = migration.MoteurMigration(source, cible, tables="dossiers")
        resultat = moteur.Executer()
        self.assertTrue(resultat["succes"], resultat)
        reponse = next(donnees for table, donnees, _commit, _id in cible.insertions
                       if table == "questionnaire_reponses")
        nouvel_individu = moteur.mapping.Get("individus", 10)
        self.assertEqual(reponse["IDindividu"], nouvel_individu)
        self.assertEqual(reponse["IDdonnee"], nouvel_individu)
        self.assertEqual(reponse["IDquestion"], moteur.mapping.Get("questionnaire_questions", 2))

    def test_reference_polymorphe_externe_reste_bloquee_hors_perimetre(self):
        schema = {
            "questionnaire_categories": ["IDcategorie", "nom"],
            "questionnaire_questions": ["IDquestion", "IDcategorie", "label"],
            "questionnaire_reponses": ["IDreponse", "IDquestion", "IDindividu",
                                        "IDfamille", "reponse", "type", "IDdonnee"],
        }
        lignes = {
            "questionnaire_categories": [{"IDcategorie": 1, "nom": "Location"}],
            "questionnaire_questions": [{"IDquestion": 2, "IDcategorie": 1,
                                          "label": "Etat"}],
            "questionnaire_reponses": [{"IDreponse": 20, "IDquestion": 2,
                                         "IDindividu": None, "IDfamille": None,
                                         "reponse": "Bon", "type": "location",
                                         "IDdonnee": 77}],
        }
        source, cible = DBFactice(schema, lignes), DBFactice(schema)
        simulation = migration.MoteurMigration(source, cible, tables="dossiers").Simuler()
        self.assertFalse(simulation["pret"])
        self.assertEqual(cible.insertions, [])
        self.assertTrue(any(erreur.get("erreur") == "reference_hors_perimetre"
                            and erreur.get("type") == "location"
                            for erreur in simulation["erreurs"]))

    def test_ancien_schema_sans_champs_polymorphes_reste_compatible(self):
        schema = {
            "questionnaire_categories": ["IDcategorie", "nom"],
            "questionnaire_questions": ["IDquestion", "IDcategorie", "label"],
            "individus": ["IDindividu", "nom"],
            "questionnaire_reponses": ["IDreponse", "IDquestion", "IDindividu",
                                        "IDfamille", "reponse"],
        }
        lignes = {
            "questionnaire_categories": [{"IDcategorie": 1, "nom": "Identite"}],
            "questionnaire_questions": [{"IDquestion": 2, "IDcategorie": 1,
                                          "label": "Allergies"}],
            "individus": [{"IDindividu": 10, "nom": "Alice"}],
            "questionnaire_reponses": [{"IDreponse": 20, "IDquestion": 2,
                                         "IDindividu": 10, "IDfamille": None,
                                         "reponse": "Aucune"}],
        }
        source, cible = DBFactice(schema, lignes), DBFactice(schema)
        simulation = migration.MoteurMigration(source, cible, tables="dossiers").Simuler()
        self.assertTrue(simulation["pret"], simulation)
        self.assertEqual(cible.insertions, [])


if __name__ == "__main__":
    unittest.main()
