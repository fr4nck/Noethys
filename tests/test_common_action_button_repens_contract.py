# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FICHIER = ROOT / "noethys" / "Ctrl" / "CTRL_Bouton_image.py"
ICONES = ROOT / "noethys" / "Utils" / "UTILS_IconesRepens.py"


def test_bouton_commun_utilise_le_catalogue_repens():
    texte = FICHIER.read_text(encoding="utf-8")
    assert "UTILS_IconesRepens" in texte
    assert "ICONES_ACTIONS_HISTORIQUES" in texte
    for nom in (
        "ajouter.png",
        "modifier.png",
        "supprimer.png",
        "aide.png",
        "fermer.png",
        "annuler.png",
        "valider.png",
        "filtre.png",
    ):
        assert nom in texte


def test_bouton_commun_consomme_le_css_repens_et_ses_etats():
    texte = FICHIER.read_text(encoding="utf-8")
    assert "UTILS_StyleRepens as Style" in texte
    assert 'Style.couleur("surface_container_high")' in texte
    assert 'Style.etat("pressed")' in texte
    assert 'Style.etat("hover")' in texte
    assert 'Style.etat("focus")' in texte
    assert 'Style.etat("disabled")' in texte
    assert 'Style.cible_action("standard")' in texte
    assert "UTILS_Interface" not in texte
    assert "UTILS_UIMetrics" not in texte


def test_catalogue_repens_couvre_les_actions_de_dialogue():
    texte = ICONES.read_text(encoding="utf-8")
    for nom in ("help", "dismiss", "check", "filter"):
        assert '"%s"' % nom in texte
