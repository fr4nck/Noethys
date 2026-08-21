# -*- coding: utf-8 -*-
"""Contrat UI du sélecteur d'image métier."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Ctrl" / "CTRL_Image_mode.py"


def _source():
    return SOURCE.read_text(encoding="utf-8")


def _methods(class_name):
    tree = ast.parse(_source())
    classe = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    return {node.name for node in classe.body if isinstance(node, ast.FunctionDef)}


def test_ctrl_conserve_api_metier_image():
    for nom in ("GetPhoto", "GetImageDefaut", "Ajouter", "Supprimer", "Sauvegarder"):
        assert nom in _methods("CTRL")


def test_format_source_est_separe_du_rendu_dpi():
    source = _source()
    assert "tailleImageSource" in source
    assert "_TailleAffichage" in source
    assert "UTILS_UIMetrics.px" in source
    assert "tailleCadre=self.tailleImageSource" in source


def test_chrome_historique_a_disparu():
    source = _source()
    ast.parse(source)
    assert "CTRL_ActionRepens.CTRL" in source
    assert "UTILS_Interface.GetCouleurRole" in source
    assert "wx.BoxSizer" in source
    assert "wx.BitmapButton" not in source
    assert "wx.Colour(0, 0, 0)" not in source
    assert "Images/16x16" not in source
