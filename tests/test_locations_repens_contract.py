# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_locations_utilise_les_commandes_repens():
    texte = _read("noethys/Dlg/DLG_Locations_Repens.py")
    assert "CTRL_ActionRepens" in texte
    assert "CTRL_OutilsListeRepens" in texte
    assert "FlexGridSizer" not in texte
    assert "BitmapButton" not in texte
    assert "SUNKEN_BORDER" not in texte
    assert "Images/16x16" not in texte


def test_demandes_locations_utilise_les_commandes_repens():
    texte = _read("noethys/Dlg/DLG_Locations_demandes_Repens.py")
    assert "CTRL_ActionRepens" in texte
    assert "CTRL_OutilsListeRepens" in texte
    assert "FlexGridSizer" not in texte
    assert "BitmapButton" not in texte
    assert "SUNKEN_BORDER" not in texte
    assert "Images/16x16" not in texte


def test_navigation_locations_branche_les_pages_repens():
    texte = _read("noethys/Dlg/DLG_Tableau_bord_locations_Repens.py")
    assert "DLG_Locations_Repens" in texte
    assert "DLG_Locations_demandes_Repens" in texte


def test_outils_liste_repens_ne_depend_plus_de_platebutton():
    texte = _read("noethys/Ctrl/CTRL_OutilsListeRepens.py")
    assert "platebtn" not in texte.lower()
    assert "Images/16x16" not in texte
    assert "CTRL_ActionRepens" in texte
