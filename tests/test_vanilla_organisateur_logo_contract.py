from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACCUEIL = ROOT / "noethys" / "Ctrl" / "CTRL_Accueil.py"
ORGANISATEUR = ROOT / "noethys" / "Utils" / "UTILS_Organisateur.py"


def test_accueil_reuses_existing_organisateur_logo_pipeline():
    source = ACCUEIL.read_text(encoding="utf-8")
    assert "UTILS_Organisateur.GetDonnees(tailleLogo=(80, 80))" in source
    assert '.get("logo")' in source
    assert "self.logo_organisateur.IsOk()" in source


def test_logo_rescaling_preserves_aspect_ratio_for_wide_and_tall_images():
    source = ORGANISATEUR.read_text(encoding="utf-8")
    # Wide images: constrain width and derive height from the original ratio.
    assert "hauteur = int(hauteur * tailleMaxi / largeur)" in source
    # Tall images: constrain height and derive width from the original ratio.
    assert "largeur = int(largeur * tailleMaxi / hauteur)" in source
    assert "quality=wx.IMAGE_QUALITY_HIGH" in source


def test_logo_is_not_upscaled_when_already_smaller_than_target():
    source = ORGANISATEUR.read_text(encoding="utf-8")
    assert "if max(largeur, hauteur) > tailleMaxi" in source
    assert "largeur = int(largeur)" in source
    assert "hauteur = int(hauteur)" in source
