from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from noethys_qt.activity_editor import NativeActivityEditorRepository
from noethys_qt.activity_lifecycle import ActivityLifecycleRepository


DDL = """
CREATE TABLE activites (
    IDactivite INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT,
    date_creation TEXT,
    psu_unite_prevision INTEGER,
    psu_unite_presence INTEGER,
    psu_tarif_forfait INTEGER,
    psu_etiquette_rtt INTEGER
);
CREATE TABLE inscriptions (IDinscription INTEGER PRIMARY KEY AUTOINCREMENT, IDactivite INTEGER);
CREATE TABLE responsables_activite (IDresponsable INTEGER PRIMARY KEY AUTOINCREMENT, IDactivite INTEGER, nom TEXT);
CREATE TABLE groupes_activites (IDgroupe_activite INTEGER PRIMARY KEY AUTOINCREMENT, IDtype_groupe_activite INTEGER, IDactivite INTEGER);
CREATE TABLE groupes (IDgroupe INTEGER PRIMARY KEY AUTOINCREMENT, IDactivite INTEGER, nom TEXT);
CREATE TABLE agrements (IDagrement INTEGER PRIMARY KEY AUTOINCREMENT, IDactivite INTEGER, agrement TEXT);
CREATE TABLE pieces_activites (IDpiece_activite INTEGER PRIMARY KEY AUTOINCREMENT, IDactivite INTEGER, IDtype_piece INTEGER);
CREATE TABLE cotisations_activites (IDcotisation_activite INTEGER PRIMARY KEY AUTOINCREMENT, IDactivite INTEGER, IDtype_cotisation INTEGER);
CREATE TABLE renseignements_activites (IDrenseignement_activite INTEGER PRIMARY KEY AUTOINCREMENT, IDactivite INTEGER, IDrenseignement INTEGER);
CREATE TABLE unites (IDunite INTEGER PRIMARY KEY AUTOINCREMENT, IDactivite INTEGER, nom TEXT);
CREATE TABLE etiquettes (IDetiquette INTEGER PRIMARY KEY AUTOINCREMENT, IDactivite INTEGER, label TEXT, parent INTEGER);
CREATE TABLE unites_remplissage (IDunite_remplissage INTEGER PRIMARY KEY AUTOINCREMENT, IDactivite INTEGER, nom TEXT);
CREATE TABLE ouvertures (IDouverture INTEGER PRIMARY KEY AUTOINCREMENT, IDactivite INTEGER, IDunite INTEGER, IDgroupe INTEGER);
CREATE TABLE remplissage (IDremplissage INTEGER PRIMARY KEY AUTOINCREMENT, IDactivite INTEGER, IDunite_remplissage INTEGER, IDgroupe INTEGER);
CREATE TABLE categories_tarifs (IDcategorie_tarif INTEGER PRIMARY KEY AUTOINCREMENT, IDactivite INTEGER, nom TEXT);
CREATE TABLE noms_tarifs (IDnom_tarif INTEGER PRIMARY KEY AUTOINCREMENT, IDactivite INTEGER, nom TEXT);
CREATE TABLE tarifs (
    IDtarif INTEGER PRIMARY KEY AUTOINCREMENT,
    IDactivite INTEGER,
    IDnom_tarif INTEGER,
    categories_tarifs TEXT,
    groupes TEXT
);
CREATE TABLE tarifs_lignes (IDligne INTEGER PRIMARY KEY AUTOINCREMENT, IDactivite INTEGER, IDtarif INTEGER, montant REAL);
CREATE TABLE portail_periodes (IDperiode INTEGER PRIMARY KEY AUTOINCREMENT, IDactivite INTEGER, nom TEXT);
CREATE TABLE portail_unites (
    IDunite INTEGER PRIMARY KEY AUTOINCREMENT,
    IDactivite INTEGER,
    nom TEXT,
    unites_principales TEXT,
    unites_secondaires TEXT
);
CREATE TABLE evenements (IDevenement INTEGER PRIMARY KEY AUTOINCREMENT, IDactivite INTEGER, IDunite INTEGER, nom TEXT);
CREATE TABLE unites_groupes (IDunite_groupe INTEGER PRIMARY KEY AUTOINCREMENT, IDunite INTEGER, IDgroupe INTEGER);
CREATE TABLE unites_incompat (IDincompat INTEGER PRIMARY KEY AUTOINCREMENT, IDunite INTEGER, IDunite_incompat INTEGER);
CREATE TABLE unites_remplissage_unites (IDlien INTEGER PRIMARY KEY AUTOINCREMENT, IDunite_remplissage INTEGER, IDunite INTEGER);
CREATE TABLE categories_tarifs_villes (IDville_tarif INTEGER PRIMARY KEY AUTOINCREMENT, IDcategorie_tarif INTEGER, ville TEXT);
CREATE TABLE combi_tarifs (IDcombi INTEGER PRIMARY KEY AUTOINCREMENT, IDtarif INTEGER, nom TEXT);
CREATE TABLE combi_tarifs_unites (IDcombi_unite INTEGER PRIMARY KEY AUTOINCREMENT, IDtarif INTEGER, IDunite INTEGER);
CREATE TABLE questionnaire_filtres (IDfiltre INTEGER PRIMARY KEY AUTOINCREMENT, IDtarif INTEGER, champ TEXT);
"""


