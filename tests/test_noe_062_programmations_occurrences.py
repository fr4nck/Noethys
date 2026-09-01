# -*- coding: utf-8 -*-
import datetime
import importlib.util
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


DATA = _charger("noethys/Data/DATA_Structures.py", "DATA_Structures_prog062")
DATA_PROG = _charger("noethys/Data/DATA_Programmations_Structures.py", "DATA_Programmations_062")
SCHEMA = _charger("noethys/Utils/UTILS_Programmations_Structures_Schema.py", "SCHEMA_Programmations_062")
PROG = _charger("noethys/Utils/UTILS_Programmations_Structures.py", "UTILS_Programmations_062")
REL = _charger("noethys/Utils/UTILS_Relations_Structures.py", "UTILS_Relations_prog062")


class SQLiteDB(object):
    isNetwork = False

    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self._resultat = []
        self.creations = []
        self.commits = 0

    def IsTableExists(self, nom_table):
        return self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (nom_table,)
        ).fetchone() is not None

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
        champs = [c for c, v in donnees]
        valeurs = [v for c, v in donnees]
        req = "INSERT INTO %s (%s) VALUES (%s)" % (
            table, ", ".join(champs), ", ".join(["?"] * len(champs))
        )
        cur = self.conn.execute(req, valeurs)
        if commit:
            self.conn.commit()
        return cur.lastrowid

    def ReqMAJ(self, table, donnees, cle, ID, IDestChaine=False, commit=True):
        donnees = list(donnees)
        champs = [c for c, v in donnees]
        valeurs = [v for c, v in donnees]
        self.conn.execute(
            "UPDATE %s SET %s WHERE %s=?" % (
                table, ", ".join("%s=?" % c for c in champs), cle
            ),
            valeurs + [ID],
        )
        if commit:
            self.conn.commit()
        return True


def _creer_table(db, nom):
    db.CreationTable(nom, DATA.DB_STRUCTURES)
    db.Commit()


def _base(avec_programmations=True):
    db = SQLiteDB()
    for table in ("structures", "structures_groupes", "lieux", "structures_relations", "structures_payeurs"):
        _creer_table(db, table)
    if avec_programmations:
        for table in DATA_PROG.GetNomsTables():
            db.CreationTable(table, DATA_PROG.DB_PROGRAMMATIONS_STRUCTURES)
            db.Commit()
    db.ReqInsert("structures", [
        ("uid", "STR-ASSO"), ("type_structure", "association"),
        ("nom", "Club test"), ("actif", 1),
        ("date_creation", "2026-09-01"), ("date_modification", "2026-09-01"),
    ])
    db.ReqInsert("structures_groupes", [
        ("IDstructure", 1), ("nom", "Section badminton"), ("actif", 1), ("memo", ""),
    ])
    db.ReqInsert("lieux", [
        ("uid", "LIEU-GYM"), ("nom", "Gymnase test"), ("type_lieu", "gymnase"),
        ("actif", 1), ("date_creation", "2026-09-01"), ("date_modification", "2026-09-01"),
    ])
    relation = REL.GestionnaireRelationsStructures(db).CreerRelation({
        "uid": "REL-PROG-2026",
        "IDstructure": 1,
        "type_relation": "mise_disposition",
        "libelle": "Badminton annuel",
        "saison": "2026-2027",
        "date_debut": "2026-09-01",
        "date_fin": "2027-08-31",
        "tarif": 44,
        "unite_tarif": "heure",
        "regle_adhesion": "requise",
        "mode_facturation": "mensuel",
    }, date="2026-09-01")
    return db, relation


def _programmation(db, relation, uid="PROG-2026"):
    gestion = PROG.GestionnaireProgrammationsStructures(db)
    IDprog = gestion.CreerProgrammation({
        "uid": uid,
        "IDrelation_structure": relation,
        "saison": "2026-2027",
        "date_debut": "2026-09-01",
        "date_fin": "2027-08-31",
    }, date="2026-09-01")
    return gestion, IDprog


def _creneau(gestion, IDprog, uid="CRN-MARDI"):
    return gestion.CreerCreneau(IDprog, {
        "uid": uid,
        "jour_semaine": 1,
        "heure_debut": "18:00",
        "heure_fin": "19:30",
        "IDgroupe_structure": 1,
        "IDlieu": 1,
        "nature": "sport",
        "libelle": "Badminton adultes",
        "appliquer_scolaire": 1,
        "appliquer_vacances": 0,
        "inclure_feries": 0,
        "frequence": 1,
    }, date="2026-09-01")


def test_schema_declare_programmation_et_creneaux():
    assert DATA_PROG.GetNomsTables() == (
        "structures_programmations", "structures_programmations_creneaux"
    )
    assert "IDrelation_structure" in DATA_PROG.GetChamps("structures_programmations")
    champs = DATA_PROG.GetChamps("structures_programmations_creneaux")
    for champ in ("jour_semaine", "appliquer_scolaire", "appliquer_vacances", "frequence", "etat_renouvellement"):
        assert champ in champs


