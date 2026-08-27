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


SCHEMA = _charger_module("noethys/Utils/UTILS_Tiers_Schema.py", "UTILS_Tiers_Schema_noe062b")
INTERVENTIONS = _charger_module("noethys/Utils/UTILS_Interventions.py", "UTILS_Interventions_noe062b")


class SQLiteDB(object):
    """Petit adaptateur du contrat GestionDB utilisé par le métier 062B."""
    isNetwork = False

    def __init__(self):
        self.connexion = sqlite3.connect(":memory:")
        self.cursor = self.connexion.cursor()
        self.creations = []
        self.commits = 0
        self.fail_insert_table = None
        self.fail_update_table = None

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
        if self.fail_insert_table == nom_table:
            return None
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
        if self.fail_update_table == nom_table:
            return False
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
    resultat = SCHEMA.AssurerSchema062B(db, appliquer=True)
    assert resultat["ok"] is True
    db.cursor.execute(
        "CREATE TABLE ecoles (IDecole INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, rue TEXT, cp TEXT, ville TEXT, tel TEXT, mail TEXT)"
    )
    db.cursor.execute(
        "INSERT INTO ecoles (nom, rue, cp, ville, tel, mail) VALUES (?, ?, ?, ?, ?, ?)",
        ("École Jean-Moulin", "1 rue des Écoles", "35130", "La Guerche-de-Bretagne", "0200000000", "ecole@example.fr"),
    )
    db.connexion.commit()
    return db


