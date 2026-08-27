# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _charger():
    path = ROOT / "scripts" / "check_schema_compatibility.py"
    spec = importlib.util.spec_from_file_location("check_schema_compatibility_test", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GUARD = _charger()


def test_les_tests_jetables_sont_hors_perimetre_schema():
    assert GUARD.is_ignored_path("tests/test_schema_temporaire.py") is True
    assert GUARD.is_ignored_path("tests/sous_dossier/test_db.py") is True


def test_le_code_applicatif_reste_surveille():
    assert GUARD.is_ignored_path("noethys/UpgradeDB.py") is False
    assert GUARD.is_ignored_path("noethys/Utils/UTILS_Tiers_Schema.py") is False


def test_le_constructeur_synthetique_historique_reste_explicitement_ignore():
    assert GUARD.is_ignored_path("scripts/build_synthetic_recette_db.py") is True
    assert GUARD.is_ignored_path("scripts/autre_migration.py") is False
