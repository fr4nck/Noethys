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


SCHEMA_B = _charger_module("noethys/Utils/UTILS_Tiers_Schema.py", "UTILS_Tiers_Schema_noe062c_base")
SCHEMA_C = _charger_module("noethys/Utils/UTILS_Tiers_Schema062C.py", "UTILS_Tiers_Schema_noe062c")
INTERVENTIONS = _charger_module("noethys/Utils/UTILS_Interventions.py", "UTILS_Interventions_noe062c")
LIEUX = _charger_module("noethys/Utils/UTILS_Lieux.py", "UTILS_Lieux_noe062c")
EXECUTION = _charger_module("noethys/Utils/UTILS_Interventions_Execution.py", "UTILS_Interventions_Execution_noe062c")
SESSIONS = _charger_module("noethys/Utils/UTILS_PMSL_Sessions.py", "UTILS_PMSL_Sessions_noe062c")


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
        self.cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (nom_table,))
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
            "INSERT INTO %s (%s) VALUES (%s)" % (nom_table, ", ".join(noms), marqueurs),
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
            "UPDATE %s SET %s WHERE %s=?" % (nom_table, ", ".join(clauses), nom_champ_id),
            tuple(valeurs),
        )
        if commit:
            self.connexion.commit()
        return True


def _db_pret():
    db = SQLiteDB()
    resultat = SCHEMA_C.AssurerSchema062C(db, appliquer=True)
    assert resultat["ok"] is True
    db.cursor.execute(
        "CREATE TABLE ecoles (IDecole INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, rue TEXT, cp TEXT, ville TEXT, tel TEXT, mail TEXT)"
    )
    db.cursor.execute(
        "INSERT INTO ecoles (nom, rue, cp, ville, tel, mail) VALUES (?, ?, ?, ?, ?, ?)",
        ("École Jean-Moulin", "1 rue des Écoles", "35130", "La Guerche-de-Bretagne", "0200000000", "ecole@example.fr"),
    )
    db.connexion.commit()
    service = INTERVENTIONS.GestionnaireInterventions(db)
    ecole = service.SynchroniserEcoleHistorique(1)
    IDintervention = service.CreerSeanceSportEcole(
        ecole["IDstructure"], "2026-09-04", "09:00", "10:30",
        libelle="EPS - cycle athlétisme", statut="planifiee",
    )
    return db, IDintervention


