# -*- coding: utf-8 -*-
import hashlib
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))


def _charger(path, nom):
    spec = importlib.util.spec_from_file_location(nom, str(ROOT / path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DATA = _charger("noethys/Data/DATA_Structures.py", "DATA_Structures_noe062_conv")
DATA_CONV = _charger(
    "noethys/Data/DATA_Conventions_Structures.py", "DATA_Conventions_noe062_conv"
)
SCHEMA = _charger(
    "noethys/Utils/UTILS_Conventions_Structures_Schema.py",
    "UTILS_Conventions_Schema_noe062_conv",
)
CONV = _charger(
    "noethys/Utils/UTILS_Conventions_Structures.py",
    "UTILS_Conventions_noe062_conv",
)
REL = _charger(
    "noethys/Utils/UTILS_Relations_Structures.py",
    "UTILS_Relations_noe062_conv",
)


class SQLiteDB(object):
    isNetwork = False

    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self._resultat = []
        self.creations = []
        self.commits = 0

    def IsTableExists(self, nom_table):
        cur = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (nom_table,)
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

    def CreationTable(self, nom_table, dico):
        champs = []
        for nom, type_sql, info in dico[nom_table]:
            if type_sql == "LONGBLOB":
                type_sql = "BLOB"
            elif type_sql == "BIGINT":
                type_sql = "INTEGER"
            champs.append("%s %s" % (nom, type_sql))
        self.conn.execute("CREATE TABLE %s (%s)" % (nom_table, ", ".join(champs)))
        self.creations.append(nom_table)

    def Commit(self):
        self.conn.commit()
        self.commits += 1

    def ReqInsert(self, table, donnees, commit=True):
        donnees = list(donnees)
        champs = [champ for champ, valeur in donnees]
        valeurs = [valeur for champ, valeur in donnees]
        req = "INSERT INTO %s (%s) VALUES (%s)" % (
            table,
            ", ".join(champs),
            ", ".join(["?"] * len(champs)),
        )
        cur = self.conn.execute(req, valeurs)
        if commit:
            self.conn.commit()
        return cur.lastrowid

    def ReqMAJ(self, table, donnees, cle, ID, IDestChaine=False, commit=True):
        donnees = list(donnees)
        champs = [champ for champ, valeur in donnees]
        valeurs = [valeur for champ, valeur in donnees]
        req = "UPDATE %s SET %s WHERE %s=?" % (
            table,
            ", ".join("%s=?" % champ for champ in champs),
            cle,
        )
        self.conn.execute(req, valeurs + [ID])
        if commit:
            self.conn.commit()
        return True


def _creer_table(db, nom_table):
    db.CreationTable(nom_table, DATA.DB_STRUCTURES)
    db.Commit()


def _preparer_base(avec_conventions=True):
    db = SQLiteDB()
    for table in (
        "structures",
        "structures_groupes",
        "structures_relations",
        "structures_payeurs",
    ):
        _creer_table(db, table)
    if avec_conventions:
        db.CreationTable("structures_conventions", DATA_CONV.DB_CONVENTIONS_STRUCTURES)
        db.Commit()
    db.ReqInsert(
        "structures",
        [
            ("uid", "STR-benef"),
            ("type_structure", "association"),
            ("nom", "Association bénéficiaire"),
            ("actif", 1),
            ("date_creation", "2026-09-01"),
            ("date_modification", "2026-09-01"),
        ],
    )
    return db


def _creer_relation(db, date_fin="2027-08-31"):
    gestion = REL.GestionnaireRelationsStructures(db)
    return gestion.CreerRelation(
        {
            "uid": "REL-2026-001",
            "IDstructure": 1,
            "type_relation": "mise_disposition",
            "libelle": "Encadrement sportif saison 2026-2027",
            "saison": "2026-2027",
            "date_debut": "2026-09-01",
            "date_fin": date_fin,
            "tarif": 44,
            "unite_tarif": "heure",
            "regle_adhesion": "requise",
            "mode_facturation": "mensuel",
        },
        date="2026-09-01",
    )


def _creer_convention_brouillon(db):
    IDrelation = _creer_relation(db)
    gestion = CONV.GestionnaireConventionsStructures(db)
    IDconv = gestion.CreerConvention(
        {
            "uid": "CONV-2026-001",
            "IDrelation_structure": IDrelation,
            "reference": "MAD-2026-001",
            "date_debut": "2026-09-01",
            "date_fin": "2027-08-31",
            "objet": "Mise à disposition d'un éducateur sportif",
        },
        date="2026-09-01",
    )
    return gestion, IDrelation, IDconv


def test_schema_declare_snapshot_et_versionnement():
    champs = DATA_CONV.GetChamps()
    assert champs[0] == "IDconvention_structure"
    for champ in (
        "uid",
        "IDrelation_structure",
        "IDconvention_parent",
        "version",
        "statut",
        "snapshot_contractuel",
        "empreinte_sha256",
        "date_validation",
        "date_signature",
    ):
        assert champ in champs


def test_activation_refuse_relation_absente_sans_ecriture():
    db = SQLiteDB()
    resultat = SCHEMA.AssurerSchemaConventions(db, appliquer=True)
    assert resultat["ok"] is False
    assert resultat["prerequis_absents"] == ("structures_relations",)
    assert db.creations == []


def test_activation_cree_uniquement_conventions_et_est_idempotente():
    db = SQLiteDB()
    _creer_table(db, "structures_relations")
    avant = list(db.creations)
    resultat = SCHEMA.AssurerSchemaConventions(db, appliquer=True)
    assert resultat["ok"] is True
    assert resultat["tables_creees"] == ("structures_conventions",)
    assert db.creations == avant + ["structures_conventions"]

    resultat2 = SCHEMA.AssurerSchemaConventions(db, appliquer=True)
    assert resultat2["ok"] is True
    assert resultat2["tables_creees"] == ()
    assert db.creations == avant + ["structures_conventions"]


def test_schema_conventions_incomplet_bloque_sans_reparation_silencieuse():
    db = SQLiteDB()
    _creer_table(db, "structures_relations")
    db.conn.execute(
        "CREATE TABLE structures_conventions (IDconvention_structure INTEGER PRIMARY KEY AUTOINCREMENT, uid VARCHAR(64))"
    )
    db.conn.commit()
    creations = list(db.creations)
    resultat = SCHEMA.AssurerSchemaConventions(db, appliquer=True)
    assert resultat["ok"] is False
    assert resultat["tables_incoherentes"] == ("structures_conventions",)
    assert "IDrelation_structure" in resultat["rapport"]["structures_conventions"]["champs_manquants"]
    assert db.creations == creations


def test_creation_initiale_est_version_1_et_liee_a_la_relation():
    db = _preparer_base()
    gestion, IDrelation, IDconv = _creer_convention_brouillon(db)
    conv = gestion.LireConvention(IDconv)
    assert conv["uid"] == "CONV-2026-001"
    assert conv["IDrelation_structure"] == IDrelation
    assert conv["IDconvention_parent"] is None
    assert conv["version"] == 1
    assert conv["statut"] == CONV.STATUT_BROUILLON
    assert conv["snapshot_contractuel"] is None


def test_une_seule_version_1_par_relation():
    db = _preparer_base()
    gestion, IDrelation, IDconv = _creer_convention_brouillon(db)
    try:
        gestion.CreerConvention(
            {
                "IDrelation_structure": IDrelation,
                "date_debut": "2026-09-01",
                "date_fin": "2027-08-31",
            }
        )
        assert False, "deuxième version 1 acceptée"
    except ValueError as err:
        assert "initiale existe déjà" in str(err)


def test_brouillon_est_modifiable_sans_changer_son_identite():
    db = _preparer_base()
    gestion, IDrelation, IDconv = _creer_convention_brouillon(db)
    gestion.ModifierConvention(
        IDconv,
        {"objet": "Objet corrigé", "notes": "Préparation bureau"},
        date="2026-09-02",
    )
    conv = gestion.LireConvention(IDconv)
    assert conv["uid"] == "CONV-2026-001"
    assert conv["version"] == 1
    assert conv["objet"] == "Objet corrigé"

    try:
        gestion.ModifierConvention(IDconv, {"version": 8})
        assert False, "version modifiée directement"
    except ValueError:
        pass


def test_validation_fige_relation_payeur_et_sha256():
    db = _preparer_base()
    gestion, IDrelation, IDconv = _creer_convention_brouillon(db)
    assert gestion.ValiderConvention(
        IDconv,
        complements={"contact_convention": {"nom": "Martin", "role": "président"}},
        date="2026-09-03",
    ) is True

    conv = gestion.LireConvention(IDconv)
    assert conv["statut"] == CONV.STATUT_VALIDEE
    assert conv["date_validation"] == "2026-09-03"
    assert conv["empreinte_sha256"] == hashlib.sha256(conv["snapshot_contractuel"]).hexdigest()
    assert gestion.VerifierIntegrite(IDconv) is True

    snapshot = gestion.LireSnapshot(IDconv)
    assert snapshot["schema"] == "noe-062-convention-v1"
    assert snapshot["relation"]["uid"] == "REL-2026-001"
    assert snapshot["relation"]["regle_adhesion"] == "requise"
    assert snapshot["payeurs"][0]["implicite"] is True
    assert snapshot["payeurs"][0]["IDstructure_payeur"] == 1
    assert snapshot["complements"]["contact_convention"]["nom"] == "Martin"


def test_version_validee_ne_peut_plus_etre_modifiee():
    db = _preparer_base()
    gestion, IDrelation, IDconv = _creer_convention_brouillon(db)
    gestion.ValiderConvention(IDconv, date="2026-09-03")
    try:
        gestion.ModifierConvention(IDconv, {"objet": "Réécriture interdite"})
        assert False, "version validée modifiée"
    except ValueError as err:
        assert "figée" in str(err)


def test_snapshot_altere_bloque_signature():
    db = _preparer_base()
    gestion, IDrelation, IDconv = _creer_convention_brouillon(db)
    gestion.ValiderConvention(IDconv, date="2026-09-03")
    db.conn.execute(
        "UPDATE structures_conventions SET snapshot_contractuel=? WHERE IDconvention_structure=?",
        (b'{"altération":true}', IDconv),
    )
    db.conn.commit()
    assert gestion.VerifierIntegrite(IDconv) is False
    try:
        gestion.SignerConvention(IDconv, date="2026-09-04")
        assert False, "signature d'un snapshot altéré acceptée"
    except ValueError as err:
        assert "altéré" in str(err)


def test_signature_preserve_snapshot_et_permet_avenant_v2():
    db = _preparer_base()
    gestion, IDrelation, IDconv = _creer_convention_brouillon(db)
    gestion.ValiderConvention(IDconv, date="2026-09-03")
    avant = gestion.LireConvention(IDconv)["snapshot_contractuel"]
    assert gestion.SignerConvention(IDconv, date="2026-09-05") is True
    parent = gestion.LireConvention(IDconv)
    assert parent["statut"] == CONV.STATUT_SIGNEE
    assert parent["date_signature"] == "2026-09-05"
    assert parent["snapshot_contractuel"] == avant

    IDavenant = gestion.CreerAvenant(
        IDconv,
        {
            "uid": "CONV-2026-001-A1",
            "reference": "MAD-2026-001-A1",
            "date_debut": "2027-01-01",
            "date_fin": "2027-08-31",
            "objet": "Avenant horaires",
        },
        date="2026-12-15",
    )
    avenant = gestion.LireConvention(IDavenant)
    assert avenant["version"] == 2
    assert avenant["IDconvention_parent"] == IDconv
    assert avenant["IDrelation_structure"] == IDrelation
    assert avenant["statut"] == CONV.STATUT_BROUILLON
    assert avenant["snapshot_contractuel"] is None


def test_avenant_refuse_parent_brouillon_ou_annule():
    db = _preparer_base()
    gestion, IDrelation, IDconv = _creer_convention_brouillon(db)
    try:
        gestion.CreerAvenant(IDconv, {"date_debut": "2027-01-01"})
        assert False, "avenant depuis brouillon accepté"
    except ValueError:
        pass
    gestion.AnnulerConvention(IDconv)
    try:
        gestion.CreerAvenant(IDconv, {"date_debut": "2027-01-01"})
        assert False, "avenant depuis convention annulée accepté"
    except ValueError:
        pass


def test_periode_convention_ne_depasse_pas_relation():
    db = _preparer_base()
    IDrelation = _creer_relation(db, date_fin="2027-06-30")
    gestion = CONV.GestionnaireConventionsStructures(db)
    try:
        gestion.CreerConvention(
            {
                "IDrelation_structure": IDrelation,
                "date_debut": "2026-09-01",
                "date_fin": "2027-08-31",
            }
        )
        assert False, "convention hors relation acceptée"
    except ValueError as err:
        assert "après la relation" in str(err)


def test_snapshot_prend_en_compte_payeur_structure_explicite():
    db = _preparer_base()
    gestion, IDrelation, IDconv = _creer_convention_brouillon(db)
    db.ReqInsert(
        "structures",
        [
            ("uid", "STR-payeur"),
            ("type_structure", "mairie_collectivite"),
            ("nom", "Mairie payeuse"),
            ("actif", 1),
            ("date_creation", "2026-09-01"),
            ("date_modification", "2026-09-01"),
        ],
    )
    relations = REL.GestionnaireRelationsStructures(db)
    relations.CreerPayeur(
        {
            "IDrelation_structure": IDrelation,
            "type_payeur": "structure",
            "IDstructure_payeur": 2,
            "taux_prise_en_charge": 75,
            "reference": "BC-2026-17",
        },
        date="2026-09-02",
    )
    gestion.ValiderConvention(IDconv, date="2026-09-03")
    snapshot = gestion.LireSnapshot(IDconv)
    assert len(snapshot["payeurs"]) == 1
    assert snapshot["payeurs"][0]["implicite"] is False
    assert snapshot["payeurs"][0]["IDstructure_payeur"] == 2
    assert snapshot["payeurs"][0]["taux_prise_en_charge"] == 75.0


def test_archivage_preserve_historique_et_exige_etat_final():
    db = _preparer_base()
    gestion, IDrelation, IDconv = _creer_convention_brouillon(db)
    try:
        gestion.ArchiverConvention(IDconv)
        assert False, "brouillon archivé"
    except ValueError:
        pass
    gestion.AnnulerConvention(IDconv, date="2026-09-04")
    assert gestion.ArchiverConvention(IDconv, date="2026-09-05") is True
    conv = gestion.LireConvention(IDconv)
    assert conv["actif"] == 0
    assert conv["statut"] == CONV.STATUT_ANNULEE
