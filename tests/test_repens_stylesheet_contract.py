# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE = ROOT / "noethys" / "Utils" / "UTILS_StyleRepens.py"
SHELL = ROOT / "noethys" / "Ctrl" / "CTRL_FenetreRepens.py"
TEXT = ROOT / "noethys" / "Ctrl" / "CTRL_TexteRepens.py"
ACTION = ROOT / "noethys" / "Ctrl" / "CTRL_ActionRepens.py"
SURFACE = ROOT / "noethys" / "Ctrl" / "CTRL_SurfaceRepens.py"
BADGE = ROOT / "noethys" / "Ctrl" / "CTRL_BadgeRepens.py"
BANDEAU = ROOT / "noethys" / "Ctrl" / "CTRL_Bandeau.py"
PRELEVEMENT = ROOT / "noethys" / "Dlg" / "DLG_Active_prelevement.py"
RIB = ROOT / "noethys" / "Dlg" / "DLG_Saisie_rib.py"
CALENDRIER = ROOT / "noethys" / "Dlg" / "DLG_Activite_calendrier.py"


def test_style_repens_est_le_point_entree_css_de_noethys():
    texte = STYLE.read_text(encoding="utf-8")
    assert "Façade de style unique" in texte
    assert "RAYONS =" in texte
    assert "TYPOGRAPHIES =" in texte
    for api in (
        "def couleur(",
        "def etat(",
        "def espace(",
        "def rayon(",
        "def taille_icone(",
        "def police(",
        "def appliquer_fenetre(",
        "def appliquer_texte(",
        "def appliquer_saisie(",
        "def appliquer_liste(",
        "def tokens(",
    ):
        assert api in texte


def test_style_repens_expose_une_hierarchie_html_h1_a_h6():
    style = STYLE.read_text(encoding="utf-8")
    texte = TEXT.read_text(encoding="utf-8")
    for role in ("h1", "h2", "h3", "h4", "h5", "h6"):
        assert '"%s"' % role in style
        assert '"%s"' % role in texte
    assert '"title": {"alias": "h1"}' in style
    assert '"section": {"alias": "h2"}' in style
    assert "class H1(CTRL)" in texte
    assert "class H2(CTRL)" in texte
    assert "class H3(CTRL)" in texte
    assert "SetRole" in texte
    assert "UTILS_StyleRepens as Style" in texte


def test_composants_repens_communs_passent_par_la_facade_de_style():
    for fichier in (TEXT, ACTION, SURFACE, BADGE, BANDEAU, SHELL):
        texte = fichier.read_text(encoding="utf-8")
        assert "UTILS_StyleRepens as Style" in texte
        assert "wx.Colour(" not in texte

    for fichier in (TEXT, ACTION, SURFACE, BADGE, BANDEAU):
        texte = fichier.read_text(encoding="utf-8")
        assert "UTILS_Interface" not in texte
        assert "UTILS_UIMetrics" not in texte


def test_badge_repens_expose_les_etats_semantiques_du_mockup():
    texte = BADGE.read_text(encoding="utf-8")
    assert "class CTRL(wx.Control)" in texte
    assert '"succes": ("success", "success_text")' in texte
    assert '"attention": ("warning", "warning_text")' in texte
    assert '"danger": ("danger", "danger_text")' in texte
    assert '"info": ("info", "info_text")' in texte
    assert "DrawRoundedRectangle" in texte


def test_shell_repens_centralise_dialogue_frame_sections_et_footer():
    texte = SHELL.read_text(encoding="utf-8")
    for classe in (
        "class Section(",
        "class BarreActions(",
        "class Dialog(wx.Dialog)",
        "class Frame(wx.Frame)",
    ):
        assert classe in texte
    assert "CTRL_TexteRepens.H2" in texte
    assert 'niveau="h3"' in texte
    assert "wx.RESIZE_BORDER" in texte
    assert "wx.MAXIMIZE_BOX" in texte
    assert "wx.MINIMIZE_BOX" in texte
    assert "FlexGridSizer" not in texte
    assert "BitmapButton" not in texte
    assert "StaticBox" not in texte
    assert "SendSizeEvent" not in texte


def test_premieres_fenetres_metier_consument_le_shell_commun():
    prelevement = PRELEVEMENT.read_text(encoding="utf-8")
    rib = RIB.read_text(encoding="utf-8")
    calendrier = CALENDRIER.read_text(encoding="utf-8")

    for texte in (prelevement, rib):
        assert "class Dialog(CTRL_FenetreRepens.Dialog)" in texte
        assert "self.AjouterSection(" in texte
        assert "self.AjouterAction(" in texte
        assert "FlexGridSizer" not in texte
        assert "BitmapButton" not in texte
        assert "StaticBox" not in texte

    assert "CTRL_BadgeRepens.CTRL" in rib
    assert 'SetEtat(_(u"Coordonnées valides"), "succes")' in rib
    assert 'SetEtat(_(u"À vérifier"), "attention")' in rib
    assert "string.letters" not in rib

    assert "CTRL_FenetreRepens.Section" in calendrier
    assert "CTRL_ActionRepens.CTRL" in calendrier
    assert "FlexGridSizer" not in calendrier
    assert "BitmapButton" not in calendrier
    assert "StaticBox" not in calendrier