def make_repo(tmp_path: Path) -> tuple[Path, ActivityLifecycleRepository]:
    database = tmp_path / "activities.db"
    with sqlite3.connect(database) as connection:
        connection.executescript(DDL)
    editor = NativeActivityEditorRepository(database)
    return database, ActivityLifecycleRepository(editor)


def seed_activity(database: Path) -> int:
    with sqlite3.connect(database) as connection:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO activites (nom, date_creation) VALUES ('ALSH', '2026-09-01')")
        activity_id = int(cursor.lastrowid)
        cursor.execute("INSERT INTO responsables_activite (IDactivite, nom) VALUES (?, 'Direction')", (activity_id,))
        cursor.execute("INSERT INTO groupes_activites (IDtype_groupe_activite, IDactivite) VALUES (7, ?)", (activity_id,))
        cursor.execute("INSERT INTO groupes (IDactivite, nom) VALUES (?, '6-8 ans')", (activity_id,)); group_id = int(cursor.lastrowid)
        cursor.execute("INSERT INTO agrements (IDactivite, agrement) VALUES (?, '035ORG')", (activity_id,))
        cursor.execute("INSERT INTO pieces_activites (IDactivite, IDtype_piece) VALUES (?, 1)", (activity_id,))
        cursor.execute("INSERT INTO cotisations_activites (IDactivite, IDtype_cotisation) VALUES (?, 2)", (activity_id,))
        cursor.execute("INSERT INTO renseignements_activites (IDactivite, IDrenseignement) VALUES (?, 3)", (activity_id,))
        cursor.execute("INSERT INTO unites (IDactivite, nom) VALUES (?, 'Journée')", (activity_id,)); unit_id = int(cursor.lastrowid)
        cursor.execute("INSERT INTO unites (IDactivite, nom) VALUES (?, 'Repas')", (activity_id,)); unit2_id = int(cursor.lastrowid)
        cursor.execute("INSERT INTO unites_groupes (IDunite, IDgroupe) VALUES (?, ?)", (unit_id, group_id))
        cursor.execute("INSERT INTO unites_incompat (IDunite, IDunite_incompat) VALUES (?, ?)", (unit_id, unit2_id))
        cursor.execute("INSERT INTO etiquettes (IDactivite, label, parent) VALUES (?, 'Racine', NULL)", (activity_id,)); root_label = int(cursor.lastrowid)
        cursor.execute("INSERT INTO etiquettes (IDactivite, label, parent) VALUES (?, 'Enfant', ?)", (activity_id, root_label)); child_label = int(cursor.lastrowid)
        cursor.execute("INSERT INTO unites_remplissage (IDactivite, nom) VALUES (?, 'Capacité')", (activity_id,)); fill_id = int(cursor.lastrowid)
        cursor.execute("INSERT INTO unites_remplissage_unites (IDunite_remplissage, IDunite) VALUES (?, ?)", (fill_id, unit_id))
        cursor.execute("INSERT INTO ouvertures (IDactivite, IDunite, IDgroupe) VALUES (?, ?, ?)", (activity_id, unit_id, group_id))
        cursor.execute("INSERT INTO remplissage (IDactivite, IDunite_remplissage, IDgroupe) VALUES (?, ?, ?)", (activity_id, fill_id, group_id))
        cursor.execute("INSERT INTO categories_tarifs (IDactivite, nom) VALUES (?, 'Habitant')", (activity_id,)); category_id = int(cursor.lastrowid)
        cursor.execute("INSERT INTO categories_tarifs_villes (IDcategorie_tarif, ville) VALUES (?, 'Bais')", (category_id,))
        cursor.execute("INSERT INTO noms_tarifs (IDactivite, nom) VALUES (?, 'Journée')", (activity_id,)); tariff_name_id = int(cursor.lastrowid)
        cursor.execute(
            "INSERT INTO tarifs (IDactivite, IDnom_tarif, categories_tarifs, groupes) VALUES (?, ?, ?, ?)",
            (activity_id, tariff_name_id, str(category_id), str(group_id)),
        ); tariff_id = int(cursor.lastrowid)
        cursor.execute("INSERT INTO tarifs_lignes (IDactivite, IDtarif, montant) VALUES (?, ?, 12.5)", (activity_id, tariff_id))
        cursor.execute("INSERT INTO combi_tarifs (IDtarif, nom) VALUES (?, 'Journée')", (tariff_id,))
        cursor.execute("INSERT INTO combi_tarifs_unites (IDtarif, IDunite) VALUES (?, ?)", (tariff_id, unit_id))
        cursor.execute("INSERT INTO questionnaire_filtres (IDtarif, champ) VALUES (?, 'QF')", (tariff_id,))
        cursor.execute("INSERT INTO portail_periodes (IDactivite, nom) VALUES (?, 'Été')", (activity_id,))
        cursor.execute(
            "INSERT INTO portail_unites (IDactivite, nom, unites_principales, unites_secondaires) VALUES (?, 'Journée + repas', ?, ?)",
            (activity_id, str(unit_id), str(unit2_id)),
        )
        cursor.execute("INSERT INTO evenements (IDactivite, IDunite, nom) VALUES (?, ?, 'Sortie')", (activity_id, unit_id))
        cursor.execute(
            "UPDATE activites SET psu_unite_prevision=?, psu_unite_presence=?, psu_tarif_forfait=?, psu_etiquette_rtt=? WHERE IDactivite=?",
            (unit_id, unit2_id, tariff_id, child_label, activity_id),
        )
        connection.commit()
        return activity_id


