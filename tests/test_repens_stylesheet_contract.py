# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE = ROOT / "noethys" / "Utils" / "UTILS_StyleRepens.py"
SHELL = ROOT / "noethys" / "Ctrl" / "CTRL_FenetreRepens.py"
ACTION = ROOT / "noethys" / "Ctrl" / "CTRL_ActionRepens.py"
SURFACE = ROOT / "noethys" / "Ctrl" / "CTRL_SurfaceRepens.py"
BANDEAU = ROOT / "noethys" / "Ctrl" / "CTRL_Bandeau.py"
PRELEVEMENT = ROOT / "noethys" / "Dlg" / "DLG_Active_prelevement.py"
CALENDRIER = ROOT / "noethys" / "Dlg" / "DLG_Activite_calendrier.py"


def test_style_repens_est_le_point_entree_css_de_noethys():
    texte = STYLE.read_text(encoding="utf-8")
    assert "Façade de style unique" in texte
    assert "RAYONS =" in texte
    assert "TYPOGRAPHIES =" in texte
    for api in (
        "def couleur(",
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


def test_composants_repens_communs_passent_par_la_facade_de_style():
    for fichier in (ACTION, SURFACE, BANDEAU, SHELL):
        texte = fichier.read_text(encoding="utf-8")
        assert "UTILS_StyleRepens as Style" in texte
        assert "wx.Colour(" not in texte

    action = ACTION.read_text(encoding="utf-8")
    surface = SURFACE.read_text(encoding="utf-8")
    bandeau = BANDEAU.read_text(encoding="utf-8")
    assert "UTILS_Interface" not in action
    assert "UTILS_UIMetrics" not in action
    assert "UTILS_Interface" not in surface
    assert "UTILS_UIMetrics" not in surface
    assert "UTILS_Interface" not in bandeau
    assert "UTILS_UIMetrics" not in bandeau


def test_shell_repens_centralise_dialogue_frame_sections_et_footer():
    texte = SHELL.read_text(encoding="utf-8")
    for classe in (
        "class Section(",
        "class BarreActions(",
        "class Dialog(wx.Dialog)",
        "class Frame(wx.Frame)",
    ):
        assert classe in texte
    assert "wx.RESIZE_BORDER" in texte
    assert "wx.MAXIMIZE_BOX" in texte
    assert "wx.MINIMIZE_BOX" in texte
    assert "FlexGridSizer" not in texte
    assert "BitmapButton" not in texte
    assert "StaticBox" not in texte
    assert "SendSizeEvent" not in texte


def test_premieres_fenetres_metier_consument_le_shell_commun():
    prelevement = PRELEVEMENT.read_text(encoding="utf-8")
    calendrier = CALENDRIER.read_text(encoding="utf-8")

    assert "class Dialog(CTRL_FenetreRepens.Dialog)" in prelevement
    assert "self.AjouterSection(" in prelevement
    assert "self.AjouterAction(" in prelevement
    assert "FlexGridSizer" not in prelevement
    assert "BitmapButton" not in prelevement
    assert "StaticBox" not in prelevement

    assert "CTRL_FenetreRepens.Section" in calendrier
    assert "CTRL_ActionRepens.CTRL" in calendrier
    assert "FlexGridSizer" not in calendrier
    assert "BitmapButton" not in calendrier
    assert "StaticBox" not in calendrier