class Noe062BInterventionsTests(unittest.TestCase):

    def test_schema_062b_est_additif_et_idempotent(self):
        db = SQLiteDB()
        try:
            resultat = SCHEMA.AssurerSchema062B(db, appliquer=True)
            self.assertTrue(resultat["ok"])
            self.assertEqual(resultat["tables_creees"], ("structures", "structures_contacts", "interventions"))
            self.assertEqual(set(db.creations), {"structures", "structures_contacts", "interventions"})

            creations = list(db.creations)
            resultat2 = SCHEMA.AssurerSchema062B(db, appliquer=True)
            self.assertTrue(resultat2["ok"])
            self.assertEqual(resultat2["tables_creees"], ())
            self.assertEqual(db.creations, creations)
        finally:
            db.Close()

    def test_ecole_historique_devient_un_tiers_ecole_sans_perdre_sa_denomination(self):
        db = _db_pret()
        try:
            service = INTERVENTIONS.GestionnaireInterventions(db)
            ecole = service.SynchroniserEcoleHistorique(1)
            self.assertEqual(ecole["type_structure"], "ecole")
            self.assertEqual(ecole["nom"], "École Jean-Moulin")
            self.assertEqual(ecole["uid"], "ECOLE-NOETHYS-1")

            # Une seconde synchronisation met à jour la même fiche, sans doublon.
            db.cursor.execute("UPDATE ecoles SET nom=? WHERE IDecole=1", ("École Jean-Moulin - Centre",))
            db.connexion.commit()
            ecole2 = service.SynchroniserEcoleHistorique(1)
            self.assertEqual(ecole2["IDstructure"], ecole["IDstructure"])
            self.assertEqual(ecole2["nom"], "École Jean-Moulin - Centre")
            self.assertEqual(len(service.tiers.ListerStructures(actifs_seulement=False)), 1)
        finally:
            db.Close()

    def test_enregistrer_une_seance_sport_ecole_calcule_la_duree_et_restitue_le_nom(self):
        db = _db_pret()
        try:
            service = INTERVENTIONS.GestionnaireInterventions(db)
            ecole = service.SynchroniserEcoleHistorique(1)
            IDseance = service.CreerSeanceSportEcole(
                ecole["IDstructure"],
                "04/09/2026",
                "09:00",
                "10:30",
                libelle="EPS - cycle athlétisme",
            )
            self.assertTrue(IDseance)

            seances = service.ListerSeancesSportEcole(ecole["IDstructure"])
            self.assertEqual(len(seances), 1)
            self.assertEqual(seances[0]["nom_ecole"], "École Jean-Moulin")
            self.assertEqual(seances[0]["duree_minutes"], 90)
            self.assertEqual(seances[0]["date"], "2026-09-04")
            self.assertEqual(seances[0]["libelle"], "EPS - cycle athlétisme")
        finally:
            db.Close()

    def test_horaire_incoherent_est_refuse_avant_ecriture(self):
        db = _db_pret()
        try:
            service = INTERVENTIONS.GestionnaireInterventions(db)
            ecole = service.SynchroniserEcoleHistorique(1)
            with self.assertRaises(ValueError):
                service.CreerSeanceSportEcole(ecole["IDstructure"], "04/09/2026", "10:30", "09:00")
            self.assertEqual(service.ListerSeancesSportEcole(ecole["IDstructure"]), [])
        finally:
            db.Close()

    def test_date_videe_est_refusee_au_lieu_de_devenir_aujourdhui(self):
        db = _db_pret()
        try:
            service = INTERVENTIONS.GestionnaireInterventions(db)
            ecole = service.SynchroniserEcoleHistorique(1)
            with self.assertRaises(ValueError):
                service.CreerSeanceSportEcole(ecole["IDstructure"], "", "09:00", "10:00")
            self.assertEqual(service.ListerSeancesSportEcole(ecole["IDstructure"]), [])
        finally:
            db.Close()

    def test_echec_insert_est_remonte_comme_erreur_metier(self):
        db = _db_pret()
        try:
            service = INTERVENTIONS.GestionnaireInterventions(db)
            ecole = service.SynchroniserEcoleHistorique(1)
            db.fail_insert_table = "interventions"
            with self.assertRaises(RuntimeError):
                service.CreerSeanceSportEcole(ecole["IDstructure"], "04/09/2026", "09:00", "10:00")
        finally:
            db.Close()

    def test_echec_update_est_remonte_comme_erreur_metier(self):
        db = _db_pret()
        try:
            service = INTERVENTIONS.GestionnaireInterventions(db)
            ecole = service.SynchroniserEcoleHistorique(1)
            IDseance = service.CreerSeanceSportEcole(ecole["IDstructure"], "04/09/2026", "09:00", "10:00")
            db.fail_update_table = "interventions"
            with self.assertRaises(RuntimeError):
                service.ModifierSeanceSport(IDseance, {"notes": "nouvelle note"})
            with self.assertRaises(RuntimeError):
                service.ArchiverSeanceSport(IDseance)
        finally:
            db.Close()

    def test_modification_partielle_et_archivage_ne_detruisent_pas_la_seance(self):
        db = _db_pret()
        try:
            service = INTERVENTIONS.GestionnaireInterventions(db)
            ecole = service.SynchroniserEcoleHistorique(1)
            IDseance = service.CreerSeanceSportEcole(
                ecole["IDstructure"], "04/09/2026", "09:00", "10:30",
                libelle="EPS - cycle athlétisme", notes="Cour de l'école",
            )
            self.assertTrue(service.ModifierSeanceSport(IDseance, {"heure_fin": "11:00"}))
            seance = service.LireIntervention(IDseance)
            self.assertEqual(seance["heure_debut"], "09:00")
            self.assertEqual(seance["heure_fin"], "11:00")
            self.assertEqual(seance["duree_minutes"], 120)
            self.assertEqual(seance["libelle"], "EPS - cycle athlétisme")
            self.assertEqual(seance["notes"], "Cour de l'école")

            self.assertTrue(service.ArchiverSeanceSport(IDseance))
            self.assertEqual(service.ListerSeancesSportEcole(ecole["IDstructure"]), [])
            archivee = service.ListerSeancesSportEcole(ecole["IDstructure"], actifs_seulement=False)
            self.assertEqual(len(archivee), 1)
            self.assertEqual(archivee[0]["libelle"], "EPS - cycle athlétisme")
            self.assertEqual(archivee[0]["actif"], 0)
        finally:
            db.Close()

    def test_filtre_par_periode_ne_retourne_que_les_seances_demandees(self):
        db = _db_pret()
        try:
            service = INTERVENTIONS.GestionnaireInterventions(db)
            ecole = service.SynchroniserEcoleHistorique(1)
            for date in ("2026-09-02", "2026-10-07", "2026-11-04"):
                service.CreerSeanceSportEcole(ecole["IDstructure"], date, "14:00", "15:00")
            seances = service.ListerSeancesSportEcole(
                ecole["IDstructure"], date_debut="01/10/2026", date_fin="31/10/2026"
            )
            self.assertEqual([item["date"] for item in seances], ["2026-10-07"])
        finally:
            db.Close()

    def test_ecole_avec_seance_est_detectee_par_le_garde_de_suppression(self):
        db = _db_pret()
        try:
            self.assertEqual(INTERVENTIONS.CompterInterventionsEcoleHistorique(db, 1), 0)
            service = INTERVENTIONS.GestionnaireInterventions(db)
            ecole = service.SynchroniserEcoleHistorique(1)
            service.CreerSeanceSportEcole(ecole["IDstructure"], "04/09/2026", "09:00", "10:00")
            self.assertEqual(INTERVENTIONS.CompterInterventionsEcoleHistorique(db, 1), 1)
        finally:
            db.Close()

    def test_interface_verifie_les_droits_sur_chaque_mutation(self):
        source = (ROOT / "noethys" / "Dlg" / "DLG_Seances_sport_ecoles.py").read_text(encoding="utf-8")
        self.assertIn('VerificationDroitsUtilisateurActuel("parametrage_ecoles", "creer")', source)
        self.assertIn('VerificationDroitsUtilisateurActuel("parametrage_ecoles", "modifier")', source)
        self.assertIn('VerificationDroitsUtilisateurActuel("parametrage_ecoles", "supprimer")', source)

    def test_gestion_ecoles_bloque_la_suppression_si_des_seances_existent(self):
        source = (ROOT / "noethys" / "Dlg" / "DLG_Ecoles.py").read_text(encoding="utf-8")
        self.assertIn("class ListViewEcoles(OL_Ecoles.ListView)", source)
        self.assertIn("CompterInterventionsEcoleHistorique", source)
        self.assertIn("historique doit rester rattaché", source)


if __name__ == "__main__":
    unittest.main()