def test_create_activity_creates_only_provisional_activity(tmp_path: Path) -> None:
    database, lifecycle = make_repo(tmp_path)
    activity_id = lifecycle.create_activity()
    with sqlite3.connect(database) as connection:
        row = connection.execute("SELECT nom, date_creation FROM activites WHERE IDactivite=?", (activity_id,)).fetchone()
        groups = connection.execute("SELECT COUNT(*) FROM groupes WHERE IDactivite=?", (activity_id,)).fetchone()[0]
    assert row is not None
    assert row[0] is None
    assert row[1]
    assert groups == 0


def test_duplicate_copies_configuration_and_remaps_internal_ids(tmp_path: Path) -> None:
    database, lifecycle = make_repo(tmp_path)
    source_id = seed_activity(database)
    copy_id = lifecycle.duplicate_activity(source_id)

    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT nom FROM activites WHERE IDactivite=?", (copy_id,)).fetchone()[0] == "Copie de ALSH"
        assert connection.execute("SELECT COUNT(*) FROM inscriptions WHERE IDactivite=?", (copy_id,)).fetchone()[0] == 0

        source_units = [row[0] for row in connection.execute("SELECT IDunite FROM unites WHERE IDactivite=? ORDER BY IDunite", (source_id,))]
        copy_units = [row[0] for row in connection.execute("SELECT IDunite FROM unites WHERE IDactivite=? ORDER BY IDunite", (copy_id,))]
        assert len(copy_units) == 2
        assert set(copy_units).isdisjoint(source_units)

        copy_group = connection.execute("SELECT IDgroupe FROM groupes WHERE IDactivite=?", (copy_id,)).fetchone()[0]
        tariff = connection.execute("SELECT IDtarif, categories_tarifs, groupes FROM tarifs WHERE IDactivite=?", (copy_id,)).fetchone()
        copy_category = connection.execute("SELECT IDcategorie_tarif FROM categories_tarifs WHERE IDactivite=?", (copy_id,)).fetchone()[0]
        assert tariff[1] == str(copy_category)
        assert tariff[2] == str(copy_group)

        portal = connection.execute("SELECT unites_principales, unites_secondaires FROM portail_unites WHERE IDactivite=?", (copy_id,)).fetchone()
        assert {int(portal[0]), int(portal[1])} == set(copy_units)

        labels = connection.execute("SELECT IDetiquette, label, parent FROM etiquettes WHERE IDactivite=? ORDER BY IDetiquette", (copy_id,)).fetchall()
        root = next(row for row in labels if row[1] == "Racine")
        child = next(row for row in labels if row[1] == "Enfant")
        assert child[2] == root[0]

        psu = connection.execute(
            "SELECT psu_unite_prevision, psu_unite_presence, psu_tarif_forfait, psu_etiquette_rtt FROM activites WHERE IDactivite=?",
            (copy_id,),
        ).fetchone()
        assert psu[0] in copy_units and psu[1] in copy_units
        assert psu[2] == tariff[0]
        assert psu[3] == child[0]

        assert connection.execute("SELECT COUNT(*) FROM questionnaire_filtres WHERE IDtarif=?", (tariff[0],)).fetchone()[0] == 1


