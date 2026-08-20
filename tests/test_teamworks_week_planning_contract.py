#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
from pathlib import Path


def _read(path):
    root = Path(__file__).resolve().parents[1]
    texte = (root / path).read_text(encoding="utf-8")
    ast.parse(texte)
    return texte


def test_teamworks_reader_is_read_only_and_uses_real_presence_table():
    texte = _read("noethys/Utils/UTILS_Teamworks_Planning.py")
    assert "mode=ro" in texte
    assert "FROM presences AS p" in texte
    assert "LEFT JOIN personnes" in texte
    assert "LEFT JOIN cat_presences" in texte
    assert "INSERT " not in texte
    assert "UPDATE " not in texte
    assert "DELETE " not in texte


def test_week_view_is_dense_responsive_grid():
    texte = _read("noethys/Ctrl/CTRL_Planning_semaine.py")
    assert "wx.grid" in texte
    assert "CreateGrid(0, 8)" in texte
    assert "EnableEditing(False)" in texte
    assert "GetFacteurEcran" in texte
    assert "Source Teamworks" in texte
    assert ".Float()" not in texte


def test_home_individuals_view_does_not_create_civility_images():
    texte = _read("noethys/Ctrl/CTRL_Recherche_individus.py")
    bloc = texte.split("class ListeIndividusAccueil", 1)[1].split("class ToolBar", 1)[0]
    assert "AddNamedImages" not in bloc
    assert "imageGetter" not in bloc
    assert "État" in bloc
    assert "COLONNES_EXPANSIBLES" in bloc
