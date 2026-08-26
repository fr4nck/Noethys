# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "noethys" / "Utils" / "UTILS_Icones_pmsl.py"
SPEC = importlib.util.spec_from_file_location("UTILS_Icones_pmsl_test", MODULE_PATH)
ICONES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ICONES)


def test_mapping_p0_univoque():
    assert ICONES.RoleDepuisLegacy("Images/16x16/Ajouter.png") == "action.add"
    assert ICONES.RoleDepuisLegacy("Images/16x16/Modifier.png") == "action.edit"
    assert ICONES.RoleDepuisLegacy("Images/16x16/Supprimer.png") == "action.delete"
    assert ICONES.RoleDepuisLegacy("Images/16x16/Actualiser.png") == "action.refresh"


def test_composites_non_mappes_par_defaut():
    assert ICONES.RoleDepuisLegacy("Images/16x16/Calendrier_ajout.png") is None
    assert ICONES.RoleDepuisLegacy("Images/16x16/Apercu_fusion_emails.png") is None


def test_taille_est_rabattue_sur_une_taille_du_pack():
    assert ICONES._taille_depuis_chemin("Images/16x16/Ajouter.png") == 16
    assert ICONES._taille_depuis_chemin("Images/48x48/Ajouter.png") == 32


def test_asset_pilote_est_vendore():
    source = Path(ICONES._svg_path("action.add", 16))
    assert source.is_file()
    assert "currentColor" in source.read_text(encoding="utf-8")


def test_interrupteur_legacy(monkeypatch):
    monkeypatch.setenv("PMSL_LEGACY_ICONS", "1")
    assert ICONES._disabled() is True
