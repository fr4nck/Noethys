# -*- coding: utf-8 -*-
"""Contrat UI des options d'édition des rappels."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Ctrl" / "CTRL_Rappels_options.py"


def _source():
    return SOURCE.read_text(encoding="utf-8")


def test_options_conservent_le_contrat_metier():
    tree = ast.parse(_source())
    classe = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "CTRL")
    methods = {node.name for node in classe.body if isinstance(node, ast.FunctionDef)}
    for nom in ("OnBoutonModele", "OnCheckRepertoire", "OnBoutonRepertoire", "MemoriserParametres", "GetOptions"):
        assert nom in methods
    source = _source()
    for cle in ("codeBarre", "coupon", "IDmodele", "repertoire"):
        assert '"%s"' % cle in source


def test_layout_est_reellement_fluide():
    source = _source()
    assert "wx.BoxSizer" in source
    assert "CTRL_ActionRepens.CTRL" in source
    assert "UTILS_UIMetrics.action_target" in source
    assert "FlexGridSizer" not in source
    assert "BitmapButton" not in source
    assert "Images/16x16" not in source
    assert "SetMinSize((270" not in source


def test_lecture_repertoire_appelle_bien_getvalue():
    source = _source()
    assert "self.ctrl_repertoire.GetValue()" in source
    assert "self.ctrl_repertoire.GetValue !=" not in source
