# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FICHIER = ROOT / "noethys" / "Utils" / "UTILS_Dialogs.py"


def test_dialogues_sont_bornes_a_la_zone_de_travail():
    texte = FICHIER.read_text(encoding="utf-8")
    assert "wx.Display.GetFromWindow" in texte
    assert "GetClientArea" in texte
    assert "AjusteDansEcran" in texte
    assert "_LimiterTaille" in texte


def test_minima_historiques_peuvent_etre_reduits_sur_petit_ecran():
    texte = FICHIER.read_text(encoding="utf-8")
    assert "parent.SetMinSize" in texte
    assert "largeur_max" in texte
    assert "hauteur_max" in texte
    assert "AjusteDansEcran(parent)" in texte
