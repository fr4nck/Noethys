# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANDEAU = ROOT / "noethys" / "Ctrl" / "CTRL_Bandeau.py"


def test_bandeau_nutilise_plus_htmlwindow():
    texte = BANDEAU.read_text(encoding="utf-8")
    assert "HtmlWindow" not in texte
    assert "wx.html" not in texte
    assert "class TexteIntro(wx.StaticText)" in texte
    assert "self.Wrap(" in texte


def test_bandeau_ne_fige_plus_la_hauteur_du_texte():
    texte = BANDEAU.read_text(encoding="utf-8")
    assert "hauteurHtml reste accepté" in texte
    assert "panel_min_height" in texte
    assert "EVT_SIZE" in texte
    assert "Reflow" in texte
