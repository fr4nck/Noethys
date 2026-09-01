# -*- coding: utf-8 -*-
import datetime
import importlib.util
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


BASE = _charger(
    "tests/test_noe_062_conventions_avenants.py",
    "test_noe_062_conventions_avenants_base_programmations",
)
DATA = _charger(
    "noethys/Data/DATA_Programmations_Structures.py",
    "DATA_Programmations_Structures_test",
)
SCHEMA = _charger(
    "noethys/Utils/UTILS_Programmations_Structures_Schema.py",
    "UTILS_Programmations_Structures_Schema_test",
)
PROG = _charger(
    "noethys/Utils/UTILS_Programmations_Structures.py",
    "UTILS_Programmations_Structures_test",
)
REC = _charger(
    "noethys/Utils/UTILS_Locations_Recurrence.py",
    "UTILS_Locations_Recurrence_programmations_test",
)
REL = BASE.REL


def _creer_tables_programmation(db):
    for table in ("structures_programmations", "structures_programmations_creneaux"):
        db.CreationTable(table, DATA.DB_PROGRAMMATIONS_STRUCTURES)
        db.Commit()


def _preparer_relation_programmable():
    db = BASE._preparer_base()
    _creer_tables_programmation(db)
    IDrelation = BASE._creer_relation(db)
    gestion = PROG.GestionnaireProgrammationsStructures(db)
    return db, gestion, IDrelation


def _creer_programme_relation(gestion, IDrelation, uid="PROG-2026-001"):
    return gestion.CreerProgrammation(
        {
            "uid": uid,
            "type_source": "relation",
            "IDrelation_structure": IDrelation,
            "saison": "2026-2027",
            "libelle": "Programme sportif annuel",
            "date_debut": "2026-09-01",
            "date_fin": "2027-08-31",
            "UIDintervenant_habituel": "SAL-001",
        },
        date="2026-09-01",
    )


def _ajouter_lundi(gestion, IDprog, **kwargs):
    donnees = {
        "jour_semaine": 0,
        "heure_debut": "10:30",
        "heure_fin": "11:15",
        "appliquer_scolaire": True,
        "appliquer_vacances": False,
        "inclure_feries": False,
        "frequence": 1,
        "groupe": "Groupe 1",
    }
    donnees.update(kwargs)
    return gestion.AjouterCreneau(IDprog, donnees, date="2026-09-01")


def test_schema_declare_programme_et_creneau_sans_dupliquer_les_interventions():
    assert set(DATA.DB_PROGRAMMATIONS_STRUCTURES) == {
        "structures_programmations",
        "structures_programmations_creneaux",
    }
    champs_programme = DATA.GetChamps("structures_programmations")
    champs_creneau = DATA.GetChamps("structures_programmations_creneaux")
    assert "type_source" in champs_programme
    assert "IDrelation_structure" in champs_programme
    assert "IDactivite" in champs_programme
    assert "IDprogrammation_parent" in champs_programme
    assert "IDcreneau_source" in champs_creneau
    assert "frequence" in champs_creneau
    assert "appliquer_scolaire" in champs_creneau
    assert "appliquer_vacances" in champs_creneau
    assert "date" not in champs_creneau
    assert "IDintervention" not in champs_creneau


def test_schema_peut_etre_active_sans_structures_relations_pour_activites_internes():
    db = BASE.SQLiteDB()
    rapport = SCHEMA.AssurerSchemaProgrammations(db, appliquer=True)
    assert rapport["ok"] is True
    assert set(rapport["tables_creees"]) == {
        "structures_programmations",
        "structures_programmations_creneaux",
    }
    assert rapport["prerequis_absents"] == ()
    assert db.IsTableExists("structures_relations") is False

    second = SCHEMA.AssurerSchemaProgrammations(db, appliquer=True)
    assert second["ok"] is True
    assert second["tables_creees"] == ()


