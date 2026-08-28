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


SCHEMA = _charger_module("noethys/Utils/UTILS_Tiers_Schema.py", "UTILS_Tiers_Schema_noe062b_roles")
DATA = _charger_module("noethys/Data/DATA_Structures.py", "DATA_Structures_noe062b_roles")


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


def test_contrat_roles_contacts_est_independant_des_autres_lots_062b():
    assert SCHEMA.TABLES_062B_ROLES_CONTACTS == (
        "structures",
        "structures_contacts",
        "structures_roles_contacts",
    )
    assert "interventions" not in SCHEMA.TABLES_062B_ROLES_CONTACTS
    assert "structures_groupes" not in SCHEMA.TABLES_062B_ROLES_CONTACTS


def test_mode_diagnostic_roles_ne_cree_rien():
    db = FakeSchemaDB()
    resultat = SCHEMA.AssurerSchema062BRolesContacts(db, appliquer=False)

    assert resultat["ok"] is True
    assert set(resultat["tables_absentes"]) == {
        "structures",
        "structures_contacts",
        "structures_roles_contacts",
    }
    assert db.creations == []
    assert db.commits == 0


def test_activation_roles_cree_uniquement_le_socle_necessaire():
    db = FakeSchemaDB()
    resultat = SCHEMA.AssurerSchema062BRolesContacts(db, appliquer=True)

    assert resultat["ok"] is True
    assert resultat["tables_creees"] == (
        "structures",
        "structures_contacts",
        "structures_roles_contacts",
    )
    assert db.creations == list(SCHEMA.TABLES_062B_ROLES_CONTACTS)
    assert db.commits == 3
    assert "interventions" not in db.tables
    assert "structures_groupes" not in db.tables


def test_activation_roles_est_idempotente():
    tables = {
        nom_table: _schema_sqlite(nom_table)
        for nom_table in SCHEMA.TABLES_062B_ROLES_CONTACTS
    }
    db = FakeSchemaDB(tables=tables)

    resultat = SCHEMA.AssurerSchema062BRolesContacts(db, appliquer=True)

    assert resultat["ok"] is True
    assert resultat["tables_creees"] == ()
    assert db.creations == []
    assert db.commits == 0


def test_schema_roles_incomplet_bloque_avant_toute_creation():
    db = FakeSchemaDB({
        "structures_roles_contacts": [
            ("IDrole_contact", "INTEGER", 1),
            ("IDcontact", "INTEGER", 0),
        ],
    })

    resultat = SCHEMA.AssurerSchema062BRolesContacts(db, appliquer=True)

    assert resultat["ok"] is False
    assert resultat["tables_incoherentes"] == ("structures_roles_contacts",)
    assert "role" in resultat["rapport"]["structures_roles_contacts"]["champs_manquants"]
    assert db.creations == []
    assert db.commits == 0
