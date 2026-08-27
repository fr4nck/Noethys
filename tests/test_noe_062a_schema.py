# -*- coding: utf-8 -*-
import importlib.util
import sqlite3
import sys
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


SCHEMA = _charger_module("noethys/Utils/UTILS_Tiers_Schema.py", "UTILS_Tiers_Schema_noe062a")
DATA = _charger_module("noethys/Data/DATA_Structures.py", "DATA_Structures_noe062a_schema")


def _schema_sqlite(nom_table):
    resultat = []
    for nom, type_champ, info in DATA.DB_STRUCTURES[nom_table]:
        type_sql = type_champ
        if type_sql == "LONGBLOB":
            type_sql = "BLOB"
        if type_sql == "BIGINT":
            type_sql = "INTEGER"
        type_prag = type_sql.split(" PRIMARY KEY", 1)[0]
        pk = 1 if "PRIMARY KEY" in type_sql else 0
        resultat.append((nom, type_prag, pk))
    return resultat


class FakeSchemaDB(object):
    isNetwork = False

    def __init__(self, tables=None):
        self.tables = dict(tables or {})
        self.creations = []
        self.commits = 0
        self._resultat = []

    def IsTableExists(self, nom_table):
        return nom_table in self.tables

    def ExecuterReq(self, req):
        if req.startswith("PRAGMA table_info('"):
            nom_table = req.split("'", 2)[1]
            colonnes = self.tables.get(nom_table, [])
            self._resultat = [
                (index, nom, type_sql, 0, None, pk)
                for index, (nom, type_sql, pk) in enumerate(colonnes)
            ]
            return 1
        return 0

    def ResultatReq(self):
        return list(self._resultat)

    def CreationTable(self, nom_table, dico):
        self.creations.append(nom_table)
        self.tables[nom_table] = _schema_sqlite(nom_table)

    def Commit(self):
        self.commits += 1


def test_inspection_est_strictement_lecture_seule():
    db = FakeSchemaDB()
    rapport = SCHEMA.InspecterSchema(db)
    assert rapport["structures"]["existe"] is False
    assert rapport["structures_contacts"]["existe"] is False
    assert db.creations == []
    assert db.commits == 0


def test_mode_diagnostic_ne_cree_rien():
    db = FakeSchemaDB()
    resultat = SCHEMA.AssurerSchema(db, appliquer=False)
    assert resultat["ok"] is True
    assert resultat["tables_creees"] == ()
    assert set(resultat["tables_absentes"]) == {"structures", "structures_contacts"}
    assert db.creations == []


def test_activation_cree_uniquement_les_deux_tables_062a():
    db = FakeSchemaDB()
    resultat = SCHEMA.AssurerSchema(db, appliquer=True)
    assert resultat["ok"] is True
    assert resultat["tables_creees"] == ("structures", "structures_contacts")
    assert db.creations == ["structures", "structures_contacts"]
    assert db.commits == 2
    assert set(db.tables) == {"structures", "structures_contacts"}
    assert [champ[0] for champ in db.tables["structures"]] == [champ[0] for champ in DATA.DB_STRUCTURES["structures"]]


def test_activation_est_idempotente():
    tables = {
        "structures": _schema_sqlite("structures"),
        "structures_contacts": _schema_sqlite("structures_contacts"),
    }
    db = FakeSchemaDB(tables=tables)
    resultat = SCHEMA.AssurerSchema(db, appliquer=True)
    assert resultat["ok"] is True
    assert resultat["tables_creees"] == ()
    assert db.creations == []
    assert db.commits == 0


def test_table_existante_incomplete_n_est_jamais_modifiee_silencieusement():
    tables = {
        "structures": [("IDstructure", "INTEGER", 1), ("nom", "VARCHAR(300)", 0)],
        "structures_contacts": _schema_sqlite("structures_contacts"),
    }
    db = FakeSchemaDB(tables=tables)
    resultat = SCHEMA.AssurerSchema(db, appliquer=True)
    assert resultat["ok"] is False
    assert resultat["tables_incoherentes"] == ("structures",)
    assert "uid" in resultat["rapport"]["structures"]["champs_manquants"]
    assert db.creations == []
    assert db.commits == 0


def test_mauvais_type_de_cle_primaire_est_incompatible():
    structures = _schema_sqlite("structures")
    structures[0] = ("IDstructure", "TEXT", 1)
    db = FakeSchemaDB({
        "structures": structures,
        "structures_contacts": _schema_sqlite("structures_contacts"),
    })
    resultat = SCHEMA.AssurerSchema(db, appliquer=False)
    assert resultat["ok"] is False
    assert "IDstructure" in resultat["rapport"]["structures"]["champs_incompatibles"]


def test_absence_de_cle_primaire_est_incompatible():
    structures = _schema_sqlite("structures")
    structures[0] = ("IDstructure", "INTEGER", 0)
    db = FakeSchemaDB({
        "structures": structures,
        "structures_contacts": _schema_sqlite("structures_contacts"),
    })
    resultat = SCHEMA.AssurerSchema(db, appliquer=False)
    assert resultat["ok"] is False
    assert "IDstructure" in resultat["rapport"]["structures"]["champs_incompatibles"]


def test_preflight_incoherent_bloque_avant_creation_d_une_table_absente():
    db = FakeSchemaDB({
        "structures": [("IDstructure", "INTEGER", 1), ("nom", "VARCHAR(300)", 0)],
    })
    resultat = SCHEMA.AssurerSchema(db, appliquer=True)
    assert resultat["ok"] is False
    assert resultat["tables_incoherentes"] == ("structures",)
    assert resultat["tables_absentes"] == ("structures_contacts",)
    assert db.creations == []
    assert db.commits == 0


def test_contrat_062a_est_executable_par_sqlite():
    connexion = sqlite3.connect(":memory:")
    try:
        curseur = connexion.cursor()
        for nom_table in SCHEMA.TABLES_062A:
            champs = ", ".join("%s %s" % (nom, type_champ) for nom, type_champ, info in DATA.DB_STRUCTURES[nom_table])
            curseur.execute("CREATE TABLE %s (%s)" % (nom_table, champs))

        curseur.execute(
            "INSERT INTO structures (uid, type_structure, nom, actif) VALUES (?, ?, ?, ?)",
            ("STR-test", "ecole", "Ecole de test", 1),
        )
        IDstructure = curseur.lastrowid
        curseur.execute(
            "INSERT INTO structures_contacts (IDstructure, nom, fonction, actif) VALUES (?, ?, ?, ?)",
            (IDstructure, "Martin", "Direction", 1),
        )
        connexion.commit()

        curseur.execute("SELECT uid, type_structure, nom FROM structures WHERE IDstructure=?", (IDstructure,))
        assert curseur.fetchone() == ("STR-test", "ecole", "Ecole de test")
    finally:
        connexion.close()
