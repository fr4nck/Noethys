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


SCHEMA = _charger_module("noethys/Utils/UTILS_Tiers_Schema.py", "UTILS_Tiers_Schema_062b_ref")
TIERS = _charger_module("noethys/Utils/UTILS_Tiers.py", "UTILS_Tiers_062b_ref")


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

    def ReqDEL(self, nom_table, nom_champ_id, ID, commit=True, IDestChaine=False):
        self.cursor.execute(
            "DELETE FROM %s WHERE %s=?" % (nom_table, nom_champ_id),
            (ID,),
        )
        if commit:
            self.connexion.commit()
        return True


class Noe062BReferentielTests(unittest.TestCase):

    def test_contrat_historique_062b_reste_inchange(self):
        self.assertEqual(("interventions",), SCHEMA.TABLES_062B)
        self.assertNotIn("structures_groupes", SCHEMA.TABLES_062B_COMPLET)
        self.assertNotIn("structures_roles_contacts", SCHEMA.TABLES_062B_COMPLET)

    def test_activation_referentiel_est_additive_et_idempotente(self):
        db = SQLiteDB()
        try:
            resultat_a = SCHEMA.AssurerSchema(db, appliquer=True)
            self.assertTrue(resultat_a["ok"])
            self.assertEqual(("structures", "structures_contacts"), resultat_a["tables_creees"])

            resultat = SCHEMA.AssurerSchema062BReferentiel(db, appliquer=True)
            self.assertTrue(resultat["ok"])
            self.assertEqual(
                ("structures_groupes", "structures_roles_contacts"),
                resultat["tables_creees"],
            )
            self.assertFalse(db.IsTableExists("interventions"))

            resultat2 = SCHEMA.AssurerSchema062BReferentiel(db, appliquer=True)
            self.assertTrue(resultat2["ok"])
            self.assertEqual((), resultat2["tables_creees"])
        finally:
            db.Close()

    def test_groupe_libre_est_rattache_archive_sans_suppression(self):
        db = SQLiteDB()
        try:
            SCHEMA.AssurerSchema062BReferentiel(db, appliquer=True)
            gestion = TIERS.GestionnaireTiers(db)
            IDstructure = gestion.CreerStructure({
                "type_structure": "association",
                "nom": "Club test",
            })
            IDgroupe = gestion.CreerGroupe({
                "IDstructure": IDstructure,
                "nom": " Section badminton ",
                "memo": " Mardi ",
            })

            groupe = gestion.LireGroupe(IDgroupe)
            self.assertEqual(IDstructure, groupe["IDstructure"])
            self.assertEqual("Section badminton", groupe["nom"])
            self.assertEqual("Mardi", groupe["memo"])
            self.assertEqual(1, groupe["actif"])

            gestion.ArchiverGroupe(IDgroupe)
            archive = gestion.LireGroupe(IDgroupe)
            self.assertEqual(0, archive["actif"])
            self.assertEqual("Section badminton", archive["nom"])
            self.assertEqual([], gestion.ListerGroupes(IDstructure))
            self.assertEqual(1, len(gestion.ListerGroupes(IDstructure, actifs_seulement=False)))
        finally:
            db.Close()

    def test_contact_peut_cumuler_plusieurs_roles_et_rejeu_est_idempotent(self):
        db = SQLiteDB()
        try:
            SCHEMA.AssurerSchema062BReferentiel(db, appliquer=True)
            gestion = TIERS.GestionnaireTiers(db)
            IDstructure = gestion.CreerStructure({"nom": "École test", "type_structure": "ecole"})
            IDcontact = gestion.CreerContact({
                "IDstructure": IDstructure,
                "nom": "Martin",
                "fonction": "Direction",
            })

            IDplanning = gestion.AjouterRoleContact(IDcontact, "planning")
            IDplanning2 = gestion.AjouterRoleContact(IDcontact, "planning")
            IDfacturation = gestion.AjouterRoleContact(IDcontact, "facturation")

            self.assertEqual(IDplanning, IDplanning2)
            self.assertNotEqual(IDplanning, IDfacturation)
            roles = gestion.ListerRolesContact(IDcontact)
            self.assertEqual(["facturation", "planning"], [item["role"] for item in roles])

            gestion.SupprimerRoleContact(IDplanning)
            roles_apres = gestion.ListerRolesContact(IDcontact)
            self.assertEqual(["facturation"], [item["role"] for item in roles_apres])
            self.assertEqual(1, len(gestion.ListerContacts(IDstructure)))
        finally:
            db.Close()

    def test_vocabulaire_role_est_borne_et_groupe_exige_un_nom(self):
        with self.assertRaises(ValueError):
            TIERS.NormaliserRoleContact({"IDcontact": 1, "role": "super_admin"})
        with self.assertRaises(ValueError):
            TIERS.NormaliserGroupe({"IDstructure": 1, "nom": "   "}, creation=True)


if __name__ == "__main__":
    unittest.main()
