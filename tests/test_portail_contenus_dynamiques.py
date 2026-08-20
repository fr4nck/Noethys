#!/usr/bin/env python
# -*- coding: utf-8 -*-

import importlib.util
import unittest
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


class PortailContenusDynamiquesTests(unittest.TestCase):

    def test_url_externe_accepte_uniquement_http_et_https(self):
        self.assertTrue(PORTAIL.url_externe_valide("https://phototheque.example.org/album/12"))
        self.assertTrue(PORTAIL.url_externe_valide("http://example.org/feed"))
        self.assertFalse(PORTAIL.url_externe_valide("javascript:alert(1)"))
        self.assertFalse(PORTAIL.url_externe_valide("file:///tmp/test.html"))
        self.assertFalse(PORTAIL.url_externe_valide("example.org/sans-schema"))

    def test_iframe_est_responsive_et_echappe_les_attributs(self):
        rendu = PORTAIL.construire_iframe({
            "url": "https://example.org/view?x=1&y=2",
            "hauteur": 826,
            "defilement": False,
            "plein_ecran": True,
            "titre": 'Photothèque "été"',
        })
        self.assertIn('src="https://example.org/view?x=1&amp;y=2"', rendu)
        self.assertIn('width="100%"', rendu)
        self.assertIn('height="826"', rendu)
        self.assertIn('scrolling="no"', rendu)
        self.assertIn('title="Photothèque &quot;été&quot;"', rendu)
        self.assertIn(" allowfullscreen", rendu)
        self.assertNotIn("javascript:", rendu)

    def test_hauteur_est_bornee_et_serialisation_est_stable(self):
        self.assertEqual(PORTAIL.normaliser_hauteur(50), PORTAIL.HAUTEUR_MIN)
        self.assertEqual(PORTAIL.normaliser_hauteur(9999), PORTAIL.HAUTEUR_MAX)
        self.assertEqual(PORTAIL.normaliser_hauteur("invalide"), PORTAIL.HAUTEUR_DEFAUT)
        brut = PORTAIL.serialiser_parametres({
            "url": " https://example.org/widget ",
            "hauteur": "700",
            "defilement": 1,
        })
        relu = PORTAIL.deserialiser_parametres(brut)
        self.assertEqual(relu["source"], PORTAIL.MARQUEUR_CONTENU_EXTERNE)
        self.assertEqual(relu["url"], "https://example.org/widget")
        self.assertEqual(relu["hauteur"], 700)
        self.assertTrue(relu["defilement"])
        self.assertTrue(relu["plein_ecran"])
        self.assertEqual(relu["version"], 1)
        self.assertTrue(PORTAIL.est_configuration_contenu_externe(brut))
        self.assertFalse(PORTAIL.est_configuration_contenu_externe('{"foo":"bar"}'))
        self.assertFalse(PORTAIL.est_configuration_contenu_externe("ancien paramètre"))

    def test_categorie_locale_est_exportee_comme_bloc_texte_connecthys(self):
        self.assertEqual(PORTAIL.categorie_pour_connecthys("bloc_contenu_externe"), "bloc_texte")
        self.assertEqual(PORTAIL.categorie_pour_connecthys("bloc_blog"), "bloc_blog")

    def test_rss_est_parse_en_texte_sur_et_limite(self):
        articles = PORTAIL.parser_flux_rss_atom(RSS_EXEMPLE)
        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0]["titre"], "Stage & vacances")
        self.assertEqual(articles[0]["lien"], "https://example.org/stage?x=1&y=2")
        self.assertEqual(articles[0]["date"], "20/08/2026")
        self.assertNotIn("<strong>", articles[0]["extrait"])
        self.assertNotIn("<script>", articles[0]["extrait"])
        self.assertIn("stage", articles[0]["extrait"])
        self.assertEqual(articles[1]["lien"], "")

        rendu = PORTAIL.construire_flux_html({
            "type": "rss",
            "url": "https://example.org/feed",
            "nombre_articles": 1,
            "afficher_date": True,
            "afficher_extrait": True,
            "liens_nouvel_onglet": True,
        }, contenu=RSS_EXEMPLE)
        self.assertIn("Stage &amp; vacances", rendu)
        self.assertNotIn("Deuxieme actualite", rendu)
        self.assertIn('href="https://example.org/stage?x=1&amp;y=2"', rendu)
        self.assertIn('target="_blank"', rendu)
        self.assertIn("20/08/2026", rendu)
        self.assertNotIn("<script>", rendu)

    def test_atom_est_parse_et_rendu_sans_html_externe(self):
        articles = PORTAIL.parser_flux_rss_atom(ATOM_EXEMPLE)
        self.assertEqual(articles, [{
            "titre": "Actualite Atom",
            "lien": "https://example.org/atom",
            "extrait": "Resume Atom",
            "date": "20/08/2026",
        }])
        rendu = PORTAIL.construire_flux_html({
            "type": "rss",
            "url": "https://example.org/atom.xml",
            "afficher_date": False,
            "afficher_extrait": False,
        }, contenu=ATOM_EXEMPLE)
        self.assertIn("Actualite Atom", rendu)
        self.assertNotIn("Resume Atom", rendu)
        self.assertNotIn("20/08/2026", rendu)

    def test_configuration_rss_est_dynamique_et_bornee(self):
        brut = PORTAIL.serialiser_parametres({
            "type": "rss",
            "url": "https://example.org/feed",
            "nombre_articles": 999,
        })
        config = PORTAIL.deserialiser_parametres(brut)
        self.assertEqual(config["type"], PORTAIL.TYPE_RSS)
        self.assertEqual(config["nombre_articles"], PORTAIL.RSS_NOMBRE_MAX)
        self.assertTrue(PORTAIL.est_configuration_dynamique(brut))
        iframe = PORTAIL.serialiser_parametres({
            "type": "iframe",
            "url": "https://example.org/widget",
        })
        self.assertFalse(PORTAIL.est_configuration_dynamique(iframe))

    def test_flux_invalide_est_refuse(self):
        with self.assertRaisesRegex(ValueError, "non pris en charge"):
            PORTAIL.parser_flux_rss_atom(b"<html><body>pas un flux</body></html>")


if __name__ == "__main__":
    unittest.main()
