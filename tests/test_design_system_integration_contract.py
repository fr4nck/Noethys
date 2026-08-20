# -*- coding: utf-8 -*-
"""Contrats d'intégration entre UTILS_Interface et le design system."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERFACE = ROOT / "noethys" / "Utils" / "UTILS_Interface.py"
DIALOG = ROOT / "noethys" / "Dlg" / "DLG_Echelle_interface.py"


class DesignSystemIntegrationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = INTERFACE.read_text(encoding="utf-8")
        cls.dialog_text = DIALOG.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text)
        ast.parse(cls.dialog_text)

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
