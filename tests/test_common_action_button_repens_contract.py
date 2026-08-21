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


def test_bouton_commun_applique_les_etats_semantiques_en_clair_et_sombre():
    texte = FICHIER.read_text(encoding="utf-8")
    assert 'GetCouleurRole("surface_container_high")' in texte
    assert 'GetCouleurRole("surface_container_highest")' in texte
    assert 'GetEtatCouleurs("pressed")' in texte
    assert "if not sombre:" not in texte


def test_catalogue_repens_couvre_les_actions_de_dialogue():
    texte = ICONES.read_text(encoding="utf-8")
    for nom in ("help", "dismiss", "check", "filter"):
        assert '"%s"' % nom in texte
