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


DOC_TESTS = _charger(
    "tests/test_noe_062_conventions_documents.py",
    "test_noe_062_conventions_documents_base_annexe",
)
ADAPTER = _charger(
    "noethys/Utils/UTILS_Conventions_Structures_Recurrence.py",
    "UTILS_Conventions_Structures_Recurrence_test",
)
COMMON = _charger(
    "noethys/Utils/UTILS_Locations_Recurrence.py",
    "UTILS_Locations_Recurrence_annexe_test",
)


def _regle(debut, fin, semaines=1, feries=False):
    return {
        "date_debut": debut,
        "date_fin": fin,
        "heure_debut": "10:30",
        "heure_fin": "11:15",
        "jours_vacances": [],
        "jours_scolaires": [0],
        "semaines": semaines,
        "feries": feries,
    }


def test_paquet_documentaire_recoit_directement_annexe_du_moteur_commun():
    db = DOC_TESTS.BASE._preparer_base()
    gestion, IDrelation, IDconv = DOC_TESTS._creer_documentable(db)
    gestion.ValiderConvention(IDconv, date="2026-09-03")
    commits_avant = db.commits

    paquet = ADAPTER.ConstruirePaquetDocumentaireDepuisRecurrence(
        gestion,
        IDconv,
        _regle(datetime.date(2026, 9, 7), datetime.date(2026, 9, 21)),
        groupe="Groupe 1",
        lieu="Salle A",
        calendrier=([], []),
    )

    assert db.commits == commits_avant
    assert paquet["champs"]["{ANNEXE_NB_SEANCES}"] == "3"
    assert paquet["champs"]["{ANNEXE_DUREE_TOTALE_MINUTES}"] == "135"
    assert [ligne["date"] for ligne in paquet["lignes_annexe"]] == [
        "2026-09-07",
        "2026-09-14",
        "2026-09-21",
    ]
    assert all(ligne["groupe"] == "Groupe 1" for ligne in paquet["lignes_annexe"])
    assert all(ligne["lieu"] == "Salle A" for ligne in paquet["lignes_annexe"])


def test_lignes_annexe_sont_strictement_alignees_sur_occurrences_communes():
    regle = _regle(
        datetime.date(2026, 9, 7),
        datetime.date(2026, 10, 5),
        semaines=2,
    )
    occurrences = COMMON.CalculerOccurrencesAnnexe(regle, calendrier=([], []))
    lignes = ADAPTER.CalculerLignesAnnexe(
        regle,
        convention_uid="CONV-PARITE",
        calendrier=([], []),
    )
    assert [ligne["date"] for ligne in lignes] == [
        item["date_debut"].date().isoformat() for item in occurrences
    ]
    assert [ligne["heure_debut"] for ligne in lignes] == [
        item["date_debut"].strftime("%H:%M") for item in occurrences
    ]
    assert [ligne["heure_fin"] for ligne in lignes] == [
        item["date_fin"].strftime("%H:%M") for item in occurrences
    ]


def test_identifiants_occurrences_sont_deterministes_et_namespaces_par_convention():
    occurrence = {
        "date_debut": datetime.datetime(2026, 9, 7, 10, 30),
        "date_fin": datetime.datetime(2026, 9, 7, 11, 15),
    }
    lignes1 = ADAPTER.ConstruireLignesAnnexeDepuisOccurrences(
        [occurrence], convention_uid="CONV-A", groupe="G1", lieu="Salle"
    )
    lignes2 = ADAPTER.ConstruireLignesAnnexeDepuisOccurrences(
        [occurrence], convention_uid="CONV-A", groupe="G1", lieu="Salle"
    )
    lignes3 = ADAPTER.ConstruireLignesAnnexeDepuisOccurrences(
        [occurrence], convention_uid="CONV-B", groupe="G1", lieu="Salle"
    )
    assert lignes1[0]["identifiant_stable"] == lignes2[0]["identifiant_stable"]
    assert lignes1[0]["identifiant_stable"] != lignes3[0]["identifiant_stable"]
    assert lignes1[0]["identifiant_stable"].startswith("SEANCE-")


def test_adaptateur_refuse_occurrence_incomplete_negative_ou_non_minute():
    cas = [
        {"date_debut": datetime.datetime(2026, 9, 7, 10, 30)},
        {
            "date_debut": datetime.datetime(2026, 9, 7, 11, 15),
            "date_fin": datetime.datetime(2026, 9, 7, 10, 30),
        },
        {
            "date_debut": datetime.datetime(2026, 9, 7, 10, 30, 0),
            "date_fin": datetime.datetime(2026, 9, 7, 11, 15, 30),
        },
    ]
    for occurrence in cas:
        try:
            ADAPTER.ConstruireLignesAnnexeDepuisOccurrences([occurrence])
            assert False, "occurrence invalide acceptée"
        except ValueError:
            pass


def test_adaptateur_ne_reimplemente_aucune_requete_calendrier():
    source = (
        ROOT / "noethys" / "Utils" / "UTILS_Conventions_Structures_Recurrence.py"
    ).read_text(encoding="utf-8")
    assert "FROM vacances" not in source
    assert "FROM jours_feries" not in source
    assert "CalculerOccurrencesAnnexe" in source
