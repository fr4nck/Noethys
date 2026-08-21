#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CTRL_TARIFS = ROOT / "noethys" / "Ctrl" / "CTRL_Portail_tarifs.py"
CTRL_CONTENU = ROOT / "noethys" / "Ctrl" / "CTRL_Portail_contenu_externe.py"
SERVEUR = ROOT / "noethys" / "Ctrl" / "CTRL_Portail_serveur.py"


class PortailTarifsUIContractTests(unittest.TestCase):

    def test_interface_expose_automatique_manuel_et_apercu(self):
        texte = CTRL_TARIFS.read_text(encoding="utf-8")
        self.assertIn("Automatique (recommandé)", texte)
        self.assertIn("Sélection manuelle", texte)
        self.assertIn("nouvelle activité tarifée apparaîtra d'elle-même", texte)
        self.assertIn("wx.CheckListBox", texte)
        self.assertIn("Actualiser l'aperçu", texte)
        self.assertIn("construire_publication", texte)

    def test_contenu_dynamique_sait_rouvrir_un_bloc_tarifs(self):
        texte = CTRL_CONTENU.read_text(encoding="utf-8")
        self.assertIn("Tarifs Noethys", texte)
        self.assertIn("CTRL_Portail_tarifs.CTRL", texte)
        self.assertIn("est_configuration_bloc_tarifs", texte)
        self.assertIn("self.page_tarifs.SetParametres", texte)

    def test_tarifs_restent_exportes_comme_bloc_texte_historique(self):
        texte = CTRL_CONTENU.read_text(encoding="utf-8")
        # Le dialogue historique continue à voir le tout comme le même bloc
        # contenu externe, lui-même mappé vers bloc_texte par le socle #63.
        self.assertIn("def EstContenuExterne", texte)
        self.assertNotIn("bloc_tarifs", texte)

    def test_serveur_regenere_les_tarifs_avant_synchro_totale(self):
        texte = SERVEUR.read_text(encoding="utf-8")
        self.assertIn("from Utils import UTILS_Portail_tarifs_synchro", texte)
        preparation = texte.index("UTILS_Portail_tarifs_synchro.preparer_avant_synchro")
        synchro = texte.index("synchro.Synchro_totale()")
        self.assertLess(preparation, synchro)
        self.assertIn("Dernière version", (ROOT / "noethys" / "Utils" / "UTILS_Portail_tarifs_synchro.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
