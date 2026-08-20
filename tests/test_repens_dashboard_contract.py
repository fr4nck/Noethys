# -*- coding: utf-8 -*-
"""Contrats statiques de la première composition Repens Design."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


FILES = {
    "effectifs": ROOT / "noethys" / "Dlg" / "DLG_Effectifs.py",
    "messages": ROOT / "noethys" / "Ctrl" / "CTRL_Messages.py",
    "aujourdhui": ROOT / "noethys" / "Ctrl" / "CTRL_Ephemeride.py",
    "recherche": ROOT / "noethys" / "Ctrl" / "CTRL_Recherche_individus.py",
}


def _texte(cle):
    texte = FILES[cle].read_text(encoding="utf-8")
    ast.parse(texte)
    return texte


def test_pilotage_est_un_conteneur_responsive_et_non_un_notebook_brut():
    texte = _texte("effectifs")
    assert "class CTRL(wx.Panel)" in texte
    assert "Fréquentation & activités" in texte
    assert "wx.BoxSizer(wx.VERTICAL)" in texte
    assert "AUI_NB_BOTTOM" not in texte
    assert 'pane.Caption(_(u"Pilotage"))' in texte


def test_messages_sont_sans_quadrillage_blanc_et_ont_un_entete():
    texte = _texte("messages")
    assert "Messages & alertes" in texte
    assert "wx.LC_HRULES" not in texte
    assert "wx.LC_VRULES" not in texte
    assert 'GetCouleurRole("surface_container_lowest")' in texte


def test_aujourdhui_utilise_deux_surfaces_semantiques():
    texte = _texte("aujourdhui")
    assert "self.panel_jour" in texte
    assert "self.panel_echeances" in texte
    assert 'GetCouleurRole("surface_container_low")' in texte
    assert 'GetCouleurRole("surface_container")' in texte
    assert "wx.StaticLine" not in texte


def test_recherche_accueil_reste_search_first():
    texte = _texte("recherche")
    assert "BarreRechercheAccueil" in texte
    assert "EtatRecherche" in texte
    assert "LIMITE_RESULTATS_ACCUEIL = 30" in texte
    assert "AfficherEtatVide" in texte
    assert "Nouvelle famille" in texte
    assert "wx.LC_HRULES" not in texte
    assert "wx.LC_VRULES" not in texte
