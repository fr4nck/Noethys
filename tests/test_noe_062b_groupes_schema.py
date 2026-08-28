# -*- coding: utf-8 -*-
import importlib.util
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


SCHEMA = _charger_module("noethys/Utils/UTILS_Tiers_Schema.py", "UTILS_Tiers_Schema_noe062b_groupes")
DATA = _charger_module("noethys/Data/DATA_Structures.py", "DATA_Structures_noe062b_groupes_schema")


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


def test_contrat_groupes_est_distinct_du_contrat_interventions():
    assert SCHEMA.TABLES_062B == ("interventions",)
    assert SCHEMA.TABLES_062B_GROUPES == ("structures_groupes",)
    assert "structures_groupes" not in SCHEMA.TABLES_062B_COMPLET
    assert "interventions" not in SCHEMA.TABLES_062B_GROUPES_COMPLET


def test_diagnostic_groupes_ne_cree_rien():
    db = FakeSchemaDB()
    resultat = SCHEMA.AssurerSchema062BGroupes(db, appliquer=False)

    assert resultat["ok"] is True
    assert resultat["tables_creees"] == ()
    assert set(resultat["tables_absentes"]) == {
        "structures",
        "structures_contacts",
        "structures_groupes",
    }
    assert db.creations == []
    assert db.commits == 0


def test_activation_groupes_est_strictement_additive():
    db = FakeSchemaDB({
        "structures": _schema_sqlite("structures"),
        "structures_contacts": _schema_sqlite("structures_contacts"),
    })
    resultat = SCHEMA.AssurerSchema062BGroupes(db, appliquer=True)

    assert resultat["ok"] is True
    assert resultat["tables_creees"] == ("structures_groupes",)
    assert db.creations == ["structures_groupes"]
    assert db.commits == 1
    assert "interventions" not in db.tables


def test_activation_groupes_est_idempotente():
    db = FakeSchemaDB({
        "structures": _schema_sqlite("structures"),
        "structures_contacts": _schema_sqlite("structures_contacts"),
        "structures_groupes": _schema_sqlite("structures_groupes"),
    })
    resultat = SCHEMA.AssurerSchema062BGroupes(db, appliquer=True)

    assert resultat["ok"] is True
    assert resultat["tables_creees"] == ()
    assert db.creations == []
    assert db.commits == 0


def test_schema_incoherent_bloque_avant_toute_creation():
    db = FakeSchemaDB({
        "structures": _schema_sqlite("structures"),
        "structures_contacts": _schema_sqlite("structures_contacts"),
        "structures_groupes": [
            ("IDgroupe_structure", "INTEGER", 1),
            ("IDstructure", "INTEGER", 0),
        ],
    })
    resultat = SCHEMA.AssurerSchema062BGroupes(db, appliquer=True)

    assert resultat["ok"] is False
    assert resultat["tables_incoherentes"] == ("structures_groupes",)
    assert "nom" in resultat["rapport"]["structures_groupes"]["champs_manquants"]
    assert db.creations == []
    assert db.commits == 0