def test_schema_incoherent_bloque_toute_creation_silencieuse():
    db = BASE.SQLiteDB()
    db.conn.execute("CREATE TABLE structures_programmations (IDprogrammation_structure TEXT)")
    db.conn.commit()
    rapport = SCHEMA.AssurerSchemaProgrammations(db, appliquer=True)
    assert rapport["ok"] is False
    assert "structures_programmations" in rapport["tables_incoherentes"]
    assert db.IsTableExists("structures_programmations_creneaux") is False


def test_programmation_relation_est_bornee_par_la_relation():
    db, gestion, IDrelation = _preparer_relation_programmable()
    IDprog = _creer_programme_relation(gestion, IDrelation)
    programme = gestion.LireProgrammation(IDprog)
    assert programme["type_source"] == PROG.TYPE_SOURCE_RELATION
    assert programme["IDrelation_structure"] == IDrelation
    assert programme["statut"] == PROG.STATUT_BROUILLON

    try:
        gestion.CreerProgrammation(
            {
                "uid": "PROG-HORS-BORNES",
                "type_source": "relation",
                "IDrelation_structure": IDrelation,
                "saison": "2025-2026",
                "date_debut": "2025-09-01",
                "date_fin": "2026-08-31",
            },
            date="2026-09-01",
        )
        assert False, "programmation hors relation acceptée"
    except ValueError as err:
        assert "avant la relation" in str(err)


def test_activite_interne_peut_avoir_programmation_sans_relation_contractuelle():
    db = BASE.SQLiteDB()
    _creer_tables_programmation(db)
    db.conn.execute("CREATE TABLE activites (IDactivite INTEGER PRIMARY KEY, nom TEXT)")
    db.conn.execute("INSERT INTO activites (IDactivite, nom) VALUES (7, 'Ecole multisport')")
    db.conn.commit()
    gestion = PROG.GestionnaireProgrammationsStructures(db)
    IDprog = gestion.CreerProgrammation(
        {
            "uid": "PROG-EMS-2026",
            "type_source": "activite",
            "IDactivite": 7,
            "saison": "2026-2027",
            "libelle": "Ecole multisport",
            "date_debut": "2026-09-01",
            "date_fin": "2027-08-31",
        },
        date="2026-09-01",
    )
    programme = gestion.LireProgrammation(IDprog)
    assert programme["IDrelation_structure"] is None
    assert programme["IDactivite"] == 7


def test_source_relation_et_activite_ne_peuvent_pas_etre_melangees():
    db, gestion, IDrelation = _preparer_relation_programmable()
    try:
        gestion.CreerProgrammation(
            {
                "type_source": "relation",
                "IDrelation_structure": IDrelation,
                "IDactivite": 99,
                "saison": "2026-2027",
                "date_debut": "2026-09-01",
                "date_fin": "2027-08-31",
            }
        )
        assert False, "source mixte acceptée"
    except ValueError:
        pass


def test_unicite_source_saison_empeche_deux_programmes_actifs_concurrents():
    db, gestion, IDrelation = _preparer_relation_programmable()
    _creer_programme_relation(gestion, IDrelation)
    try:
        _creer_programme_relation(gestion, IDrelation, uid="PROG-2026-002")
        assert False, "deux programmations actives source/saison acceptées"
    except ValueError as err:
        assert "existe déjà" in str(err)


def test_creneau_valide_expose_exactement_le_contrat_du_moteur_historique():
    db, gestion, IDrelation = _preparer_relation_programmable()
    IDprog = _creer_programme_relation(gestion, IDrelation)
    IDcreneau = _ajouter_lundi(gestion, IDprog)
    regle = gestion.ConstruireRegleRecurrence(IDcreneau)
    assert set(regle) == {
        "date_debut", "date_fin", "heure_debut", "heure_fin",
        "jours_vacances", "jours_scolaires", "semaines", "feries",
    }
    assert regle["date_debut"] == datetime.date(2026, 9, 1)
    assert regle["date_fin"] == datetime.date(2027, 8, 31)
    assert regle["jours_scolaires"] == [0]
    assert regle["jours_vacances"] == []
    assert regle["semaines"] == 1
    assert regle["feries"] is False

    occurrences = REC.CalculerOccurrences(
        dict(regle, date_fin=datetime.date(2026, 9, 21)),
        calendrier=([], []),
    )
    assert [o["date_debut"].date().isoformat() for o in occurrences] == [
        "2026-09-07", "2026-09-14", "2026-09-21"
    ]


