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


SCHEMA_C = _charger_module("noethys/Utils/UTILS_Tiers_Schema062C.py", "UTILS_Tiers_Schema_noe062_inbox")
SCHEMA_INBOX = _charger_module("noethys/Utils/UTILS_Interventions_Actual_Inbox_Schema.py", "UTILS_Inbox_Schema_noe062")
INBOX = _charger_module("noethys/Utils/UTILS_Interventions_Actual_Inbox.py", "UTILS_Inbox_noe062")
LIEUX = _charger_module("noethys/Utils/UTILS_Lieux.py", "UTILS_Lieux_noe062_inbox")
EXECUTION = _charger_module("noethys/Utils/UTILS_Interventions_Execution.py", "UTILS_Execution_noe062_inbox")


SESSION_UID = "INT-INBOX-SESSION-001"
ACTUAL_UUID = "actual-33333333-3333-3333-3333-333333333333"


class SQLiteDB(object):
    isNetwork = False

    def __init__(self):
        self.connexion = sqlite3.connect(":memory:")
        self.cursor = self.connexion.cursor()
        self.creations = []
        self.commits = 0
        self.rollbacks = 0
        self.fail_intervention_update = False

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

    def Rollback(self):
        self.connexion.rollback()
        self.rollbacks += 1

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
        if self.fail_intervention_update and nom_table == "interventions":
            raise RuntimeError("échec simulé de mise à jour séance")
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
    resultat_inbox = SCHEMA_INBOX.AssurerSchemaInboxRealise(db, appliquer=True)
    assert resultat_inbox["ok"] is True
    db.ReqInsert("interventions", [
        ("uid", SESSION_UID),
        ("nature", "sport"),
        ("date", "2026-09-04"),
        ("heure_debut", "09:00"),
        ("heure_fin", "10:30"),
        ("duree_minutes", 90),
        ("libelle", "EPS - cycle athlétisme"),
        ("statut", "planifiee"),
        ("notes", ""),
        ("actif", 1),
        ("date_creation", "2026-09-01"),
        ("date_modification", "2026-09-01"),
    ])
    return db


def payload_realise(revision=4, **overrides):
    donnees = {
        "contract_version": "session-actual/1",
        "event_type": "session_actual_validated",
        "actual_uuid": ACTUAL_UUID,
        "actual_revision": revision,
        "session_uid": SESSION_UID,
        "session_status": "realisee",
        "assignment_date": "2026-09-04",
        "validated_at": "2026-09-04T10:45:00+00:00",
        "actual_staff_uid": "EMP-11111111-1111-1111-1111-111111111111",
        "actual_place_uid": None,
        "actual_start_time": "09:05",
        "actual_end_time": "10:35",
        "actual_duration_minutes": 90,
        "actual_comment": "RAS",
    }
    donnees.update(overrides)
    return donnees


def payload_annule(revision=5, **overrides):
    donnees = {
        "contract_version": "session-actual/1",
        "event_type": "session_actual_validated",
        "actual_uuid": ACTUAL_UUID,
        "actual_revision": revision,
        "session_uid": SESSION_UID,
        "session_status": "annulee",
        "assignment_date": "2026-09-04",
        "validated_at": "2026-09-04T10:50:00+00:00",
        "actual_staff_uid": None,
        "actual_place_uid": None,
        "actual_start_time": None,
        "actual_end_time": None,
        "actual_duration_minutes": None,
        "actual_comment": "Séance annulée par l'établissement",
    }
    donnees.update(overrides)
    return donnees


