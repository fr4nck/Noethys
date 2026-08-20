# -*- coding: utf-8 -*-
"""Contrat statique du panneau Individus/Familles de l'accueil."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Ctrl" / "CTRL_Recherche_individus.py"


class RechercheIndividusShellContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")
        ast.parse(cls.text)

    def test_header_is_compact_and_search_is_inline(self):
        self.assertNotIn("ctrl_sous_titre", self.text)
        self.assertIn('action_target("compact")', self.text)
        self.assertIn("entete.Add(self.ctrl_recherche", self.text)
        self.assertIn("entete.Add(self.ctrl_nouvelle_famille", self.text)

    def test_header_exposes_contextual_communication_actions(self):
        self.assertIn("self.ctrl_email", self.text)
        self.assertIn("self.ctrl_sms", self.text)
        self.assertIn("entete.Add(self.ctrl_email", self.text)
        self.assertIn("entete.Add(self.ctrl_sms", self.text)
        self.assertIn("def OnEmail", self.text)
        self.assertIn("DLG_Mailer.Dialog", self.text)
        self.assertIn("listeAdresses=adresses", self.text)
        self.assertIn("def OnSMS", self.text)
        self.assertIn("DLG_Envoi_sms.Dialog", self.text)
        self.assertIn('GetPageByCode("saisie_manuelle")', self.text)

    def test_pane_exposes_standard_window_commands(self):
        self.assertIn("def _ConfigurerPaneAui", self.text)
        self.assertIn("pane.CloseButton(True)", self.text)
        self.assertIn("pane.MaximizeButton(True)", self.text)
        self.assertIn("pane.MinimizeButton(True)", self.text)
        self.assertIn("pane.Resizable(True)", self.text)

    def test_list_keeps_responsive_columns_without_avatar_column(self):
        self.assertIn("UTILS_ColonnesResponsive.Installer", self.text)
        self.assertNotIn("GetImageCivilite", self.text)
        self.assertNotIn("imageGetter=", self.text)


if __name__ == "__main__":
    unittest.main()