class Noe062CExecutionTests(unittest.TestCase):

    def test_schema_062c_depuis_base_vide_est_additif_et_idempotent(self):
        db = SQLiteDB()
        try:
            resultat = SCHEMA_C.AssurerSchema062C(db, appliquer=True)
            self.assertTrue(resultat["ok"])
            self.assertEqual(
                resultat["tables_creees"],
                ("structures", "structures_contacts", "interventions", "lieux", "interventions_execution"),
            )
            creations = list(db.creations)
            resultat2 = SCHEMA_C.AssurerSchema062C(db, appliquer=True)
            self.assertTrue(resultat2["ok"])
            self.assertEqual((), resultat2["tables_creees"])
            self.assertEqual(creations, db.creations)
        finally:
            db.Close()

    def test_passage_062b_vers_062c_ne_modifie_pas_le_socle_062b(self):
        db = SQLiteDB()
        try:
            resultat_b = SCHEMA_B.AssurerSchema062B(db, appliquer=True)
            self.assertTrue(resultat_b["ok"])
            self.assertEqual(("structures", "structures_contacts", "interventions"), resultat_b["tables_creees"])
            champs_avant = tuple(row[1] for row in db.cursor.execute("PRAGMA table_info('interventions')").fetchall())

            resultat_c = SCHEMA_C.AssurerSchema062C(db, appliquer=True)
            self.assertTrue(resultat_c["ok"])
            self.assertEqual(("lieux", "interventions_execution"), resultat_c["tables_creees"])
            champs_apres = tuple(row[1] for row in db.cursor.execute("PRAGMA table_info('interventions')").fetchall())
            self.assertEqual(champs_avant, champs_apres)
        finally:
            db.Close()

    def test_lieu_uid_est_stable_et_archivage_non_destructif(self):
        db, IDintervention = _db_pret()
        try:
            lieux = LIEUX.GestionnaireLieux(db)
            IDlieu = lieux.CreerLieu({
                "nom": "Gymnase municipal",
                "type_lieu": "gymnase",
                "ville": "La Guerche-de-Bretagne",
                "latitude": 47.942,
                "longitude": -1.230,
            })
            initial = lieux.LireLieu(IDlieu)
            self.assertTrue(initial["uid"].startswith("LIEU-"))
            self.assertEqual("Gymnase municipal", initial["nom"])

            lieux.ModifierLieu(IDlieu, {"uid": "LIEU-FORCE", "nom": "Gymnase central"})
            modifie = lieux.LireLieu(IDlieu)
            self.assertEqual(initial["uid"], modifie["uid"])
            self.assertEqual("Gymnase central", modifie["nom"])

            lieux.ArchiverLieu(IDlieu)
            archive = lieux.LireLieu(IDlieu)
            self.assertEqual(0, archive["actif"])
            self.assertEqual(initial["uid"], archive["uid"])
        finally:
            db.Close()

    def test_execution_est_unique_par_service_et_rejeu_met_a_jour_la_meme_ligne(self):
        db, IDintervention = _db_pret()
        try:
            lieux = LIEUX.GestionnaireLieux(db)
            IDlieu = lieux.CreerLieu({"nom": "Salle EPS", "type_lieu": "salle"})
            service = EXECUTION.GestionnaireExecutionInterventions(db)
            IDexecution = service.EnregistrerExecution(IDintervention, {
                "UIDintervenant_habituel": "TW-EDUC-001",
                "UIDintervenant_prevu": "TW-EDUC-002",
                "IDlieu_prevu": IDlieu,
            })
            IDexecution2 = service.EnregistrerExecution(IDintervention, {
                "UIDintervenant_reel": "TW-EDUC-003",
                "heure_debut_reelle": "09:05",
                "heure_fin_reelle": "10:35",
                "commentaire_realise": "Remplacement validé terrain",
            })
            self.assertEqual(IDexecution, IDexecution2)
            db.cursor.execute("SELECT COUNT(*) FROM interventions_execution WHERE IDintervention=?", (IDintervention,))
            self.assertEqual(1, db.cursor.fetchone()[0])
            execution = service.LireExecution(IDintervention)
            self.assertEqual("TW-EDUC-002", execution["UIDintervenant_prevu"])
            self.assertEqual("TW-EDUC-003", execution["UIDintervenant_reel"])
            self.assertEqual(90, execution["duree_reelle_minutes"])
        finally:
            db.Close()

    def test_horaire_reel_incoherent_est_refuse_avant_ecriture(self):
        db, IDintervention = _db_pret()
        try:
            service = EXECUTION.GestionnaireExecutionInterventions(db)
            with self.assertRaises(ValueError):
                service.EnregistrerExecution(IDintervention, {
                    "heure_debut_reelle": "10:30",
                    "heure_fin_reelle": "09:00",
                })
            db.cursor.execute("SELECT COUNT(*) FROM interventions_execution")
            self.assertEqual(0, db.cursor.fetchone()[0])
        finally:
            db.Close()

    def test_lieu_inconnu_est_refuse_avant_ecriture(self):
        db, IDintervention = _db_pret()
        try:
            service = EXECUTION.GestionnaireExecutionInterventions(db)
            with self.assertRaises(ValueError):
                service.EnregistrerExecution(IDintervention, {"IDlieu_prevu": 99999})
            db.cursor.execute("SELECT COUNT(*) FROM interventions_execution")
            self.assertEqual(0, db.cursor.fetchone()[0])
        finally:
            db.Close()

    def test_agregat_echange_expose_uid_lieu_et_ne_transforme_pas_prevu_en_reel(self):
        db, IDintervention = _db_pret()
        try:
            lieux = LIEUX.GestionnaireLieux(db)
            IDlieu = lieux.CreerLieu({"nom": "Gymnase A", "type_lieu": "gymnase"})
            lieu = lieux.LireLieu(IDlieu)
            service = EXECUTION.GestionnaireExecutionInterventions(db)
            service.EnregistrerExecution(IDintervention, {
                "UIDintervenant_prevu": "TW-EDUC-010",
                "IDlieu_prevu": IDlieu,
            })
            payload = service.ConstruireInterventionEchange(IDintervention)
            intervention = INTERVENTIONS.GestionnaireInterventions(db).LireIntervention(IDintervention)
            self.assertEqual(intervention["uid"], payload["uid"])
            self.assertEqual("TW-EDUC-010", payload["UIDintervenant_prevu"])
            self.assertIsNone(payload["UIDintervenant_reel"])
            self.assertEqual(lieu["uid"], payload["UIDlieu_prevu"])
            self.assertIsNone(payload["UIDlieu_reel"])
            self.assertNotIn("IDlieu_prevu", payload)
        finally:
            db.Close()

    def test_export_sessions_filtre_par_dates_et_conserve_uid_canonique(self):
        db, IDintervention = _db_pret()
        try:
            intervention = INTERVENTIONS.GestionnaireInterventions(db).LireIntervention(IDintervention)
            export = SESSIONS.PMSLSessionExportService(db)
            lignes = export.build_interventions("2026-09-01", "2026-09-30")
            self.assertEqual(1, len(lignes))
            self.assertEqual(intervention["uid"], lignes[0]["uid"])
            self.assertEqual("2026-09-04", lignes[0]["date"])
            self.assertEqual([], export.build_interventions("2026-10-01", "2026-10-31"))
        finally:
            db.Close()


if __name__ == "__main__":
    unittest.main()
