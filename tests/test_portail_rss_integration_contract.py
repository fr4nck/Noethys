#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVEUR = ROOT / "noethys" / "Ctrl" / "CTRL_Portail_serveur.py"
SYNC_HELPER = ROOT / "noethys" / "Utils" / "UTILS_Portail_contenus_synchro.py"


class PortailRSSIntegrationContractTests(unittest.TestCase):

    def test_serveur_actualise_les_contenus_avant_la_synchro_historique(self):
        serveur = SERVEUR.read_text(encoding="utf-8")
        helper = SYNC_HELPER.read_text(encoding="utf-8")

        self.assertIn("from Utils import UTILS_Portail_contenus_synchro", serveur)
        appel_preparation = serveur.index("UTILS_Portail_contenus_synchro.preparer_avant_synchro")
        appel_synchro = serveur.index("synchro.Synchro_totale()")
        self.assertLess(appel_preparation, appel_synchro)
        self.assertIn('nom="last_update_pages"', helper)
        self.assertIn("DB.Commit()", helper)
        self.assertIn("Dernière version conservée", helper)
        self.assertIn("WHERE parametres IS NOT NULL", helper)


if __name__ == "__main__":
    unittest.main()
