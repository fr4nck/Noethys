# -*- coding: utf-8 -*-
import importlib.util
import sqlite3
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))


def _charger_module(path, nom):
    spec = importlib.util.spec_from_file_location(nom, str(ROOT / path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCHEMA = _charger_module("noethys/Utils/UTILS_Tiers_Schema.py", "UTILS_Tiers_Schema_relations")
TIERS = _charger_module("noethys/Utils/UTILS_Tiers.py", "UTILS_Tiers_relations")
RELATIONS = _charger_module("noethys/Utils/UTILS_Relations_Structures.py", "UTILS_Relations_Structures_test")


class SQLiteDB(object):
    isNetwork = False

    def __init__(self):
        self.connexion = sqlite3.connect(":memory:")
        self.cursor = self.connexion.cursor()
        self.creations = []
        self.commits = 0

    def Close(self):
        self.connexion.close()

    def IsTableExists(self, nom_table):
        self.cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (nom_table,),
        )
        return self.cursor.fetchone() is not None

    def ExecuterReq(self, req):
        try:
            self.cursor.execute(req)
            return 1
        except Exception:
            return 0

    def ResultatReq(self):
        return self.cursor.fetchall()

    def CreationTable(self, nom_table, dico):
        champs = []
        for nom, type_champ, info in dico[nom_table]:
            if type_champ == "LONGBLOB":
                type_champ = "BLOB"
            if type_champ == "BIGINT":
                type_champ = "INTEGER"
            champs.append("%s %s" % (nom, type_champ))
        self.cursor.execute("CREATE TABLE %s (%s)" % (nom_table, ", ".join(champs)))
        self.creations.append(nom_table)

    def Commit(self):
        self.connexion.commit()
        self.commits += 1

    def ReqInsert(self, nom_table, liste_donnees, commit=True):
        noms = [nom for nom, valeur in liste_donnees]
        valeurs = [valeur for nom, valeur in liste_donnees]
        marqueurs = ", ".join("?" for nom in noms)
        self.cursor.execute(
            "INSERT INTO %s (%s) VALUES (%s)" % (
                nom_table,
                ", ".join(noms),
                marqueurs,
            ),
            tuple(valeurs),
        )
        if commit:
            self.connexion.commit()
        return self.cursor.lastrowid

    def ReqMAJ(self, nom_table, liste_donnees, nom_champ_id, ID, IDestChaine=False, commit=True):
        clauses = ["%s=?" % nom for nom, valeur in liste_donnees]
        valeurs = [valeur for nom, valeur in liste_donnees]
        valeurs.append(ID)
        self.cursor.execute(
            "UPDATE %s SET %s WHERE %s=?" % (
                nom_table,
                ", ".join(clauses),
                nom_champ_id,
            ),
            tuple(valeurs),
        )
        if commit:
            self.connexion.commit()
        return True


def _db_pret():
    db = SQLiteDB()
    resultat = SCHEMA.AssurerSchema062Relations(db, appliquer=True)
    assert resultat["ok"] is True
    db.cursor.execute("CREATE TABLE activites (IDactivite INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT)")
    db.cursor.execute("INSERT INTO activites (nom) VALUES ('EPS')")
    db.cursor.execute("CREATE TABLE familles (IDfamille INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT)")
    db.cursor.execute("INSERT INTO familles (nom) VALUES ('Famille test')")
    db.connexion.commit()
    return db


class Noe062RelationsContractuellesTests(unittest.TestCase):

    def test_schema_relations_est_additif_independant_et_idempotent(self):
        db = SQLiteDB()
        try:
            resultat = SCHEMA.AssurerSchema062Relations(db, appliquer=True)
            self.assertTrue(resultat["ok"])
            self.assertEqual(
                (
                    "structures",
                    "structures_contacts",
                    "structures_groupes",
                    "structures_relations",
                    "structures_payeurs",
                ),
                resultat["tables_creees"],
            )
            self.assertFalse(db.IsTableExists("interventions"))
            self.assertFalse(db.IsTableExists("structures_roles_contacts"))

            resultat2 = SCHEMA.AssurerSchema062Relations(db, appliquer=True)
            self.assertTrue(resultat2["ok"])
            self.assertEqual((), resultat2["tables_creees"])
        finally:
            db.Close()

    def test_ancien_schema_relation_incomplet_bloque_avant_toute_creation(self):
        db = SQLiteDB()
        try:
            db.cursor.execute(
                "CREATE TABLE structures_relations (IDrelation_structure INTEGER PRIMARY KEY AUTOINCREMENT, IDstructure INTEGER)"
            )
            db.connexion.commit()
            resultat = SCHEMA.AssurerSchema062Relations(db, appliquer=True)
            self.assertFalse(resultat["ok"])
            self.assertEqual(("structures_relations",), resultat["tables_incoherentes"])
            self.assertIn("uid", resultat["rapport"]["structures_relations"]["champs_manquants"])
            self.assertIn("regle_adhesion", resultat["rapport"]["structures_relations"]["champs_manquants"])
            self.assertFalse(db.IsTableExists("structures_payeurs"))
            self.assertFalse(db.IsTableExists("structures"))
        finally:
            db.Close()

    def test_relation_conserve_uid_beneficiaire_groupe_tarif_et_adhesion(self):
        db = _db_pret()
        try:
            tiers = TIERS.GestionnaireTiers(db)
            IDstructure = tiers.CreerStructure({"type_structure": "ecole", "nom": "École Jean Moulin"})
            IDgroupe = tiers.CreerGroupe({"IDstructure": IDstructure, "nom": "CM1"})
            service = RELATIONS.GestionnaireRelationsStructures(db)
            IDrelation = service.CreerRelation({
                "IDstructure": IDstructure,
                "IDgroupe_structure": IDgroupe,
                "IDactivite": 1,
                "type_relation": "eps",
                "libelle": "Cycle EPS CM1",
                "saison": "2026-2027",
                "date_debut": "2026-09-01",
                "date_fin": "2027-06-30",
                "tarif": "23.00",
                "unite_tarif": "heure",
                "regle_adhesion": "non_applicable",
                "mode_facturation": "trimestriel",
            })
            relation = service.LireRelation(IDrelation)
            self.assertTrue(relation["uid"].startswith("REL-"))
            self.assertEqual(IDstructure, relation["IDstructure"])
            self.assertEqual(IDgroupe, relation["IDgroupe_structure"])
            self.assertEqual("Cycle EPS CM1", relation["libelle"])
            self.assertEqual("2026-2027", relation["saison"])
            self.assertEqual(23.0, relation["tarif"])
            self.assertEqual("non_applicable", relation["regle_adhesion"])

            uid = relation["uid"]
            service.ModifierRelation(IDrelation, {"tarif": "24.50", "uid": "REL-FORCEE"})
            modifiee = service.LireRelation(IDrelation)
            self.assertEqual(uid, modifiee["uid"])
            self.assertEqual(24.5, modifiee["tarif"])
        finally:
            db.Close()

    def test_adhesion_depend_de_la_relation_pas_du_type_de_structure(self):
        db = _db_pret()
        try:
            tiers = TIERS.GestionnaireTiers(db)
            IDstructure = tiers.CreerStructure({"type_structure": "mairie_collectivite", "nom": "Mairie Test"})
            service = RELATIONS.GestionnaireRelationsStructures(db)
            IDs = []
            for libelle, regle in (
                ("Partenariat ALSH", "non_applicable"),
                ("Mise à disposition", "requise"),
            ):
                IDs.append(service.CreerRelation({
                    "IDstructure": IDstructure,
                    "type_relation": "mise_disposition",
                    "libelle": libelle,
                    "regle_adhesion": regle,
                }))
            self.assertEqual("non_applicable", service.LireRelation(IDs[0])["regle_adhesion"])
            self.assertEqual("requise", service.LireRelation(IDs[1])["regle_adhesion"])
        finally:
            db.Close()

    def test_groupe_d_un_autre_beneficiaire_est_refuse_avant_ecriture(self):
        db = _db_pret()
        try:
            tiers = TIERS.GestionnaireTiers(db)
            IDa = tiers.CreerStructure({"nom": "Association A", "type_structure": "association"})
            IDb = tiers.CreerStructure({"nom": "Association B", "type_structure": "association"})
            IDgroupe_b = tiers.CreerGroupe({"IDstructure": IDb, "nom": "Section B"})
            service = RELATIONS.GestionnaireRelationsStructures(db)
            with self.assertRaises(ValueError):
                service.CreerRelation({
                    "IDstructure": IDa,
                    "IDgroupe_structure": IDgroupe_b,
                    "type_relation": "prestation",
                    "libelle": "Prestation impossible",
                })
            db.cursor.execute("SELECT COUNT(*) FROM structures_relations")
            self.assertEqual(0, db.cursor.fetchone()[0])
        finally:
            db.Close()

    def test_payeur_par_defaut_est_le_beneficiaire_sans_ecriture_redondante(self):
        db = _db_pret()
        try:
            tiers = TIERS.GestionnaireTiers(db)
            IDbeneficiaire = tiers.CreerStructure({"nom": "Cap Loisirs", "type_structure": "association"})
            service = RELATIONS.GestionnaireRelationsStructures(db)
            IDrelation = service.CreerRelation({
                "IDstructure": IDbeneficiaire,
                "type_relation": "prestation",
                "libelle": "Gym",
            })
            db.cursor.execute("SELECT COUNT(*) FROM structures_payeurs")
            self.assertEqual(0, db.cursor.fetchone()[0])
            effectifs = service.ListerPayeursEffectifs(IDrelation)
            self.assertEqual(1, len(effectifs))
            self.assertTrue(effectifs[0]["implicite"])
            self.assertEqual(IDbeneficiaire, effectifs[0]["IDstructure_payeur"])
            self.assertEqual(100.0, effectifs[0]["taux_prise_en_charge"])
        finally:
            db.Close()

    def test_payeur_structure_distinct_remplace_le_repli_implicite(self):
        db = _db_pret()
        try:
            tiers = TIERS.GestionnaireTiers(db)
            IDecole = tiers.CreerStructure({"nom": "École Test", "type_structure": "ecole"})
            IDmairie = tiers.CreerStructure({"nom": "Mairie Test", "type_structure": "mairie_collectivite"})
            service = RELATIONS.GestionnaireRelationsStructures(db)
            IDrelation = service.CreerRelation({
                "IDstructure": IDecole,
                "type_relation": "eps",
                "libelle": "EPS école",
            })
            IDpayeur = service.CreerPayeur({
                "IDrelation_structure": IDrelation,
                "type_payeur": "structure",
                "IDstructure_payeur": IDmairie,
                "taux_prise_en_charge": 100,
                "reference": "CONV-2026-01",
            })
            payeurs = service.ListerPayeursEffectifs(IDrelation)
            self.assertEqual(1, len(payeurs))
            self.assertFalse(payeurs[0]["implicite"])
            self.assertEqual(IDpayeur, payeurs[0]["IDpayeur_structure"])
            self.assertEqual(IDmairie, payeurs[0]["IDstructure_payeur"])
        finally:
            db.Close()

    def test_payeur_famille_est_possible_sans_transformer_la_relation_en_activite_famille(self):
        db = _db_pret()
        try:
            tiers = TIERS.GestionnaireTiers(db)
            IDstructure = tiers.CreerStructure({"nom": "Organisme Test", "type_structure": "autre"})
            service = RELATIONS.GestionnaireRelationsStructures(db)
            IDrelation = service.CreerRelation({
                "IDstructure": IDstructure,
                "type_relation": "prestation",
                "libelle": "Prise en charge individuelle",
            })
            service.CreerPayeur({
                "IDrelation_structure": IDrelation,
                "type_payeur": "famille",
                "IDfamille": 1,
                "taux_prise_en_charge": 50,
                "montant_plafond": 150,
            })
            payeur = service.ListerPayeurs(IDrelation)[0]
            self.assertEqual("famille", payeur["type_payeur"])
            self.assertEqual(1, payeur["IDfamille"])
            self.assertIsNone(payeur["IDstructure_payeur"])
        finally:
            db.Close()

    def test_archivage_payeur_est_non_destructif(self):
        db = _db_pret()
        try:
            tiers = TIERS.GestionnaireTiers(db)
            IDbeneficiaire = tiers.CreerStructure({"nom": "Association A", "type_structure": "association"})
            IDpayeur_struct = tiers.CreerStructure({"nom": "Financeur A", "type_structure": "financeur"})
            service = RELATIONS.GestionnaireRelationsStructures(db)
            IDrelation = service.CreerRelation({
                "IDstructure": IDbeneficiaire,
                "type_relation": "prestation",
                "libelle": "Action financée",
            })
            IDpayeur = service.CreerPayeur({
                "IDrelation_structure": IDrelation,
                "type_payeur": "structure",
                "IDstructure_payeur": IDpayeur_struct,
            })
            service.ArchiverPayeur(IDpayeur)
            archive = service.LirePayeur(IDpayeur)
            self.assertEqual(0, archive["actif"])
            self.assertEqual(1, len(service.ListerPayeurs(IDrelation, actifs_seulement=False)))
            self.assertEqual([], service.ListerPayeurs(IDrelation, actifs_seulement=True))
        finally:
            db.Close()

    def test_dates_tarifs_taux_et_vocabulaires_invalides_sont_refuses(self):
        with self.assertRaises(ValueError):
            RELATIONS.NormaliserRelation({
                "IDstructure": 1,
                "type_relation": "prestation",
                "libelle": "Test",
                "date_debut": "2027-06-30",
                "date_fin": "2026-09-01",
            })
        with self.assertRaises(ValueError):
            RELATIONS.NormaliserRelation({
                "IDstructure": 1,
                "type_relation": "prestation",
                "libelle": "Test",
                "tarif": -1,
            })
        with self.assertRaises(ValueError):
            RELATIONS.NormaliserRelation({
                "IDstructure": 1,
                "type_relation": "prestation",
                "libelle": "Test",
                "regle_adhesion": "toujours",
            })
        with self.assertRaises(ValueError):
            RELATIONS.NormaliserPayeur({
                "IDrelation_structure": 1,
                "type_payeur": "structure",
                "IDstructure_payeur": 2,
                "taux_prise_en_charge": 101,
            })


if __name__ == "__main__":
    unittest.main()
