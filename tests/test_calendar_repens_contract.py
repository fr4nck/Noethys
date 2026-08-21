# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CTRL = ROOT / "noethys" / "Ctrl" / "CTRL_Calendrier_Repens.py"
DLG = ROOT / "noethys" / "Dlg" / "DLG_calendrier_simple.py"


def test_navigation_calendrier_est_reconstruite_en_repens():
    texte = CTRL.read_text(encoding="utf-8")
    assert "CTRL_ActionRepens" in texte
    assert "wx.BoxSizer" in texte
    assert "BitmapButton" not in texte
    assert "FlexGridSizer" not in texte
    assert "SpinButton" not in texte
    assert "Images/16x16" not in texte


def test_calendrier_utilise_des_roles_semantiques():
    texte = CTRL.read_text(encoding="utf-8")
    for role in (
        "surface_container_lowest",
        "surface_container_low",
        "selection",
        "focus",
        "on_surface",
    ):
        assert '"%s"' % role in texte


def test_selecteur_commun_branche_le_calendrier_repens():
    texte = DLG.read_text(encoding="utf-8")
    assert "CTRL_Calendrier_Repens as CTRL_Calendrier" in texte
    assert "FlexGridSizer" not in texte
    assert "UTILS_Dialogs.AjusteDansEcran" in texte