def test_activation_refuse_absence_relation_et_ne_cree_rien():
    db = SQLiteDB()
    resultat = SCHEMA.AssurerSchemaProgrammations(db, appliquer=True)
    assert resultat["ok"] is False
    assert resultat["prerequis_absents"] == ("structures_relations",)
    assert db.creations == []


def test_activation_cree_uniquement_les_deux_tables_et_est_idempotente():
    db = SQLiteDB()
    _creer_table(db, "structures_relations")
    avant = list(db.creations)
    resultat = SCHEMA.AssurerSchemaProgrammations(db, appliquer=True)
    assert resultat["ok"] is True
    assert resultat["tables_creees"] == DATA_PROG.GetNomsTables()
    assert db.creations == avant + list(DATA_PROG.GetNomsTables())
    resultat2 = SCHEMA.AssurerSchemaProgrammations(db, appliquer=True)
    assert resultat2["ok"] is True
    assert resultat2["tables_creees"] == ()


def test_schema_incomplet_bloque_preflight():
    db = SQLiteDB()
    _creer_table(db, "structures_relations")
    db.conn.execute("CREATE TABLE structures_programmations (IDprogrammation_structure INTEGER PRIMARY KEY AUTOINCREMENT, uid VARCHAR(64))")
    db.conn.commit()
    resultat = SCHEMA.AssurerSchemaProgrammations(db, appliquer=True)
    assert resultat["ok"] is False
    assert resultat["tables_incoherentes"] == ("structures_programmations",)
    assert "IDrelation_structure" in resultat["rapport"]["structures_programmations"]["champs_manquants"]
    assert "structures_programmations_creneaux" not in db.creations


def test_programmation_est_bornee_par_relation_et_unique_par_saison():
    db, relation = _base()
    gestion, IDprog = _programmation(db, relation)
    prog = gestion.LireProgrammation(IDprog)
    assert prog["uid"] == "PROG-2026"
    assert prog["statut"] == PROG.STATUT_BROUILLON
    try:
        _programmation(db, relation, uid="PROG-DOUBLON")
        assert False, "programmation doublon acceptée"
    except ValueError:
        pass
    try:
        gestion.CreerProgrammation({
            "IDrelation_structure": relation, "saison": "2027-2028",
            "date_debut": "2026-08-01", "date_fin": "2027-08-31",
        })
        assert False, "programmation hors relation acceptée"
    except ValueError:
        pass


def test_creneau_valide_groupe_lieu_horaire_et_regles_calendrier():
    db, relation = _base()
    gestion, IDprog = _programmation(db, relation)
    IDcreneau = _creneau(gestion, IDprog)
    cr = gestion.LireCreneau(IDcreneau)
    assert cr["IDgroupe_structure"] == 1
    assert cr["IDlieu"] == 1
    assert cr["etat_renouvellement"] == PROG.RENOUVELLEMENT_AJOUTE
    try:
        gestion.CreerCreneau(IDprog, {
            "jour_semaine": 7, "heure_debut": "18:00", "heure_fin": "19:00"
        })
        assert False, "jour invalide accepté"
    except ValueError:
        pass
    try:
        gestion.CreerCreneau(IDprog, {
            "jour_semaine": 1, "heure_debut": "19:00", "heure_fin": "18:00"
        })
        assert False, "horaire inversé accepté"
    except ValueError:
        pass
    try:
        gestion.CreerCreneau(IDprog, {
            "jour_semaine": 1, "heure_debut": "18:00", "heure_fin": "19:00",
            "appliquer_scolaire": 0, "appliquer_vacances": 0,
        })
        assert False, "règle calendrier vide acceptée"
    except ValueError:
        pass


def test_validation_verrouille_programmation_et_creneaux():
    db, relation = _base()
    gestion, IDprog = _programmation(db, relation)
    IDcreneau = _creneau(gestion, IDprog)
    assert gestion.ChangerStatut(IDprog, PROG.STATUT_VALIDEE) is True
    assert gestion.LireProgrammation(IDprog)["statut"] == PROG.STATUT_VALIDEE
    try:
        gestion.ModifierProgrammation(IDprog, {"notes": "interdit"})
        assert False, "programmation validée modifiée"
    except ValueError:
        pass
    try:
        gestion.ModifierCreneau(IDcreneau, {"libelle": "interdit"})
        assert False, "créneau validé modifié"
    except ValueError:
        pass


