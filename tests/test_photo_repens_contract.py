# -*- coding: utf-8 -*-
"""Contrat structurel du contrôle photo individuel modernisé."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Ctrl" / "CTRL_Photo.py"


def _source():
    return SOURCE.read_text(encoding="utf-8")


def _classe():
    tree = ast.parse(_source())
    return next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "CTRL_Photo")


def test_api_photo_historique_est_conservee():
    methods = {node.name for node in _classe().body if isinstance(node, ast.FunctionDef)}
    for nom in (
        "GetImageBase64",
        "SetPhoto",
        "GetIDphoto",
        "MenuPhoto",
        "Ajoute_image",
        "ChargeEditeurPhoto",
        "Capture_image",
        "Menu_Supprimer",
    ):
        assert nom in methods


def test_moteur_photo_reste_branche_aux_sources_historiques():
    source = _source()
    assert 'GestionDB.DB(suffixe="PHOTOS")' in source
    assert "DLG_Editeur_photo" in source
    assert "DLG_Capture_video_opencv_2" in source
    assert "base64.b64encode" in source
    assert "base64.b64decode" in source


def test_chrome_photo_est_semantique():
    source = _source()
    assert "UTILS_Interface.GetCouleurRole" in source
    assert "UTILS_IconesRepens.GetBitmap" in source
    assert "UTILS_UIMetrics" in source
    assert "wx.Colour(0, 0, 0)" not in source
    assert "Images/16x16/Importer_photo.png" not in source
    assert "Images/16x16/Webcam.png" not in source
    assert "Images/16x16/Supprimer.png" not in source


def test_menu_ne_rebind_pas_les_actions_a_chaque_ouverture():
    source = _source()
    init = next(node for node in _classe().body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
    menu = next(node for node in _classe().body if isinstance(node, ast.FunctionDef) and node.name == "MenuPhoto")
    init_text = ast.get_source_segment(source, init)
    menu_text = ast.get_source_segment(source, menu)
    assert "EVT_MENU" in init_text
    assert "EVT_MENU" not in menu_text
