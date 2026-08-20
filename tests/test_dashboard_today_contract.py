#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
from pathlib import Path


def _source(path):
    root = Path(__file__).resolve().parents[1]
    texte = (root / path).read_text(encoding="utf-8")
    ast.parse(texte)
    return texte


def test_ephemeride_is_now_operational_dashboard():
    texte = _source("noethys/Ctrl/CTRL_Ephemeride.py")

    assert "wx.BoxSizer" in texte
    assert "Open-Meteo" in texte
    assert "Aujourd'hui / Échéancier" in texte
    assert "dashboard_echeances" in texte
    assert "wx.lib.analogclock" not in texte
    assert "CTRL_Newsticker" not in texte
    assert "LISTE_CITATIONS" not in texte
    assert ".Float()" not in texte


def test_individuals_panel_drops_legacy_flexgrid_and_avatar_width():
    texte = _source("noethys/Ctrl/CTRL_Recherche_individus.py")

    assert "wx.BoxSizer(wx.VERTICAL)" in texte
    assert "wx.FlexGridSizer" not in texte
    assert "wx.SUNKEN_BORDER" not in texte
    assert "SetColumnWidth(0, 0)" in texte


def test_aui_helpers_do_not_monkey_patch_wx_classes():
    texte = _source("noethys/Utils/UTILS_Aui.py")

    assert "AuiToolBar.__init__ =" not in texte
    assert "wx.ToolBar.SetToolBitmapSize =" not in texte
    assert "ConfigurerManager" in texte
    assert "AUI_DOCKART_SASH_SIZE" in texte
