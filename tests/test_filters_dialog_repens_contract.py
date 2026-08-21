# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FICHIER = ROOT / "noethys" / "Dlg" / "DLG_Filtres_listes.py"


def test_dialogue_filtres_abandonne_la_grille_et_les_petits_boutons():
    texte = FICHIER.read_text(encoding="utf-8")
    assert "FlexGridSizer" not in texte
    assert "BitmapButton" not in texte
    assert "SUNKEN_BORDER" not in texte
    assert "Images/16x16" not in texte
    assert "CTRL_ActionRepens" in texte


def test_profil_de_filtres_est_reellement_redimensionnable():
    texte = FICHIER.read_text(encoding="utf-8")
    assert "wx.SplitterWindow" in texte
    assert "SplitVertically" in texte
    assert "SetSashGravity" in texte
    assert "UTILS_Dialogs.AjusteDansEcran" in texte
