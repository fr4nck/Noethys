# -*- coding: utf-8 -*-
"""Contrat statique du panneau Individus/Familles Repens."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Ctrl" / "CTRL_Recherche_individus.py"
ACTION = ROOT / "noethys" / "Ctrl" / "CTRL_ActionRepens.py"
ICONES = ROOT / "noethys" / "Utils" / "UTILS_IconesRepens.py"


class RechercheIndividusShellContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")
        cls.action = ACTION.read_text(encoding="utf-8")
        cls.icones = ICONES.read_text(encoding="utf-8")
        ast.parse(cls.text)
        ast.parse(cls.action)
        ast.parse(cls.icones)

    def test_header_is_contextual_without_duplicate_title(self):
        self.assertNotIn("ctrl_sous_titre", self.text)
        self.assertNotIn("self.ctrl_titre =", self.text)
        self.assertIn("entete.Add(self.ctrl_resume", self.text)
        self.assertIn("entete.Add(self.ctrl_recherche", self.text)
        self.assertIn("entete.Add(self.ctrl_nouvelle_famille", self.text)
        self.assertIn('variante="primaire"', self.text)

    def test_header_exposes_contextual_communication_actions(self):
        self.assertIn('icone="mail"', self.text)
        self.assertIn('icone="chat"', self.text)
        self.assertIn("entete.Add(self.ctrl_email", self.text)
        self.assertIn("entete.Add(self.ctrl_sms", self.text)
        self.assertIn("def OnEmail", self.text)
        self.assertIn("DLG_Mailer.Dialog", self.text)
        self.assertIn("dlg.ctrl_destinataires.SetDonneesManuelles(adresses)", self.text)
        self.assertIn("def OnSMS", self.text)
        self.assertIn("DLG_Envoi_sms.Dialog", self.text)
        self.assertIn('GetPageByCode("saisie_manuelle")', self.text)
        self.assertIn('"mail":', self.icones)
        self.assertIn('"chat":', self.icones)

    def test_daily_commands_use_repens_actions_and_overflow(self):
        self.assertIn("class BarreCommandes(wx.Panel)", self.text)
        self.assertIn("CTRL_ActionRepens.CTRL", self.text)
        self.assertIn('label=_(u"Modifier")', self.text)
        self.assertIn('label=_(u"Calendrier")', self.text)
        self.assertIn('label=_(u"Fiche individuelle")', self.text)
        self.assertIn('label=_(u"Plus")', self.text)
        self.assertIn('u"Supprimer ou détacher…"', self.text)
        self.assertNotIn("class ToolBar(wx.ToolBar)", self.text)

    def test_common_action_is_rounded_and_keyboard_operable(self):
        self.assertIn("DrawRoundedRectangle", self.action)
        self.assertIn("wx.WXK_SPACE", self.action)
        self.assertIn("wx.WXK_RETURN", self.action)
        self.assertIn("wx.EVT_SET_FOCUS", self.action)
        self.assertIn("wx.PostEvent", self.action)

    def test_pane_exposes_standard_window_commands(self):
        self.assertIn("def _ConfigurerPaneAui", self.text)
        self.assertIn("pane.CloseButton(True)", self.text)
        self.assertIn("pane.MaximizeButton(True)", self.text)
        self.assertIn("pane.MinimizeButton(True)", self.text)
        self.assertIn("pane.Resizable(True)", self.text)
        self.assertIn("pane.Movable(True)", self.text)

    def test_list_keeps_responsive_columns_without_avatar_column(self):
        self.assertIn("UTILS_ColonnesResponsive.Installer", self.text)
        self.assertNotIn("GetImageCivilite", self.text)
        self.assertNotIn("imageGetter=", self.text)

    def test_empty_state_is_compact_instead_of_replacing_the_data_surface(self):
        self.assertIn("class IndicationRecherche(wx.Panel)", self.text)
        self.assertIn('SetMinSize((-1, UTILS_UIMetrics.px(54)))', self.text)
        self.assertIn("principal.Add(self.ctrl_listview, 1", self.text)


if __name__ == "__main__":
    unittest.main()
