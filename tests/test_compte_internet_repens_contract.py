# -*- coding: utf-8 -*-
"""Contrat UI du résumé compte internet."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Ctrl" / "CTRL_Compte_internet.py"


def _source():
    return SOURCE.read_text(encoding="utf-8")


def test_source_reste_native_et_semantique():
    source = _source()
    ast.parse(source)
    assert "class CTRL(wx.Panel)" in source
    assert "UTILS_Interface.GetCouleurRole" in source
    assert "UTILS_UIMetrics" in source
    assert "wx.BoxSizer" in source
    assert "StaticText" in source
    assert "HtmlWindow" not in source
    assert "SetPage(" not in source
    assert "Images/16x16" not in source


def test_api_metier_historique_est_conservee():
    tree = ast.parse(_source())
    classe = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "CTRL")
    methods = {node.name for node in classe.body if isinstance(node, ast.FunctionDef)}
    for nom in (
        "SetDonnees",
        "GetDonnees",
        "MAJ",
        "GetIdentifiant",
        "GetMdp",
        "Modifier",
        "Envoyer_pressepapiers",
    ):
        assert nom in methods


def test_reflow_reagit_a_la_largeur():
    source = _source()
    assert "wx.EVT_SIZE" in source
    assert "Wrap(" in source
    assert "GetClientSize" in source