class Noe062SessionActualInboxTests(unittest.TestCase):

    def test_schema_inbox_est_additif_explicite_et_idempotent(self):
        db = SQLiteDB()
        try:
            resultat_sans_socle = SCHEMA_INBOX.AssurerSchemaInboxRealise(db, appliquer=True)
            self.assertFalse(resultat_sans_socle["ok"])
            self.assertIn("interventions", resultat_sans_socle["prerequis_absents"])
            self.assertFalse(db.IsTableExists("interventions_execution_inbox"))

            self.assertTrue(SCHEMA_C.AssurerSchema062C(db, appliquer=True)["ok"])
            resultat = SCHEMA_INBOX.AssurerSchemaInboxRealise(db, appliquer=True)
            self.assertTrue(resultat["ok"])
            self.assertEqual(("interventions_execution_inbox",), resultat["tables_creees"])
            creations = list(db.creations)
            resultat2 = SCHEMA_INBOX.AssurerSchemaInboxRealise(db, appliquer=True)
            self.assertTrue(resultat2["ok"])
            self.assertEqual((), resultat2["tables_creees"])
            self.assertEqual(creations, db.creations)
        finally:
            db.Close()

    def test_realise_met_a_jour_la_meme_seance_sans_en_creer(self):
        db = _db_pret()
        try:
            lieux = LIEUX.GestionnaireLieux(db)
            IDlieu = lieux.CreerLieu({"uid": "LIEU-GYMNASE-001", "nom": "Gymnase A", "type_lieu": "gymnase"})
            message = payload_realise(actual_place_uid="LIEU-GYMNASE-001")
            resultat = INBOX.GestionnaireInboxRealise(db).AppliquerMessage(
                message,
                "session-actual:%s:r4:activity_users" % ACTUAL_UUID,
                date_reception="2026-09-04 10:46:00",
            )
            self.assertTrue(resultat["applique"])
            db.cursor.execute("SELECT COUNT(*) FROM interventions")
            self.assertEqual(1, db.cursor.fetchone()[0])
            db.cursor.execute("SELECT statut FROM interventions WHERE uid=?", (SESSION_UID,))
            self.assertEqual("realisee", db.cursor.fetchone()[0])
            db.cursor.execute("SELECT COUNT(*) FROM interventions_execution_inbox")
            self.assertEqual(1, db.cursor.fetchone()[0])
            execution = EXECUTION.GestionnaireExecutionInterventions(db).LireExecution(resultat["IDintervention"])
            self.assertEqual("EMP-11111111-1111-1111-1111-111111111111", execution["UIDintervenant_reel"])
            self.assertEqual(IDlieu, execution["IDlieu_reel"])
            self.assertEqual("09:05", execution["heure_debut_reelle"])
            self.assertEqual("10:35", execution["heure_fin_reelle"])
            self.assertEqual(90, execution["duree_reelle_minutes"])
        finally:
            db.Close()

    def test_rejeu_exact_est_un_noop(self):
        db = _db_pret()
        try:
            service = INBOX.GestionnaireInboxRealise(db)
            cle = "session-actual:%s:r4:activity_users" % ACTUAL_UUID
            premier = service.AppliquerMessage(payload_realise(), cle, date_reception="2026-09-04 10:46:00")
            second = service.AppliquerMessage(payload_realise(), cle, date_reception="2026-09-04 10:47:00")
            self.assertTrue(premier["applique"])
            self.assertTrue(second["replay"])
            self.assertFalse(second["applique"])
            db.cursor.execute("SELECT COUNT(*) FROM interventions_execution_inbox")
            self.assertEqual(1, db.cursor.fetchone()[0])
            db.cursor.execute("SELECT COUNT(*) FROM interventions_execution")
            self.assertEqual(1, db.cursor.fetchone()[0])
        finally:
            db.Close()

    def test_meme_cle_avec_payload_different_est_un_conflit(self):
        db = _db_pret()
        try:
            service = INBOX.GestionnaireInboxRealise(db)
            cle = "session-actual:%s:r4:activity_users" % ACTUAL_UUID
            service.AppliquerMessage(payload_realise(), cle, date_reception="2026-09-04 10:46:00")
            with self.assertRaisesRegex(INBOX.ActualInboxError, "payload différent"):
                service.AppliquerMessage(
                    payload_realise(actual_comment="payload divergent"),
                    cle,
                    date_reception="2026-09-04 10:47:00",
                )
        finally:
            db.Close()

    def test_meme_revision_avec_autre_payload_est_un_conflit(self):
        db = _db_pret()
        try:
            service = INBOX.GestionnaireInboxRealise(db)
            service.AppliquerMessage(
                payload_realise(), "message-A", date_reception="2026-09-04 10:46:00"
            )
            with self.assertRaisesRegex(INBOX.ActualInboxError, "même révision"):
                service.AppliquerMessage(
                    payload_realise(actual_comment="divergent"),
                    "message-B",
                    date_reception="2026-09-04 10:47:00",
                )
            db.cursor.execute("SELECT COUNT(*) FROM interventions_execution_inbox")
            self.assertEqual(1, db.cursor.fetchone()[0])
        finally:
            db.Close()

    def test_revision_plus_ancienne_est_refusee(self):
        db = _db_pret()
        try:
            service = INBOX.GestionnaireInboxRealise(db)
            service.AppliquerMessage(
                payload_realise(revision=5), "message-r5", date_reception="2026-09-04 10:46:00"
            )
            with self.assertRaisesRegex(INBOX.ActualInboxError, "obsolète"):
                service.AppliquerMessage(
                    payload_realise(revision=4), "message-r4", date_reception="2026-09-04 10:47:00"
                )
        finally:
            db.Close()

    def test_revision_suivante_annulee_efface_tout_le_reel(self):
        db = _db_pret()
        try:
            service = INBOX.GestionnaireInboxRealise(db)
            lieux = LIEUX.GestionnaireLieux(db)
            lieux.CreerLieu({"uid": "LIEU-GYMNASE-001", "nom": "Gymnase A", "type_lieu": "gymnase"})
            service.AppliquerMessage(
                payload_realise(revision=4, actual_place_uid="LIEU-GYMNASE-001"),
                "message-r4",
                date_reception="2026-09-04 10:46:00",
            )
            service.AppliquerMessage(
                payload_annule(revision=5),
                "message-r5",
                date_reception="2026-09-04 10:51:00",
            )
            db.cursor.execute("SELECT IDintervention, statut FROM interventions WHERE uid=?", (SESSION_UID,))
            IDintervention, statut = db.cursor.fetchone()
            self.assertEqual("annulee", statut)
            execution = EXECUTION.GestionnaireExecutionInterventions(db).LireExecution(IDintervention)
            self.assertIsNone(execution["UIDintervenant_reel"])
            self.assertIsNone(execution["IDlieu_reel"])
            self.assertIsNone(execution["heure_debut_reelle"])
            self.assertIsNone(execution["heure_fin_reelle"])
            self.assertIsNone(execution["duree_reelle_minutes"])
            self.assertEqual("Séance annulée par l'établissement", execution["commentaire_realise"])
        finally:
            db.Close()

    def test_lieu_inconnu_refuse_avant_toute_ecriture(self):
        db = _db_pret()
        try:
            with self.assertRaises((INBOX.ActualInboxError, ValueError)):
                INBOX.GestionnaireInboxRealise(db).AppliquerMessage(
                    payload_realise(actual_place_uid="LIEU-INCONNU"),
                    "message-lieu-inconnu",
                    date_reception="2026-09-04 10:46:00",
                )
            db.cursor.execute("SELECT statut FROM interventions WHERE uid=?", (SESSION_UID,))
            self.assertEqual("planifiee", db.cursor.fetchone()[0])
            db.cursor.execute("SELECT COUNT(*) FROM interventions_execution")
            self.assertEqual(0, db.cursor.fetchone()[0])
            db.cursor.execute("SELECT COUNT(*) FROM interventions_execution_inbox")
            self.assertEqual(0, db.cursor.fetchone()[0])
        finally:
            db.Close()

    def test_seance_absente_n_est_jamais_creee(self):
        db = _db_pret()
        try:
            message = payload_realise(session_uid="INT-ABSENTE")
            with self.assertRaisesRegex(INBOX.ActualInboxError, "aucune création implicite"):
                INBOX.GestionnaireInboxRealise(db).AppliquerMessage(
                    message, "message-absent", date_reception="2026-09-04 10:46:00"
                )
            db.cursor.execute("SELECT COUNT(*) FROM interventions")
            self.assertEqual(1, db.cursor.fetchone()[0])
            db.cursor.execute("SELECT COUNT(*) FROM interventions_execution_inbox")
            self.assertEqual(0, db.cursor.fetchone()[0])
        finally:
            db.Close()

    def test_duree_incoherente_est_refusee_avant_ecriture(self):
        db = _db_pret()
        try:
            with self.assertRaisesRegex(INBOX.ActualInboxError, "durée réelle incohérente"):
                INBOX.GestionnaireInboxRealise(db).AppliquerMessage(
                    payload_realise(actual_duration_minutes=91),
                    "message-duree",
                    date_reception="2026-09-04 10:46:00",
                )
            db.cursor.execute("SELECT COUNT(*) FROM interventions_execution_inbox")
            self.assertEqual(0, db.cursor.fetchone()[0])
        finally:
            db.Close()

    def test_echec_apres_insertion_inbox_provoque_un_rollback_integral(self):
        db = _db_pret()
        try:
            db.fail_intervention_update = True
            with self.assertRaises(RuntimeError):
                INBOX.GestionnaireInboxRealise(db).AppliquerMessage(
                    payload_realise(), "message-rollback", date_reception="2026-09-04 10:46:00"
                )
            self.assertGreaterEqual(db.rollbacks, 1)
            db.cursor.execute("SELECT COUNT(*) FROM interventions_execution_inbox")
            self.assertEqual(0, db.cursor.fetchone()[0])
            db.cursor.execute("SELECT COUNT(*) FROM interventions_execution")
            self.assertEqual(0, db.cursor.fetchone()[0])
            db.cursor.execute("SELECT statut FROM interventions WHERE uid=?", (SESSION_UID,))
            self.assertEqual("planifiee", db.cursor.fetchone()[0])
        finally:
            db.Close()

    def test_vocabulaire_de_domaine_est_independant_des_noms_de_produits(self):
        db = _db_pret()
        try:
            service = INBOX.GestionnaireInboxRealise(db)
            with self.assertRaisesRegex(INBOX.ActualInboxError, "domaine source"):
                service.AppliquerMessage(
                    payload_realise(), "message-produit", source_domain="portail",
                    date_reception="2026-09-04 10:46:00",
                )
            self.assertEqual("operations_portal", INBOX.SOURCE_DOMAIN)
            self.assertNotIn("noethys", INBOX.SOURCE_DOMAIN.lower())
            self.assertNotIn("teamworks", INBOX.SOURCE_DOMAIN.lower())
        finally:
            db.Close()


if __name__ == "__main__":
    unittest.main()
