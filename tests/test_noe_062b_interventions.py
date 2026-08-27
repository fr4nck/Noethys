# -*- coding: utf-8 -*-
import importlib.util
import sqlite3
import sys
from pathlib import Path

import pytest


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


def test_schema_062b_est_additif_et_idempotent():
    db = SQLiteDB()
    try:
        resultat = SCHEMA.AssurerSchema062B(db, appliquer=True)
        assert resultat["ok"] is True
        assert resultat["tables_creees"] == ("structures", "structures_contacts", "interventions")
        assert set(db.creations) == {"structures", "structures_contacts", "interventions"}

        creations = list(db.creations)
        resultat2 = SCHEMA.AssurerSchema062B(db, appliquer=True)
        assert resultat2["ok"] is True
        assert resultat2["tables_creees"] == ()
        assert db.creations == creations
    finally:
        db.Close()


def test_ecole_historique_devient_un_tiers_ecole_sans_perdre_sa_denomination():
    db = _db_pret()
    try:
        service = INTERVENTIONS.GestionnaireInterventions(db)
        ecole = service.SynchroniserEcoleHistorique(1)
        assert ecole["type_structure"] == "ecole"
        assert ecole["nom"] == "École Jean-Moulin"
        assert ecole["uid"] == "ECOLE-NOETHYS-1"

        # Une seconde synchronisation met à jour la même fiche, sans doublon.
        db.cursor.execute("UPDATE ecoles SET nom=? WHERE IDecole=1", ("École Jean-Moulin - Centre",))
        db.connexion.commit()
        ecole2 = service.SynchroniserEcoleHistorique(1)
        assert ecole2["IDstructure"] == ecole["IDstructure"]
        assert ecole2["nom"] == "École Jean-Moulin - Centre"
        assert len(service.tiers.ListerStructures(actifs_seulement=False)) == 1
    finally:
        db.Close()


def test_enregistrer_une_seance_sport_ecole_calcule_la_duree_et_restitue_le_nom():
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
        assert IDseance

        seances = service.ListerSeancesSportEcole(ecole["IDstructure"])
        assert len(seances) == 1
        assert seances[0]["nom_ecole"] == "École Jean-Moulin"
        assert seances[0]["duree_minutes"] == 90
        assert seances[0]["date"] == "2026-09-04"
        assert seances[0]["libelle"] == "EPS - cycle athlétisme"
    finally:
        db.Close()


def test_horaire_incoherent_est_refuse_avant_ecriture():
    db = _db_pret()
    try:
        service = INTERVENTIONS.GestionnaireInterventions(db)
        ecole = service.SynchroniserEcoleHistorique(1)
        with pytest.raises(ValueError):
            service.CreerSeanceSportEcole(ecole["IDstructure"], "04/09/2026", "10:30", "09:00")
        assert service.ListerSeancesSportEcole(ecole["IDstructure"]) == []
    finally:
        db.Close()


def test_modification_partielle_et_archivage_ne_detruisent_pas_la_seance():
    db = _db_pret()
    try:
        service = INTERVENTIONS.GestionnaireInterventions(db)
        ecole = service.SynchroniserEcoleHistorique(1)
        IDseance = service.CreerSeanceSportEcole(
            ecole["IDstructure"], "04/09/2026", "09:00", "10:30",
            libelle="EPS - cycle athlétisme", notes="Cour de l'école",
        )
        assert service.ModifierSeanceSport(IDseance, {"heure_fin": "11:00"}) is True
        seance = service.LireIntervention(IDseance)
        assert seance["heure_debut"] == "09:00"
        assert seance["heure_fin"] == "11:00"
        assert seance["duree_minutes"] == 120
        assert seance["libelle"] == "EPS - cycle athlétisme"
        assert seance["notes"] == "Cour de l'école"

        assert service.ArchiverSeanceSport(IDseance) is True
        assert service.ListerSeancesSportEcole(ecole["IDstructure"]) == []
        archivee = service.ListerSeancesSportEcole(ecole["IDstructure"], actifs_seulement=False)
        assert len(archivee) == 1
        assert archivee[0]["libelle"] == "EPS - cycle athlétisme"
        assert archivee[0]["actif"] == 0
    finally:
        db.Close()


def test_filtre_par_periode_ne_retourne_que_les_seances_demandees():
    db = _db_pret()
    try:
        service = INTERVENTIONS.GestionnaireInterventions(db)
        ecole = service.SynchroniserEcoleHistorique(1)
        for date in ("2026-09-02", "2026-10-07", "2026-11-04"):
            service.CreerSeanceSportEcole(ecole["IDstructure"], date, "14:00", "15:00")
        seances = service.ListerSeancesSportEcole(
            ecole["IDstructure"], date_debut="01/10/2026", date_fin="31/10/2026"
        )
        assert [item["date"] for item in seances] == ["2026-10-07"]
    finally:
        db.Close()