def test_renouvellement_conserve_filiation_et_detecte_modification_suppression():
    db, relation = _base()
    gestion, IDprog = _programmation(db, relation)
    ancien_creneau = _creneau(gestion, IDprog)
    gestion.ChangerStatut(IDprog, PROG.STATUT_VALIDEE)

    relation2 = REL.GestionnaireRelationsStructures(db).CreerRelation({
        "uid": "REL-PROG-2027", "IDstructure": 1,
        "type_relation": "mise_disposition", "libelle": "Badminton annuel",
        "saison": "2027-2028", "date_debut": "2027-09-01", "date_fin": "2028-08-31",
        "tarif": 46, "unite_tarif": "heure", "regle_adhesion": "requise",
        "mode_facturation": "mensuel",
    }, date="2027-06-01")
    nouveau = gestion.RenouvelerProgrammation(
        IDprog, relation2, "2027-2028", "2027-09-01", "2028-08-31", date="2027-06-01"
    )
    prog2 = gestion.LireProgrammation(nouveau)
    assert prog2["IDprogrammation_source"] == IDprog
    copies = gestion.ListerCreneaux(nouveau)
    assert len(copies) == 1
    copie = copies[0]
    assert copie["IDcreneau_source"] == ancien_creneau
    assert copie["etat_renouvellement"] == PROG.RENOUVELLEMENT_INCHANGE

    gestion.ModifierCreneau(copie["IDcreneau_programmation"], {"heure_fin": "20:00"})
    assert gestion.LireCreneau(copie["IDcreneau_programmation"])["etat_renouvellement"] == PROG.RENOUVELLEMENT_MODIFIE
    gestion.SupprimerCreneau(copie["IDcreneau_programmation"])
    assert gestion.LireCreneau(copie["IDcreneau_programmation"])["etat_renouvellement"] == PROG.RENOUVELLEMENT_SUPPRIME
    assert gestion.ListerCreneaux(nouveau, conserves_seulement=True) == []


def test_apercu_delegue_strictement_au_calculateur_historique():
    db, relation = _base()
    gestion, IDprog = _programmation(db, relation)
    _creneau(gestion, IDprog)
    appels = []

    def calculateur(params):
        appels.append(dict(params))
        assert params["jours_scolaires"] == [1]
        assert params["jours_vacances"] == []
        assert params["semaines"] == 1
        assert params["feries"] is False
        return [
            {"date_debut": datetime.datetime(2026, 9, 8, 18, 0), "date_fin": datetime.datetime(2026, 9, 8, 19, 30)},
            {"date_debut": datetime.datetime(2026, 9, 15, 18, 0), "date_fin": datetime.datetime(2026, 9, 15, 19, 30)},
        ]

    occurrences = gestion.GenererApercuOccurrences(IDprog, calculateur)
    assert len(appels) == 1
    assert len(occurrences) == 2
    assert occurrences[0]["date"] == "2026-09-08"
    assert occurrences[0]["duree_minutes"] == 90
    assert occurrences[0]["uid"].startswith("OCC-")
    assert occurrences[0]["uid_relation"] == "REL-PROG-2026"
    assert occurrences[0]["IDstructure"] == 1


def test_occurrences_sont_deterministes_et_dedoublonnees():
    db, relation = _base()
    gestion, IDprog = _programmation(db, relation)
    _creneau(gestion, IDprog)
    occurrence = {"date_debut": datetime.datetime(2026, 9, 8, 18, 0), "date_fin": datetime.datetime(2026, 9, 8, 19, 30)}
    def calculateur(params):
        return [occurrence, occurrence]
    premier = gestion.GenererApercuOccurrences(IDprog, calculateur)
    second = gestion.GenererApercuOccurrences(IDprog, calculateur)
    assert len(premier) == 1
    assert premier[0]["uid"] == second[0]["uid"]


def test_annexe_est_triee_et_calcule_volume_previsionnel():
    db, relation = _base()
    gestion, IDprog = _programmation(db, relation)
    _creneau(gestion, IDprog)
    def calculateur(params):
        return [
            {"date_debut": datetime.datetime(2026, 9, 15, 18, 0), "date_fin": datetime.datetime(2026, 9, 15, 19, 30)},
            {"date_debut": datetime.datetime(2026, 9, 8, 18, 0), "date_fin": datetime.datetime(2026, 9, 8, 19, 30)},
        ]
    annexe = gestion.ConstruireAnnexePrevisionnelle(IDprog, calculateur)
    assert annexe["nb_seances"] == 2
    assert annexe["duree_totale_minutes"] == 180
    assert [x["numero"] for x in annexe["lignes"]] == [1, 2]
    assert annexe["lignes"][0]["date"] == "2026-09-08"
    assert annexe["lignes"][0]["jour"] == "mardi"


def test_calculateur_invalide_est_refuse_et_programmation_annulee_ne_genere_rien():
    db, relation = _base()
    gestion, IDprog = _programmation(db, relation)
    _creneau(gestion, IDprog)
    try:
        gestion.GenererApercuOccurrences(IDprog, None)
        assert False, "calculateur absent accepté"
    except TypeError:
        pass
    gestion.ChangerStatut(IDprog, PROG.STATUT_ANNULEE)
    try:
        gestion.GenererApercuOccurrences(IDprog, lambda params: [])
        assert False, "programmation annulée génératrice"
    except ValueError:
        pass
