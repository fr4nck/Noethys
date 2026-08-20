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


if __name__ == "__main__":
    unittest.main()