def test_delete_is_blocked_when_registrations_exist(tmp_path: Path) -> None:
    database, lifecycle = make_repo(tmp_path)
    activity_id = seed_activity(database)
    with sqlite3.connect(database) as connection:
        connection.execute("INSERT INTO inscriptions (IDactivite) VALUES (?)", (activity_id,))
        connection.commit()

    check = lifecycle.delete_check(activity_id)
    assert check.registrations == 1
    assert not check.allowed
    with pytest.raises(ValueError, match="déjà inscrits"):
        lifecycle.delete_activity(activity_id)
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM activites WHERE IDactivite=?", (activity_id,)).fetchone()[0] == 1


def test_delete_removes_configuration_atomically(tmp_path: Path) -> None:
    database, lifecycle = make_repo(tmp_path)
    activity_id = seed_activity(database)
    lifecycle.delete_activity(activity_id)
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM activites WHERE IDactivite=?", (activity_id,)).fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM groupes WHERE IDactivite=?", (activity_id,)).fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM unites").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM questionnaire_filtres").fetchone()[0] == 0
        assert connection.execute("SELECT COUNT(*) FROM evenements").fetchone()[0] == 0


def test_delete_rolls_back_everything_if_one_step_fails(tmp_path: Path) -> None:
    database, lifecycle = make_repo(tmp_path)
    activity_id = seed_activity(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TRIGGER refuse_agreement_delete BEFORE DELETE ON agrements "
            "BEGIN SELECT RAISE(FAIL, 'refus test'); END"
        )
        before_links = connection.execute("SELECT COUNT(*) FROM unites_groupes").fetchone()[0]
        connection.commit()

    with pytest.raises(sqlite3.IntegrityError, match="refus test"):
        lifecycle.delete_activity(activity_id)

    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM activites WHERE IDactivite=?", (activity_id,)).fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM unites_groupes").fetchone()[0] == before_links
        assert connection.execute("SELECT COUNT(*) FROM responsables_activite WHERE IDactivite=?", (activity_id,)).fetchone()[0] == 1
