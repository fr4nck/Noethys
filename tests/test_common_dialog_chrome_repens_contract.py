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


def test_bandeau_consomme_le_style_central_et_reflow():
    texte = BANDEAU.read_text(encoding="utf-8")
    assert "hauteurHtml reste accepté" in texte
    assert "UTILS_StyleRepens as Style" in texte
    assert "UTILS_Interface" not in texte
    assert "UTILS_UIMetrics" not in texte
    assert "EVT_SIZE" in texte
    assert "Reflow" in texte
    assert 'Style.police("title")' in texte
