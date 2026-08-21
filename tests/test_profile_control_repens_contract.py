# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FICHIER = ROOT / "noethys" / "Ctrl" / "CTRL_Profil.py"


def test_selecteur_profils_utilise_les_actions_repens():
    texte = FICHIER.read_text(encoding="utf-8")
    assert "CTRL_ActionRepens" in texte
    assert "FlexGridSizer" not in texte
    assert "BitmapButton" not in texte
    assert "Images/16x16" not in texte
    assert "UTILS_UIMetrics.action_target" in texte


def test_selecteur_profils_conserve_son_api_metier():
    texte = FICHIER.read_text(encoding="utf-8")
    for methode in (
        "GetIDprofil",
        "SetOnDefaut",
        "OnChoixProfil",
        "Enregistrer",
        "ViderProfil",
        "Envoyer_parametres",
        "Recevoir_parametres",
    ):
        assert "def %s" % methode in texte
