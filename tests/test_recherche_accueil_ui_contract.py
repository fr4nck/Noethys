# -*- coding: utf-8 -*-

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FICHIER = ROOT / "noethys" / "Ctrl" / "CTRL_Recherche_individus.py"


def source():
    texte = FICHIER.read_text(encoding="utf-8")
    ast.parse(texte)
    return texte


def test_recherche_accueil_est_search_first():
    texte = source()
    assert "class EtatRecherche(wx.Panel)" in texte
    assert "Rechercher une famille ou un individu" in texte
    assert "AfficherEtatVide" in texte
    assert "AfficherAucunResultat" in texte
    assert "AfficherResultats" in texte
    assert "LIMITE_RESULTATS_ACCUEIL = 30" in texte


def test_recherche_accueil_reste_responsive_et_sans_grille_agressive():
    texte = source()
    assert "wx.LC_HRULES" not in texte
    assert "wx.LC_VRULES" not in texte
    assert "wx.FlexGridSizer" not in texte
    assert "UTILS_ColonnesResponsive.Installer" in texte
    assert "UTILS_UIMetrics.action_target(\"standard\")" in texte


def test_actions_principales_sont_identifiables():
    texte = source()
    assert "Nouvelle famille" in texte
    assert "Voir tout" in texte
    assert 'UTILS_FluentIcons.GetBitmap("add"' in texte
