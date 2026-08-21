#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CTRL_TARIFS = ROOT / "noethys" / "Ctrl" / "CTRL_Portail_tarifs.py"
CTRL_CONTENU = ROOT / "noethys" / "Ctrl" / "CTRL_Portail_contenu_externe.py"
REGISTRE = ROOT / "noethys" / "Utils" / "UTILS_Portail_blocs.py"
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

    def test_tarifs_et_contenu_externe_ne_sont_plus_un_fourre_tout(self):
        contenu = CTRL_CONTENU.read_text(encoding="utf-8")
        registre = REGISTRE.read_text(encoding="utf-8")
        self.assertNotIn("CTRL_Portail_tarifs", contenu)
        self.assertNotIn("Tarifs Noethys", contenu)
        self.assertIn('CODE_CONTENU_EXTERNE = "bloc_contenu_externe"', registre)
        self.assertIn('CODE_TARIFS = "bloc_tarifs_noethys"', registre)
        self.assertIn("def detecter_code", registre)

    def test_types_ui_distincts_restent_exportes_comme_bloc_texte_historique(self):
        registre = REGISTRE.read_text(encoding="utf-8")
        self.assertIn("CODES_VIRTUELS", registre)
        self.assertIn("return CODE_TEXTE", registre)
        self.assertIn("est_configuration_bloc_tarifs", registre)
        self.assertIn("est_configuration_contenu_externe", registre)

    def test_serveur_regenere_les_tarifs_avant_synchro_totale(self):
        texte = SERVEUR.read_text(encoding="utf-8")
        self.assertIn("from Utils import UTILS_Portail_tarifs_synchro", texte)
        preparation = texte.index("UTILS_Portail_tarifs_synchro.preparer_avant_synchro")
        synchro = texte.index("synchro.Synchro_totale()")
        self.assertLess(preparation, synchro)
        self.assertIn("Dernière version", (ROOT / "noethys" / "Utils" / "UTILS_Portail_tarifs_synchro.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
