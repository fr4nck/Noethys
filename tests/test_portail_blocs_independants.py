#!/usr/bin/env python
# -*- coding: utf-8 -*-

import importlib.util
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
if str(NOETHYS) not in sys.path:
    sys.path.insert(0, str(NOETHYS))

from Utils import UTILS_Portail_blocs as BLOCS
from Utils import UTILS_Portail_contenus
from Utils import UTILS_Portail_tarifs_bloc


class PortailBlocsIndependantsTests(unittest.TestCase):

    def test_contenu_externe_et_tarifs_sont_deux_types_ui_distincts(self):
        self.assertNotEqual(BLOCS.CODE_CONTENU_EXTERNE, BLOCS.CODE_TARIFS)
        self.assertIn(BLOCS.CODE_CONTENU_EXTERNE, BLOCS.CODES_VIRTUELS)
        self.assertIn(BLOCS.CODE_TARIFS, BLOCS.CODES_VIRTUELS)

    def test_les_deux_types_restent_des_blocs_texte_connecthys(self):
        self.assertEqual(BLOCS.categorie_persistante(BLOCS.CODE_CONTENU_EXTERNE), BLOCS.CODE_TEXTE)
        self.assertEqual(BLOCS.categorie_persistante(BLOCS.CODE_TARIFS), BLOCS.CODE_TEXTE)
        self.assertEqual(BLOCS.categorie_persistante("bloc_blog"), "bloc_blog")

    def test_un_bloc_existant_est_rouvert_dans_le_bon_editeur(self):
        iframe = UTILS_Portail_contenus.serialiser_parametres({
            "type": "iframe",
            "url": "https://example.org/widget",
        })
        tarifs = UTILS_Portail_tarifs_bloc.serialiser_configuration({
            "mode": "auto",
            "titre": "Tarifs",
        })
        self.assertEqual(BLOCS.detecter_code({
            "categorie": "bloc_texte",
            "elements": [{"parametres": iframe}],
        }), BLOCS.CODE_CONTENU_EXTERNE)
        self.assertEqual(BLOCS.detecter_code({
            "categorie": "bloc_texte",
            "elements": [{"parametres": tarifs}],
        }), BLOCS.CODE_TARIFS)
        self.assertEqual(BLOCS.detecter_code({
            "categorie": "bloc_texte",
            "elements": [{"parametres": None}],
        }), BLOCS.CODE_TEXTE)

    def test_editeur_contenu_externe_ne_contient_plus_les_tarifs(self):
        texte = (NOETHYS / "Ctrl" / "CTRL_Portail_contenu_externe.py").read_text(encoding="utf-8")
        self.assertNotIn("CTRL_Portail_tarifs", texte)
        self.assertNotIn("Tarifs Noethys", texte)
        self.assertNotIn("TYPE_TARIFS", texte)


if __name__ == "__main__":
    unittest.main()
