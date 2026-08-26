# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLE = ROOT / "noethys" / "Utils" / "UTILS_StyleRepens.py"
TEXTES = ROOT / "noethys" / "Ctrl" / "CTRL_TexteRepens.py"
BANDEAU = ROOT / "noethys" / "Ctrl" / "CTRL_Bandeau.py"
FENETRE = ROOT / "noethys" / "Ctrl" / "CTRL_FenetreRepens.py"


ROLES = (
    "display",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "lead",
    "body_large", "body", "body_small",
    "label", "caption", "micro",
    "data_large",
)


CLASSES = (
    "Display",
    "H1", "H2", "H3", "H4", "H5", "H6",
    "Lead",
    "BodyLarge", "Body", "BodySmall",
    "Label", "Caption", "Micro",
    "DataLarge",
)


def test_gamme_typographique_repens_couvre_7_a_18_points():
    texte = STYLE.read_text(encoding="utf-8")
    for role in ROLES:
        assert '"%s"' % role in texte
    assert '"display": {"points": 18' in texte
    assert '"caption": {"points": 7' in texte
    assert '"micro": {"points": 7' in texte
    assert '"data_large": {"points": 16' in texte
    assert "UTILS_Interface.GetTailleTexte() / 100.0" in texte
    assert "points * facteur_texte" in texte


def test_ctrl_texte_expose_un_helper_pour_chaque_niveau():
    texte = TEXTES.read_text(encoding="utf-8")
    for classe in CLASSES:
        assert "class %s(" % classe in texte
    for role in ROLES:
        assert '"%s"' % role in texte
    assert "Style.normaliser_role_typographie" in texte


def test_reflow_ignore_une_largeur_deja_traitee():
    texte = TEXTES.read_text(encoding="utf-8")

    assert "self._last_wrap_width = None" in texte
    assert "largeur == self._last_wrap_width" in texte
    assert "self._last_wrap_width = largeur" in texte
    assert "self.Wrap(largeur)" in texte


def test_gabarits_utilisent_la_hierarchie_semantique():
    bandeau = BANDEAU.read_text(encoding="utf-8")
    fenetre = FENETRE.read_text(encoding="utf-8")
    assert "CTRL_TexteRepens.H1(" in bandeau
    assert 'role="lead"' in bandeau
    assert "CTRL_TexteRepens.H2(" in fenetre
    assert 'niveau="h3"' in fenetre


def test_anciens_alias_restent_compatibles_sans_devenir_la_reference():
    texte = STYLE.read_text(encoding="utf-8")
    assert '"title": {"alias": "h1"}' in texte
    assert '"section": {"alias": "h2"}' in texte
    assert '"bodylarge": "body_large"' in texte
    assert '"datalarge": "data_large"' in texte
