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


class FakeSchemaDB(object):
    def __init__(self, tables=None):
        self.tables = dict(tables or {})
        self.creations = []
        self.commits = 0

    def IsTableExists(self, nom_table):
        return nom_table in self.tables

    def GetListeChamps2(self, nom_table):
        return [(champ, "TEXT") for champ in self.tables[nom_table]]

    def CreationTable(self, nom_table, dico):
        self.creations.append(nom_table)
        self.tables[nom_table] = [champ[0] for champ in dico[nom_table]]

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
    assert db.tables["structures"] == [champ[0] for champ in DATA.DB_STRUCTURES["structures"]]


def test_activation_est_idempotente():
    tables = {
        "structures": [champ[0] for champ in DATA.DB_STRUCTURES["structures"]],
        "structures_contacts": [champ[0] for champ in DATA.DB_STRUCTURES["structures_contacts"]],
    }
    db = FakeSchemaDB(tables=tables)
    resultat = SCHEMA.AssurerSchema(db, appliquer=True)
    assert resultat["ok"] is True
    assert resultat["tables_creees"] == ()
    assert db.creations == []
    assert db.commits == 0


def test_table_existante_incomplete_n_est_jamais_modifiee_silencieusement():
    tables = {
        "structures": ["IDstructure", "nom"],
        "structures_contacts": [champ[0] for champ in DATA.DB_STRUCTURES["structures_contacts"]],
    }
    db = FakeSchemaDB(tables=tables)
    resultat = SCHEMA.AssurerSchema(db, appliquer=True)
    assert resultat["ok"] is False
    assert resultat["tables_incoherentes"] == ("structures",)
    assert "uid" in resultat["rapport"]["structures"]["champs_manquants"]
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