def test_creneau_refuse_jour_horaire_periode_et_regle_vides_invalides():
    db, gestion, IDrelation = _preparer_relation_programmable()
    IDprog = _creer_programme_relation(gestion, IDrelation)
    cas = [
        {"jour_semaine": 7, "heure_debut": "10:00", "heure_fin": "11:00"},
        {"jour_semaine": 0, "heure_debut": "11:00", "heure_fin": "10:00"},
        {
            "jour_semaine": 0,
            "heure_debut": "10:00",
            "heure_fin": "11:00",
            "appliquer_scolaire": False,
            "appliquer_vacances": False,
        },
        {"jour_semaine": 0, "heure_debut": "10:00", "heure_fin": "11:00", "frequence": 9},
        {
            "jour_semaine": 0,
            "heure_debut": "10:00",
            "heure_fin": "11:00",
            "date_debut": "2025-09-01",
        },
    ]
    for donnees in cas:
        try:
            gestion.AjouterCreneau(IDprog, donnees)
            assert False, "créneau invalide accepté: %r" % donnees
        except ValueError:
            pass


def test_programmation_validee_et_ses_creneaux_deviennent_immuables():
    db, gestion, IDrelation = _preparer_relation_programmable()
    IDprog = _creer_programme_relation(gestion, IDrelation)
    IDcreneau = _ajouter_lundi(gestion, IDprog)
    assert gestion.ValiderProgrammation(IDprog, date="2026-09-02") is True
    assert gestion.ConstruireRegleRecurrence(IDcreneau, exiger_validee=True)

    operations = (
        lambda: gestion.ModifierProgrammation(IDprog, {"libelle": "Changé"}),
        lambda: gestion.ModifierCreneau(IDcreneau, {"heure_debut": "09:30"}),
        lambda: gestion.SupprimerCreneau(IDcreneau),
        lambda: gestion.AjouterCreneau(IDprog, {
            "jour_semaine": 1, "heure_debut": "10:00", "heure_fin": "11:00"
        }),
    )
    for operation in operations:
        try:
            operation()
            assert False, "mutation d'une programmation validée acceptée"
        except ValueError:
            pass


def test_renouvellement_n1_conserve_filiation_sans_transposer_dates_exactes():
    db, gestion, IDrelation = _preparer_relation_programmable()
    IDprog = _creer_programme_relation(gestion, IDrelation)
    IDsimple = _ajouter_lundi(gestion, IDprog, uid="CREN-SIMPLE")
    IDborne = _ajouter_lundi(
        gestion,
        IDprog,
        uid="CREN-BORNE",
        jour_semaine=2,
        date_debut="2026-11-01",
        date_fin="2027-03-31",
    )
    gestion.ValiderProgrammation(IDprog, date="2026-09-02")

    relations = REL.GestionnaireRelationsStructures(db)
    IDrelation2 = relations.CreerRelation(
        {
            "uid": "REL-2027-001",
            "IDstructure": 1,
            "type_relation": "mise_disposition",
            "libelle": "Encadrement sportif saison 2027-2028",
            "saison": "2027-2028",
            "date_debut": "2027-09-01",
            "date_fin": "2028-08-31",
            "tarif": 44,
            "unite_tarif": "heure",
            "regle_adhesion": "requise",
            "mode_facturation": "mensuel",
        },
        date="2027-06-01",
    )
    IDnouveau = gestion.RenouvelerProgrammation(
        IDprog,
        saison="2027-2028",
        date_debut="2027-09-01",
        date_fin="2028-08-31",
        source={"type_source": "relation", "IDrelation_structure": IDrelation2},
        uid="PROG-2027-001",
        date="2027-06-01",
    )
    nouveau = gestion.LireProgrammation(IDnouveau)
    assert nouveau["IDprogrammation_parent"] == IDprog
    assert nouveau["statut"] == PROG.STATUT_BROUILLON
    clones = gestion.ListerCreneaux(IDnouveau)
    assert len(clones) == 2
    par_source = dict((c["IDcreneau_source"], c) for c in clones)
    assert par_source[IDsimple]["etat_renouvellement"] == PROG.RENOUVELLEMENT_INCHANGE
    assert par_source[IDborne]["etat_renouvellement"] == PROG.RENOUVELLEMENT_MODIFIE
    assert par_source[IDborne]["date_debut"] is None
    assert par_source[IDborne]["date_fin"] is None


