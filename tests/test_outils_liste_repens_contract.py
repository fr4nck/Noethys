# -*- coding: utf-8 -*-
"""Contrat structurel de la barre commune ObjectListView Repens."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Ctrl" / "CTRL_OutilsListeRepens.py"


def _source():
    return SOURCE.read_text(encoding="utf-8")


def _tree():
    return ast.parse(_source())


def _class(name):
    for node in _tree().body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise AssertionError("Classe %s introuvable" % name)


def _methods(class_name):
    return {node.name for node in _class(class_name).body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def test_barre_recherche_conserve_api_historique():
    methods = _methods("BarreRecherche")
    for name in ("OnSearch", "OnCancel", "OnDoSearch", "Cancel", "Recherche"):
        assert name in methods


def test_ctrl_supporte_filtres_cochage_et_regroupement():
    methods = _methods("CTRL")
    for name in (
        "MAJ_ctrl_filtrer",
        "SetFiltres",
        "OnBoutonFiltrer",
        "OnBoutonCocher",
        "OnMenu",
    ):
        assert name in methods

    init = next(node for node in _class("CTRL").body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
    args = [arg.arg for arg in init.args.args]
    assert "afficherCocher" in args
    assert "afficherRegroupement" in args
    assert "style" in args


def test_regroupement_reste_compatible_avec_objectlistview():
    methods = _methods("CTRL_Regroupement")
    for name in ("MAJ", "GetTitresColonnes", "GetRegroupement", "OnChoix"):
        assert name in methods


def test_barre_reste_repens_sans_chrome_historique():
    source = _source()
    assert "CTRL_ActionRepens.CTRL" in source
    assert "wx.BoxSizer" in source
    assert "UTILS_UIMetrics.action_target" in source
    assert "PlateButton" not in source
    assert "BitmapButton" not in source
    assert "FlexGridSizer" not in source
    assert "Images/16x16" not in source


def test_commandes_historiques_sont_toutes_presentes():
    source = _source()
    for token in (
        "ID_FILTRES_GERER",
        "ID_FILTRES_EFFACER",
        "ID_COCHER_TOUT",
        "ID_DECOCHER_TOUT",
        "CocheListeTout",
        "CocheListeRien",
        "ctrl_regroupement",
    ):
        assert token in source
