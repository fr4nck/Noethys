# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DLG = ROOT / "noethys" / "Dlg"


def _texte(nom):
    return (DLG / nom).read_text(encoding="utf-8")


def test_cockpit_branche_les_enveloppes_repens():
    texte = _texte("DLG_Effectifs.py")
    assert "DLG_Nbre_inscrits_Repens" in texte
    assert "DLG_Recap_evenements_Repens" in texte
    assert "DLG_Tableau_bord_locations_Repens" in texte


def test_inscriptions_ne_reconstruit_pas_la_vieille_toolbar():
    texte = _texte("DLG_Nbre_inscrits_Repens.py")
    assert "legacy.Panel.__init__" not in texte
    assert "FlexGridSizer" not in texte
    assert "BitmapButton" not in texte
    assert "Images/16x16" not in texte
    assert "CTRL_ActionRepens" in texte
    assert "UTILS_HyperTreeRepens.Configurer" in texte


def test_evenements_ne_reconstruit_pas_la_vieille_toolbar():
    texte = _texte("DLG_Recap_evenements_Repens.py")
    assert "legacy.Panel.__init__" not in texte
    assert "FlexGridSizer" not in texte
    assert "BitmapButton" not in texte
    assert "Images/16x16" not in texte
    assert "_GetDashboard" in texte
    assert "UTILS_HyperTreeRepens.Configurer" in texte


def test_locations_abandonne_le_toolbook_a_icones_32px():
    texte = _texte("DLG_Tableau_bord_locations_Repens.py")
    assert "wx.Toolbook" not in texte
    assert "ImageList" not in texte
    assert "Images/32x32" not in texte
    assert "aui.AuiNotebook" in texte
    assert "UTILS_Aui.ConfigurerNotebook" in texte
