# -*- coding: utf-8 -*-
import datetime
import importlib.util
import sqlite3
import sys
from pathlib import Path

import unittest


def _raises(exception, match=None):
    return unittest.TestCase().assertRaisesRegex(exception, match or ".*")


ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))


def _charger(path, nom):
    spec = importlib.util.spec_from_file_location(nom, str(ROOT / path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DATA = _charger("noethys/Data/DATA_Structures.py", "DATA_Structures_mat")
DATA_PROG = _charger("noethys/Data/DATA_Programmations_Structures.py", "DATA_Prog_mat")
DATA_LIENS = _charger("noethys/Data/DATA_Programmations_Interventions.py", "DATA_Liens_mat")
SCHEMA = _charger("noethys/Utils/UTILS_Programmations_Interventions_Schema.py", "Schema_mat")
MAT = _charger("noethys/Utils/UTILS_Programmations_Interventions.py", "Materialisation_mat")


class SQLiteDB(object):
    isNetwork = False

    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self._resultat = []
        self.creations = []
        self.commits = 0
        self.rollbacks = 0
        self.echec_table = None

    def IsTableExists(self, nom):
        cur = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (nom,)
        )
        return cur.fetchone() is not None

    def ExecuterReq(self, req):
        try:
            cur = self.conn.execute(req)
            self._resultat = cur.fetchall()
            return 1
        except sqlite3.Error:
            self._resultat = []
            return 0

    def ResultatReq(self):
        return list(self._resultat)

    def CreationTable(self, nom, dico):
        champs = []
        for champ, type_sql, info in dico[nom]:
            if type_sql == "LONGBLOB":
                type_sql = "BLOB"
            elif type_sql == "BIGINT":
                type_sql = "INTEGER"
            champs.append("%s %s" % (champ, type_sql))
        self.conn.execute("CREATE TABLE %s (%s)" % (nom, ", ".join(champs)))
        self.creations.append(nom)

    def Commit(self):
        self.conn.commit()
        self.commits += 1

    def Rollback(self):
        self.conn.rollback()
        self.rollbacks += 1

    def ReqInsert(self, table, donnees, commit=True):
        if self.echec_table == table:
            raise RuntimeError("échec injecté sur %s" % table)
        donnees = list(donnees)
        champs = [x[0] for x in donnees]
        valeurs = [x[1] for x in donnees]
        cur = self.conn.execute(
            "INSERT INTO %s (%s) VALUES (%s)" % (
                table, ", ".join(champs), ", ".join(["?"] * len(champs))
            ),
            valeurs,
        )
        if commit:
            self.conn.commit()
        return cur.lastrowid

    def ReqMAJ(self, table, donnees, cle, ID, IDestChaine=False, commit=True):
        donnees = list(donnees)
        champs = [x[0] for x in donnees]
        valeurs = [x[1] for x in donnees]
        self.conn.execute(
            "UPDATE %s SET %s WHERE %s=?" % (
                table, ", ".join("%s=?" % champ for champ in champs), cle
            ),
            valeurs + [ID],
        )
        if commit:
            self.conn.commit()
        return True


def _creer_table(db, nom, dico):
    db.CreationTable(nom, dico)
    db.Commit()


def _base(avec_lien=True):
    db = SQLiteDB()
    for table in (
        "structures",
        "structures_relations",
        "interventions",
        "interventions_execution",
        "lieux",
    ):
        _creer_table(db, table, DATA.DB_STRUCTURES)
    for table in ("structures_programmations", "structures_programmations_creneaux"):
        _creer_table(db, table, DATA_PROG.DB_PROGRAMMATIONS_STRUCTURES)
    if avec_lien:
        _creer_table(db, "interventions_programmations", DATA_LIENS.DB_PROGRAMMATIONS_INTERVENTIONS)
    db.conn.execute("CREATE TABLE activites (IDactivite INTEGER PRIMARY KEY, nom TEXT)")
    db.conn.execute("INSERT INTO activites VALUES (10, 'École multisport')")
    db.ReqInsert("structures", [
        ("uid", "STR-1"), ("type_structure", "association"),
        ("nom", "Club partenaire"), ("actif", 1),
    ])
    db.ReqInsert("structures_relations", [
        ("uid", "REL-1"), ("IDstructure", 1),
        ("type_relation", "mise_disposition"), ("libelle", "Cycle sport"),
        ("saison", "2026-2027"), ("date_debut", "2026-09-01"),
        ("date_fin", "2027-08-31"), ("actif", 1),
    ])
    return db


def _programme(db, source="relation", uid="PROG-1", staff=None, lieu=None):
    valeurs = [
        ("uid", uid), ("type_source", source),
        ("IDrelation_structure", 1 if source == "relation" else None),
        ("IDactivite", 10 if source == "activite" else None),
        ("IDgroupe_activite", 20 if source == "activite" else None),
        ("IDprogrammation_parent", None), ("saison", "2026-2027"),
        ("libelle", "Programmation test"), ("statut", "validee"),
        ("date_debut", "2026-09-07"), ("date_fin", "2026-09-21"),
        ("UIDintervenant_habituel", staff), ("IDlieu_habituel", lieu),
        ("actif", 1), ("memo", ""),
        ("date_creation", "2026-09-01"), ("date_modification", "2026-09-01"),
    ]
    IDprog = db.ReqInsert("structures_programmations", valeurs)
    db.ReqInsert("structures_programmations_creneaux", [
        ("uid", "CREN-%s" % uid),
        ("IDprogrammation_structure", IDprog), ("IDcreneau_source", None),
        ("jour_semaine", 0), ("heure_debut", "10:00"), ("heure_fin", "11:00"),
        ("date_debut", None), ("date_fin", None),
        ("appliquer_scolaire", 1), ("appliquer_vacances", 0),
        ("inclure_feries", 0), ("frequence", 1), ("IDlieu", None),
        ("groupe", "Groupe A"), ("observations", ""),
        ("etat_renouvellement", "ajoute"), ("actif", 1),
        ("date_creation", "2026-09-01"), ("date_modification", "2026-09-01"),
    ])
    return IDprog


def _calendrier():
    return ([], [])


def _compter(db, table):
    return db.conn.execute("SELECT COUNT(*) FROM %s" % table).fetchone()[0]


def test_schema_additif_et_idempotent():
    db = _base(avec_lien=False)
    rapport = SCHEMA.AssurerSchemaMaterialisation(db, appliquer=False)
    assert rapport["ok"] is True
    assert not db.IsTableExists("interventions_programmations")
    rapport = SCHEMA.AssurerSchemaMaterialisation(db, appliquer=True)
    assert rapport["ok"] is True
    assert rapport["tables_creees"] == ("interventions_programmations",)
    rapport2 = SCHEMA.AssurerSchemaMaterialisation(db, appliquer=True)
    assert rapport2["ok"] is True
    assert rapport2["tables_creees"] == ()


def test_schema_refuse_table_experimentale_incomplete():
    db = _base(avec_lien=False)
    db.conn.execute("CREATE TABLE interventions_programmations (IDintervention_programmation INTEGER PRIMARY KEY)")
    rapport = SCHEMA.AssurerSchemaMaterialisation(db, appliquer=True)
    assert rapport["ok"] is False
    assert "interventions_programmations" in rapport["tables_incoherentes"]


def test_preview_programme_non_valide_refuse():
    db = _base()
    IDprog = _programme(db)
    db.conn.execute("UPDATE structures_programmations SET statut='brouillon' WHERE IDprogrammation_structure=?", (IDprog,))
    with _raises(ValueError, match="validée"):
        MAT.GestionnaireMaterialisationProgrammations(db).Previsualiser(IDprog, calendrier=_calendrier())


def test_relation_preview_puis_apply_idempotent():
    db = _base()
    IDprog = _programme(db)
    service = MAT.GestionnaireMaterialisationProgrammations(db)
    preview = service.Previsualiser(IDprog, calendrier=_calendrier())
    assert preview["applicable"] is True
    assert preview["compteurs"] == {"a_creer": 3}
    uids = [x["desire"]["uid"] for x in preview["lignes"]]
    assert len(set(uids)) == 3
    assert all(uid.startswith("INT-PROG-") for uid in uids)

    resultat = service.Appliquer(IDprog, calendrier=_calendrier(), date="2026-09-01")
    assert resultat["nb_crees"] == 3
    assert _compter(db, "interventions") == 3
    assert _compter(db, "interventions_programmations") == 3

    preview2 = service.Previsualiser(IDprog, calendrier=_calendrier())
    assert preview2["compteurs"] == {"existante": 3}
    resultat2 = service.Appliquer(IDprog, calendrier=_calendrier(), date="2026-09-02")
    assert resultat2["nb_crees"] == 0
    assert _compter(db, "interventions") == 3


def test_activite_interne_est_tracee_sans_inventer_structure_relation():
    db = _base()
    IDprog = _programme(db, source="activite", uid="PROG-ACT")
    service = MAT.GestionnaireMaterialisationProgrammations(db)
    service.Appliquer(IDprog, calendrier=_calendrier())
    row = db.conn.execute(
        "SELECT i.IDstructure, i.IDrelation_structure, l.type_source, l.IDactivite, l.IDgroupe_activite "
        "FROM interventions i JOIN interventions_programmations l ON l.IDintervention=i.IDintervention LIMIT 1"
    ).fetchone()
    assert row == (None, None, "activite", 10, 20)


def test_intervenant_et_lieu_habituels_prefill_prevu_sans_reel():
    db = _base()
    db.ReqInsert("lieux", [("uid", "LIEU-1"), ("nom", "Gymnase"), ("actif", 1)])
    IDprog = _programme(db, uid="PROG-PREV", staff="RH-123", lieu=1)
    MAT.GestionnaireMaterialisationProgrammations(db).Appliquer(IDprog, calendrier=_calendrier())
    row = db.conn.execute(
        "SELECT UIDintervenant_habituel, UIDintervenant_prevu, UIDintervenant_reel, "
        "IDlieu_prevu, IDlieu_reel FROM interventions_execution LIMIT 1"
    ).fetchone()
    assert row == ("RH-123", "RH-123", None, 1, None)


def test_seance_realisee_est_protegee_et_jamais_recrite():
    db = _base()
    IDprog = _programme(db)
    service = MAT.GestionnaireMaterialisationProgrammations(db)
    service.Appliquer(IDprog, calendrier=_calendrier())
    IDintervention = db.conn.execute("SELECT IDintervention FROM interventions ORDER BY IDintervention LIMIT 1").fetchone()[0]
    db.conn.execute(
        "UPDATE interventions SET statut='realisee', heure_debut='09:45' WHERE IDintervention=?",
        (IDintervention,),
    )
    db.conn.commit()
    preview = service.Previsualiser(IDprog, calendrier=_calendrier())
    protegee = [x for x in preview["lignes"] if x["etat"] == "protegee"]
    assert len(protegee) == 1
    assert "heure_debut" in protegee[0]["ecarts"]
    assert preview["applicable"] is True
    service.Appliquer(IDprog, calendrier=_calendrier())
    heure = db.conn.execute("SELECT heure_debut FROM interventions WHERE IDintervention=?", (IDintervention,)).fetchone()[0]
    assert heure == "09:45"


def test_derivation_manuelle_sur_planifiee_est_conflit_et_bloque_tout_apply():
    db = _base()
    IDprog = _programme(db)
    service = MAT.GestionnaireMaterialisationProgrammations(db)
    service.Appliquer(IDprog, calendrier=_calendrier())
    IDintervention = db.conn.execute("SELECT IDintervention FROM interventions ORDER BY IDintervention LIMIT 1").fetchone()[0]
    db.conn.execute("UPDATE interventions SET libelle='Modification terrain' WHERE IDintervention=?", (IDintervention,))
    db.conn.commit()
    preview = service.Previsualiser(IDprog, calendrier=_calendrier())
    assert preview["applicable"] is False
    assert any(x["raison"] == "seance_planifiee_divergente" for x in preview["lignes"])
    with _raises(ValueError, match="conflits"):
        service.Appliquer(IDprog, calendrier=_calendrier())


def test_uid_deterministe_non_trace_est_un_conflit_pas_un_rattachement_implicite():
    db = _base()
    IDprog = _programme(db)
    service = MAT.GestionnaireMaterialisationProgrammations(db)
    preview = service.Previsualiser(IDprog, calendrier=_calendrier())
    desire = preview["lignes"][0]["desire"]
    db.ReqInsert("interventions", [
        ("uid", desire["uid"]), ("nature", "autre"), ("date", desire["date"]),
        ("heure_debut", desire["heure_debut"]), ("heure_fin", desire["heure_fin"]),
        ("duree_minutes", desire["duree_minutes"]), ("libelle", "Manuelle"),
        ("statut", "planifiee"), ("actif", 1),
    ])
    preview2 = service.Previsualiser(IDprog, calendrier=_calendrier())
    assert preview2["applicable"] is False
    assert any(x["raison"] == "uid_intervention_non_trace" for x in preview2["lignes"])


def test_rollback_atomique_si_lien_echoue():
    db = _base()
    IDprog = _programme(db)
    db.echec_table = "interventions_programmations"
    service = MAT.GestionnaireMaterialisationProgrammations(db)
    with _raises(RuntimeError, match="échec injecté"):
        service.Appliquer(IDprog, calendrier=_calendrier())
    assert db.rollbacks == 1
    assert _compter(db, "interventions") == 0
    assert _compter(db, "interventions_execution") == 0


def test_occurrence_obsolete_est_signalee_sans_suppression():
    db = _base()
    IDprog = _programme(db)
    service = MAT.GestionnaireMaterialisationProgrammations(db)
    service.Appliquer(IDprog, calendrier=_calendrier())
    # Simulation d'une évolution administrative exceptionnelle d'une règle déjà matérialisée.
    db.conn.execute(
        "UPDATE structures_programmations SET date_fin='2026-09-14' WHERE IDprogrammation_structure=?",
        (IDprog,),
    )
    db.conn.commit()
    preview = service.Previsualiser(IDprog, calendrier=_calendrier())
    assert preview["compteurs"].get("obsolete") == 1
    assert _compter(db, "interventions") == 3


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for nom, fonction in sorted(globals().items()):
        if nom.startswith("test_") and callable(fonction):
            suite.addTest(unittest.FunctionTestCase(fonction, description=nom))
    return suite
