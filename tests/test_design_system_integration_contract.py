# -*- coding: utf-8 -*-
"""Contrats d'intégration entre UTILS_Interface et le design system."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERFACE = ROOT / "noethys" / "Utils" / "UTILS_Interface.py"
DIALOG = ROOT / "noethys" / "Dlg" / "DLG_Echelle_interface.py"
BANDEAU = ROOT / "noethys" / "Ctrl" / "CTRL_Bandeau.py"
BOUTON = ROOT / "noethys" / "Ctrl" / "CTRL_Bouton_image.py"
FOOTER = ROOT / "noethys" / "Ctrl" / "CTRL_Footer.py"
ULTRACHOICE = ROOT / "noethys" / "Ctrl" / "CTRL_Ultrachoice.py"


class DesignSystemIntegrationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = INTERFACE.read_text(encoding="utf-8")
        cls.dialog_text = DIALOG.read_text(encoding="utf-8")
        cls.bandeau_text = BANDEAU.read_text(encoding="utf-8")
        cls.bouton_text = BOUTON.read_text(encoding="utf-8")
        cls.footer_text = FOOTER.read_text(encoding="utf-8")
        cls.ultrachoice_text = ULTRACHOICE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text)
        ast.parse(cls.dialog_text)
        ast.parse(cls.bandeau_text)
        ast.parse(cls.bouton_text)
        ast.parse(cls.footer_text)
        ast.parse(cls.ultrachoice_text)

    def test_interface_imports_single_design_system_contract(self):
        self.assertIn("from Utils import UTILS_DesignSystem", self.text)
        self.assertIn("UTILS_DesignSystem.GetCouleur", self.text)
        self.assertIn("UTILS_DesignSystem.GetRoleComposant", self.text)
        self.assertIn("UTILS_DesignSystem.GetEtatCouleurs", self.text)

    def test_legacy_dark_palette_is_an_alias_layer_not_a_second_source(self):
        self.assertIn("PALETTE_SOMBRE = dict(UTILS_DesignSystem.PALETTE_SOMBRE)", self.text)
        self.assertIn('"selection_texte": PALETTE_SOMBRE["selection_text"]', self.text)
        self.assertIn('"metier_vert": PALETTE_SOMBRE["success"]', self.text)
        self.assertIn('"metier_jaune": PALETTE_SOMBRE["warning"]', self.text)
        self.assertIn('"metier_rouge": PALETTE_SOMBRE["danger"]', self.text)

    def test_component_surface_selection_is_centralized(self):
        start = self.text.index("def _appliquer_couleurs")
        end = self.text.index("\ndef _appliquer_barre_titre_sombre", start)
        block = self.text[start:end]
        self.assertIn("GetRoleComposant(window)", block)
        self.assertNotIn('role_fond = "surface_container_low"', block)
        self.assertNotIn('role_fond = "surface_container_high"', block)

    def test_light_mode_opts_in_only_shared_lists_before_general_return(self):
        start = self.text.index("def _appliquer_couleurs")
        end = self.text.index("\ndef _appliquer_barre_titre_sombre", start)
        block = self.text[start:end]
        list_marker = block.index('"objectlistview", "listctrl", "listview"')
        list_theme = block.index("_appliquer_palette_liste(window, sombre=sombre)")
        light_return = block.index("if not sombre:")
        self.assertLess(list_marker, list_theme)
        self.assertLess(list_theme, light_return)

    def test_list_rows_use_semantic_surface_pair(self):
        start = self.text.index("def _appliquer_palette_liste")
        end = self.text.index("\ndef _appliquer_couleurs", start)
        block = self.text[start:end]
        self.assertIn('GetCouleurRole("surface_container_lowest", sombre=sombre)', block)
        self.assertIn('GetCouleurRole("surface_container_low", sombre=sombre)', block)
        self.assertIn("index % 2 == 0", block)

    def test_business_colours_are_protected_before_list_recolouring(self):
        self.assertIn("def _peut_remplacer_surface_liste", self.text)
        start = self.text.index("def _appliquer_palette_liste")
        end = self.text.index("\ndef _appliquer_couleurs", start)
        block = self.text[start:end]
        self.assertIn("_peut_remplacer_surface_liste(couleur)", block)

    def test_historical_group_blue_is_replaced_only_as_default(self):
        start = self.text.index("def _appliquer_palette_liste")
        end = self.text.index("\ndef _appliquer_couleurs", start)
        block = self.text[start:end]
        self.assertIn('hasattr(window, "groupBackgroundColour")', block)
        self.assertIn("wx.Colour(159, 185, 250)", block)
        self.assertIn('GetCouleurRole("surface_container_high", sombre=sombre)', block)

    def test_disabled_controls_use_semantic_roles(self):
        self.assertIn('GetCouleurRole("disabled", sombre=True)', self.text)
        self.assertIn('GetCouleurRole("disabled_text", sombre=True)', self.text)
        self.assertIn('GetCouleurRole("disabled", sombre=sombre)', self.text)
        self.assertIn('GetCouleurRole("disabled_text", sombre=sombre)', self.text)

    def test_text_size_is_an_independent_accessibility_preference(self):
        self.assertIn("TAILLES_TEXTE =", self.text)
        self.assertIn('"interface_texte_pct"', self.text)
        self.assertIn("def GetTailleTexte", self.text)
        self.assertIn("def SetTailleTexte", self.text)

        start = self.text.index("def AppliquerAffichage")
        end = self.text.index("\ndef AppliquerAffichageGlobal", start)
        block = self.text[start:end]
        self.assertIn("facteur_interface = GetEchelle() / 100.0", block)
        self.assertIn("facteur_texte = facteur_interface * (GetTailleTexte() / 100.0)", block)
        self.assertIn("_appliquer_police(window, facteur_texte)", block)
        self.assertIn("_appliquer_dimensions_speciales(window, facteur_interface)", block)

    def test_preferences_dialog_exposes_accessibility_and_reset(self):
        self.assertIn('title=_(u"Apparence et accessibilité")', self.dialog_text)
        self.assertIn('_(u"Taille du texte :")', self.dialog_text)
        self.assertIn("UTILS_Interface.TAILLES_TEXTE", self.dialog_text)
        self.assertIn('_(u"Valeurs par défaut")', self.dialog_text)
        self.assertIn("def OnValeursDefaut", self.dialog_text)
        self.assertIn('UTILS_Interface.SetTailleTexte(valeurs["taille_texte"])', self.dialog_text)

    def test_common_dialog_header_uses_repens_facade(self):
        self.assertIn("UTILS_StyleRepens as Style", self.bandeau_text)
        self.assertIn('Style.appliquer_fenetre(self, "surface_container")', self.bandeau_text)
        self.assertIn('Style.couleur("outline_variant")', self.bandeau_text)
        self.assertIn("CTRL_TexteRepens.H1", self.bandeau_text)
        self.assertIn("def AppliquerTheme", self.bandeau_text)
        self.assertNotIn("from Utils import UTILS_Interface", self.bandeau_text)
        self.assertNotIn("self.SetBackgroundColour(wx.Colour(255, 255, 255))", self.bandeau_text)
        self.assertNotIn("wx.Font(10, wx.DEFAULT", self.bandeau_text)

    def test_common_image_button_uses_repens_semantic_states(self):
        self.assertIn("UTILS_StyleRepens as Style", self.bouton_text)
        self.assertIn("wx.EVT_ENTER_WINDOW", self.bouton_text)
        self.assertIn("wx.EVT_LEAVE_WINDOW", self.bouton_text)
        self.assertIn("wx.EVT_LEFT_DOWN", self.bouton_text)
        self.assertIn("wx.EVT_LEFT_UP", self.bouton_text)
        self.assertNotIn("wx.EVT_ENABLE", self.bouton_text)
        self.assertIn("def Enable(self, enable=True):", self.bouton_text)
        self.assertIn("wx.Button.Enable(self, enable)", self.bouton_text)
        self.assertIn('Style.etat("pressed")', self.bouton_text)
        self.assertIn('Style.etat("disabled")', self.bouton_text)
        self.assertIn('Style.couleur("surface_container_high")', self.bouton_text)
        self.assertIn('Style.couleur("on_surface")', self.bouton_text)
        self.assertNotIn("from Utils import UTILS_Interface", self.bouton_text)

    def test_common_list_footer_uses_repens_font_and_semantic_secondary_text(self):
        self.assertIn("UTILS_StyleRepens as Style", self.footer_text)
        self.assertIn("def AppliquerTheme", self.footer_text)
        self.assertIn('Style.couleur("surface_container")', self.footer_text)
        self.assertIn('Style.couleur("on_surface_variant")', self.footer_text)
        self.assertIn('Style.police("body")', self.footer_text)
        self.assertIn("wx.RendererNative.Get()", self.footer_text)
        self.assertNotIn("from Utils import UTILS_Interface", self.footer_text)
        self.assertNotIn("wx.Font(8, wx.SWISS", self.footer_text)
        self.assertNotIn("wx.Colour(140, 140, 140)", self.footer_text)
        self.assertIn('if "couleur" in infoColonne', self.footer_text)

    def test_ultrachoice_uses_semantic_rows_and_repens_fonts(self):
        self.assertIn("UTILS_StyleRepens as Style", self.ultrachoice_text)
        self.assertIn('Style.police("body_emphasis")', self.ultrachoice_text)
        self.assertIn('Style.police("body_small")', self.ultrachoice_text)
        self.assertIn('Style.couleur("on_surface")', self.ultrachoice_text)
        self.assertIn('Style.couleur("on_surface_variant")', self.ultrachoice_text)
        self.assertIn('role = "surface_container_lowest" if item % 2 == 0 else "surface_container_low"', self.ultrachoice_text)
        self.assertIn("fond = Style.couleur(role)", self.ultrachoice_text)
        self.assertIn("ODCB_PAINTING_SELECTED", self.ultrachoice_text)
        self.assertNotIn("from Utils import UTILS_Interface", self.ultrachoice_text)
        self.assertNotIn("wx.Font(10, wx.DEFAULT", self.ultrachoice_text)
        self.assertNotIn("wx.Font(7, wx.DEFAULT", self.ultrachoice_text)
        self.assertNotIn("wx.Colour(240, 240, 250)", self.ultrachoice_text)

    def test_existing_public_theme_and_scale_api_is_preserved(self):
        functions = {
            node.name
            for node in self.tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        required = {
            "GetEchelle", "SetEchelle", "GetTailleTexte", "SetTailleTexte",
            "GetApparence", "SetApparence", "GetTheme", "SetTheme",
            "GetValeur", "GetCouleurRole", "AppliquerAffichage",
            "AppliquerAffichageGlobal", "InstallerGestionAffichage",
        }
        self.assertTrue(required.issubset(functions), sorted(required - functions))


if __name__ == "__main__":
    unittest.main()
