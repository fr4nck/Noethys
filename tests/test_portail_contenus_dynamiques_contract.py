#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DLG = ROOT / "noethys" / "Dlg" / "DLG_Saisie_portail_bloc.py"
CTRL = ROOT / "noethys" / "Ctrl" / "CTRL_Portail_contenu_externe.py"


class PortailContenuExterneContractTests(unittest.TestCase):

    def test_editeur_de_bloc_expose_le_contenu_externe_sans_nouvelle_categorie_persistante(self):
        dlg = DLG.read_text(encoding="utf-8")
        ctrl = CTRL.read_text(encoding="utf-8")

        self.assertIn('_(u"Contenu externe")', dlg)
        self.assertIn("CTRL_Portail_contenu_externe.CTRL", dlg)
        self.assertIn('categorie = _("bloc_texte")', dlg)
        self.assertIn("EstContenuExterne", dlg)
        self.assertIn("construire_iframe", ctrl)
        self.assertIn("texte_html", ctrl)
        self.assertIn("parametres", ctrl)


if __name__ == "__main__":
    unittest.main()
