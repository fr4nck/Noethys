# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BANDEAU = ROOT / "noethys" / "Ctrl" / "CTRL_Bandeau.py"
TEXTE = ROOT / "noethys" / "Ctrl" / "CTRL_TexteRepens.py"


def test_bandeau_nutilise_plus_htmlwindow():
    texte = BANDEAU.read_text(encoding="utf-8")
    assert "HtmlWindow" not in texte
    assert "wx.html" not in texte
    assert "class TexteIntro(CTRL_TexteRepens.CTRL)" in texte
    assert "Reflow" in texte


def test_bandeau_consomme_h1_et_le_style_central():
    texte = BANDEAU.read_text(encoding="utf-8")
    assert "hauteurHtml" in texte
    assert "UTILS_StyleRepens as Style" in texte
    assert "CTRL_TexteRepens.H1" in texte
    assert 'role="body"' in texte
    assert "UTILS_Interface" not in texte
    assert "UTILS_UIMetrics" not in texte
    assert "EVT_SIZE" in texte


def test_texte_repens_expose_la_hierarchie_html_semantique():
    texte = TEXTE.read_text(encoding="utf-8")
    for role in ("h1", "h2", "h3", "h4", "h5", "h6", "body", "caption"):
        assert '"%s"' % role in texte
    assert "class H1(CTRL)" in texte
    assert "class H2(CTRL)" in texte
    assert "class H3(CTRL)" in texte
    assert "SetRole" in texte
    assert "SetFont(" not in texte
