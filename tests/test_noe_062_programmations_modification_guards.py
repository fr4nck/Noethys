# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _charger(path, nom):
    spec = importlib.util.spec_from_file_location(nom, str(ROOT / path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = _charger(
    "tests/test_noe_062_programmations_persistantes.py",
    "test_noe_062_programmations_persistantes_base_modification_guards",
)
PROG = BASE.PROG


def _creer_programme_meme_source(gestion, IDrelation, uid, saison):
    return gestion.CreerProgrammation(
        {
            "uid": uid,
            "type_source": "relation",
            "IDrelation_structure": IDrelation,
            "saison": saison,
            "libelle": "Programme parallèle",
            "date_debut": "2026-09-01",
            "date_fin": "2027-08-31",
        },
        date="2026-09-01",
    )


def test_modifier_saison_refuse_collision_avec_autre_programmation_active():
    db, gestion, IDrelation = BASE._preparer_relation_programmable()
    IDpremier = BASE._creer_programme_relation(gestion, IDrelation)
    IDsecond = _creer_programme_meme_source(
        gestion,
        IDrelation,
        uid="PROG-2027-002",
        saison="2027-2028",
    )

    try:
        gestion.ModifierProgrammation(
            IDpremier,
            {"saison": "2027-2028"},
            date="2026-09-02",
        )
        assert False, "collision source/saison acceptée pendant la modification"
    except ValueError as err:
        assert "existe déjà" in str(err)

    assert gestion.LireProgrammation(IDpremier)["saison"] == "2026-2027"
    assert gestion.LireProgrammation(IDsecond)["saison"] == "2027-2028"


def test_modifier_programmation_ignore_sa_propre_ligne_dans_controle_unicite():
    db, gestion, IDrelation = BASE._preparer_relation_programmable()
    IDprog = BASE._creer_programme_relation(gestion, IDrelation)

    assert gestion.ModifierProgrammation(
        IDprog,
        {"saison": "2026-2027", "libelle": "Programme renommé"},
        date="2026-09-02",
    ) is True
    programme = gestion.LireProgrammation(IDprog)
    assert programme["saison"] == "2026-2027"
    assert programme["libelle"] == "Programme renommé"


def test_reduire_periode_refuse_de_laisser_un_creneau_actif_hors_bornes():
    db, gestion, IDrelation = BASE._preparer_relation_programmable()
    IDprog = BASE._creer_programme_relation(gestion, IDrelation)
    BASE._ajouter_lundi(
        gestion,
        IDprog,
        uid="CREN-BORNE-MODIFICATION",
        date_debut="2026-10-01",
        date_fin="2027-03-31",
    )

    for changements, fragment in (
        ({"date_debut": "2026-11-01"}, "débute avant"),
        ({"date_fin": "2027-02-28"}, "se termine après"),
    ):
        try:
            gestion.ModifierProgrammation(
                IDprog,
                changements,
                date="2026-09-02",
            )
            assert False, "réduction incompatible avec un créneau actif acceptée"
        except ValueError as err:
            assert fragment in str(err)

        programme = gestion.LireProgrammation(IDprog)
        assert programme["date_debut"] == "2026-09-01"
        assert programme["date_fin"] == "2027-08-31"


def test_reduire_periode_reste_possible_si_tous_les_creneaux_restent_inclus():
    db, gestion, IDrelation = BASE._preparer_relation_programmable()
    IDprog = BASE._creer_programme_relation(gestion, IDrelation)
    BASE._ajouter_lundi(
        gestion,
        IDprog,
        uid="CREN-BORNE-INCLUS",
        date_debut="2026-10-01",
        date_fin="2027-03-31",
    )

    assert gestion.ModifierProgrammation(
        IDprog,
        {"date_debut": "2026-10-01", "date_fin": "2027-03-31"},
        date="2026-09-02",
    ) is True
    programme = gestion.LireProgrammation(IDprog)
    assert programme["date_debut"] == "2026-10-01"
    assert programme["date_fin"] == "2027-03-31"
