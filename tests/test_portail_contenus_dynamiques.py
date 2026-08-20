#!/usr/bin/env python
# -*- coding: utf-8 -*-

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "noethys" / "Utils" / "UTILS_Portail_contenus.py"
SPEC = importlib.util.spec_from_file_location("UTILS_Portail_contenus", MODULE_PATH)
PORTAIL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PORTAIL)


RSS_EXEMPLE = b'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Pele-Mele</title>
    <item>
      <title>Stage &amp; vacances</title>
      <link>https://example.org/stage?x=1&amp;y=2</link>
      <description><![CDATA[<p>Un <strong>stage</strong> pour les enfants.</p><script>alert(1)</script>]]></description>
      <pubDate>Thu, 20 Aug 2026 12:30:00 +0200</pubDate>
    </item>
    <item>
      <title>Deuxieme actualite</title>
      <link>javascript:alert(1)</link>
      <description>Texte simple</description>
    </item>
  </channel>
</rss>'''

ATOM_EXEMPLE = b'''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Pele-Mele</title>
  <entry>
    <title>Actualite Atom</title>
    <link href="https://example.org/atom" rel="alternate" />
    <updated>2026-08-20T12:30:00+02:00</updated>
    <summary type="html">&lt;p&gt;Resume Atom&lt;/p&gt;</summary>
  </entry>
</feed>'''


def test_url_externe_accepte_uniquement_http_et_https():
    assert PORTAIL.url_externe_valide("https://phototheque.example.org/album/12") is True
    assert PORTAIL.url_externe_valide("http://example.org/feed") is True
    assert PORTAIL.url_externe_valide("javascript:alert(1)") is False
    assert PORTAIL.url_externe_valide("file:///tmp/test.html") is False
    assert PORTAIL.url_externe_valide("example.org/sans-schema") is False


def test_iframe_est_responsive_et_echappe_les_attributs():
    rendu = PORTAIL.construire_iframe({
        "url": "https://example.org/view?x=1&y=2",
        "hauteur": 826,
        "defilement": False,
        "plein_ecran": True,
        "titre": 'Photothèque "été"',
    })

    assert 'src="https://example.org/view?x=1&amp;y=2"' in rendu
    assert 'width="100%"' in rendu
    assert 'height="826"' in rendu
    assert 'scrolling="no"' in rendu
    assert 'title="Photothèque &quot;été&quot;"' in rendu
    assert " allowfullscreen" in rendu
    assert "javascript:" not in rendu


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

    assert relu["source"] == PORTAIL.MARQUEUR_CONTENU_EXTERNE
    assert relu["url"] == "https://example.org/widget"
    assert relu["hauteur"] == 700
    assert relu["defilement"] is True
    assert relu["plein_ecran"] is True
    assert relu["version"] == 1
    assert PORTAIL.est_configuration_contenu_externe(brut) is True
    assert PORTAIL.est_configuration_contenu_externe('{"foo":"bar"}') is False
    assert PORTAIL.est_configuration_contenu_externe("ancien paramètre") is False


def test_categorie_locale_est_exportee_comme_bloc_texte_connecthys():
    assert PORTAIL.categorie_pour_connecthys("bloc_contenu_externe") == "bloc_texte"
    assert PORTAIL.categorie_pour_connecthys("bloc_blog") == "bloc_blog"


def test_rss_est_parse_en_texte_sur_et_limite():
    articles = PORTAIL.parser_flux_rss_atom(RSS_EXEMPLE)
    assert len(articles) == 2
    assert articles[0]["titre"] == "Stage & vacances"
    assert articles[0]["lien"] == "https://example.org/stage?x=1&y=2"
    assert articles[0]["date"] == "20/08/2026"
    assert "<strong>" not in articles[0]["extrait"]
    assert "<script>" not in articles[0]["extrait"]
    assert "stage" in articles[0]["extrait"]
    assert articles[1]["lien"] == ""

    rendu = PORTAIL.construire_flux_html({
        "type": "rss",
        "url": "https://example.org/feed",
        "nombre_articles": 1,
        "afficher_date": True,
        "afficher_extrait": True,
        "liens_nouvel_onglet": True,
    }, contenu=RSS_EXEMPLE)

    assert "Stage &amp; vacances" in rendu
    assert "Deuxieme actualite" not in rendu
    assert 'href="https://example.org/stage?x=1&amp;y=2"' in rendu
    assert 'target="_blank"' in rendu
    assert "20/08/2026" in rendu
    assert "<script>" not in rendu
    assert "alert(1)" in rendu  # contenu traité comme texte, jamais comme script


def test_atom_est_parse_et_rendu_sans_html_externe():
    articles = PORTAIL.parser_flux_rss_atom(ATOM_EXEMPLE)
    assert articles == [{
        "titre": "Actualite Atom",
        "lien": "https://example.org/atom",
        "extrait": "Resume Atom",
        "date": "20/08/2026",
    }]

    rendu = PORTAIL.construire_flux_html({
        "type": "rss",
        "url": "https://example.org/atom.xml",
        "afficher_date": False,
        "afficher_extrait": False,
    }, contenu=ATOM_EXEMPLE)
    assert "Actualite Atom" in rendu
    assert "Resume Atom" not in rendu
    assert "20/08/2026" not in rendu


def test_configuration_rss_est_dynamique_et_bornee():
    brut = PORTAIL.serialiser_parametres({
        "type": "rss",
        "url": "https://example.org/feed",
        "nombre_articles": 999,
    })
    config = PORTAIL.deserialiser_parametres(brut)
    assert config["type"] == PORTAIL.TYPE_RSS
    assert config["nombre_articles"] == PORTAIL.RSS_NOMBRE_MAX
    assert PORTAIL.est_configuration_dynamique(brut) is True

    iframe = PORTAIL.serialiser_parametres({
        "type": "iframe",
        "url": "https://example.org/widget",
    })
    assert PORTAIL.est_configuration_dynamique(iframe) is False


def test_flux_invalide_est_refuse():
    try:
        PORTAIL.parser_flux_rss_atom(b"<html><body>pas un flux</body></html>")
    except ValueError as err:
        assert "non pris en charge" in str(err)
    else:
        raise AssertionError("Un document HTML ne doit pas être accepté comme RSS/Atom")
