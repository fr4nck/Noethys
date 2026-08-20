#!/usr/bin/env python
# -*- coding: utf-8 -*-

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "noethys" / "Utils" / "UTILS_Portail_contenus.py"
SPEC = importlib.util.spec_from_file_location("UTILS_Portail_contenus", MODULE_PATH)
PORTAIL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PORTAIL)


def test_url_externe_accepte_uniquement_http_et_https():
    assert PORTAIL.url_externe_valide("https://phototheque.example.org/album/12") is True
    assert PORTAIL.url_externe_valide("http://example.org/feed") is True
    assert PORTAIL.url_externe_valide("javascript:alert(1)") is False
    assert PORTAIL.url_externe_valide("file:///tmp/test.html") is False
    assert PORTAIL.url_externe_valide("example.org/sans-schema") is False


def test_iframe_est_responsive_et_echappe_les_attributs():
    html = PORTAIL.construire_iframe({
        "url": "https://example.org/view?x=1&y=2",
        "hauteur": 826,
        "defilement": False,
        "plein_ecran": True,
        "titre": 'Photothèque "été"',
    })

    assert 'src="https://example.org/view?x=1&amp;y=2"' in html
    assert 'width="100%"' in html
    assert 'height="826"' in html
    assert 'scrolling="no"' in html
    assert 'title="Photothèque &quot;été&quot;"' in html
    assert " allowfullscreen" in html
    assert "javascript:" not in html


def test_hauteur_est_bornee_et_serialisation_est_stable():
    assert PORTAIL.normaliser_hauteur(50) == PORTAIL.HAUTEUR_MIN
    assert PORTAIL.normaliser_hauteur(9999) == PORTAIL.HAUTEUR_MAX
    assert PORTAIL.normaliser_hauteur("invalide") == PORTAIL.HAUTEUR_DEFAUT

    brut = PORTAIL.serialiser_parametres({
        "url": " https://example.org/widget ",
        "hauteur": "700",
        "defilement": 1,
    })
    relu = PORTAIL.deserialiser_parametres(brut)

    assert relu["url"] == "https://example.org/widget"
    assert relu["hauteur"] == 700
    assert relu["defilement"] is True
    assert relu["plein_ecran"] is True
    assert relu["version"] == 1


def test_categorie_locale_est_exportee_comme_bloc_texte_connecthys():
    assert PORTAIL.categorie_pour_connecthys("bloc_contenu_externe") == "bloc_texte"
    assert PORTAIL.categorie_pour_connecthys("bloc_blog") == "bloc_blog"
