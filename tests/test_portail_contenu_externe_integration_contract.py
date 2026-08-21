#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DLG = ROOT / "noethys" / "Dlg" / "DLG_Saisie_portail_bloc.py"
REGISTRE = ROOT / "noethys" / "Utils" / "UTILS_Portail_blocs.py"
CTRL_EXTERNE = ROOT / "noethys" / "Ctrl" / "CTRL_Portail_contenu_externe.py"


class PortailContenuExterneIntegrationContractTests(unittest.TestCase):

    def test_palette_expose_contenu_externe_et_tarifs_comme_blocs_independants(self):
        source = DLG.read_text(encoding="utf-8")
        registre = REGISTRE.read_text(encoding="utf-8")

        self.assertIn("CTRL_Portail_contenu_externe", source)
        self.assertIn("CTRL_Portail_tarifs", source)
        self.assertIn('_(u"Contenu externe")', source)
        self.assertIn('_(u"Tarifs Noethys")', source)
        self.assertIn("CODE_CONTENU_EXTERNE", source)
        self.assertIn("CODE_TARIFS", source)
        self.assertIn("categorie_persistante", source)
        self.assertIn("detecter_code", source)

        self.assertIn('CODE_TEXTE = "bloc_texte"', registre)
        self.assertIn("CODES_VIRTUELS", registre)
        self.assertIn("return CODE_TEXTE", registre)

    def test_controle_externe_stocke_configuration_et_html_dans_les_champs_existants(self):
        source = CTRL_EXTERNE.read_text(encoding="utf-8")

        self.assertIn('"parametres": UTILS_Portail_contenus.serialiser_parametres(config)', source)
        self.assertIn('"texte_html": UTILS_Portail_contenus.construire_iframe(config)', source)
        self.assertIn('"texte_xml": None', source)
        self.assertIn("url_externe_valide", source)


if __name__ == "__main__":
    unittest.main()