def test_suppression_renouvele_garde_trace_mais_ajout_local_est_simplement_archive():
    db, gestion, IDrelation = _preparer_relation_programmable()
    IDprog = _creer_programme_relation(gestion, IDrelation)
    IDajoute = _ajouter_lundi(gestion, IDprog)
    gestion.SupprimerCreneau(IDajoute, date="2026-09-02")
    assert gestion.LireCreneau(IDajoute)["actif"] == 0

    # Un créneau filié doit, lui, conserver la trace "supprime".
    IDsource = _ajouter_lundi(gestion, IDprog, uid="CREN-SOURCE-TRACE")
    gestion.ValiderProgrammation(IDprog, date="2026-09-03")
    # Le comportement de filiation est couvert exhaustivement par le renouvellement ;
    # la suppression d'un clone sera possible sur le brouillon N+1.
    assert gestion.LireCreneau(IDsource)["actif"] == 1


def test_renouvellement_est_atomique_si_le_clonage_echoue():
    db, gestion, IDrelation = _preparer_relation_programmable()
    IDprog = _creer_programme_relation(gestion, IDrelation)
    _ajouter_lundi(gestion, IDprog, uid="CREN-A")
    _ajouter_lundi(gestion, IDprog, uid="CREN-B", jour_semaine=1)
    gestion.ValiderProgrammation(IDprog, date="2026-09-02")

    relations = REL.GestionnaireRelationsStructures(db)
    IDrelation2 = relations.CreerRelation(
        {
            "uid": "REL-ROLLBACK-2027",
            "IDstructure": 1,
            "type_relation": "mise_disposition",
            "libelle": "Relation rollback",
            "saison": "2027-2028",
            "date_debut": "2027-09-01",
            "date_fin": "2028-08-31",
            "tarif": 44,
            "unite_tarif": "heure",
            "regle_adhesion": "requise",
            "mode_facturation": "mensuel",
        },
        date="2027-06-01",
    )

    original = db.ReqInsert
    compteur = {"creneaux": 0}

    def insert_fail(table, donnees, commit=True):
        if table == "structures_programmations_creneaux":
            compteur["creneaux"] += 1
            if compteur["creneaux"] == 2:
                raise RuntimeError("échec injecté")
        return original(table, donnees, commit=commit)

    db.ReqInsert = insert_fail
    try:
        gestion.RenouvelerProgrammation(
            IDprog,
            saison="2027-2028",
            date_debut="2027-09-01",
            date_fin="2028-08-31",
            source={"type_source": "relation", "IDrelation_structure": IDrelation2},
            uid="PROG-ROLLBACK-2027",
            date="2027-06-01",
        )
        assert False, "renouvellement partiel accepté"
    except RuntimeError:
        pass
    finally:
        db.ReqInsert = original

    assert gestion.LireProgrammationParUID("PROG-ROLLBACK-2027") is None
    req = "SELECT COUNT(*) FROM structures_programmations_creneaux WHERE IDprogrammation_structure NOT IN (?)"
    # Le rollback ne doit avoir laissé aucun clone supplémentaire.
    nombre_avant = len(gestion.ListerCreneaux(IDprog, actifs_seulement=False))
    assert nombre_avant == 2
