# -*- coding: utf-8 -*-
"""Contrats d'intégration entre UTILS_Interface et le design system."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERFACE = ROOT / "noethys" / "Utils" / "UTILS_Interface.py"


class DesignSystemIntegrationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = INTERFACE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text)

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

    def test_light_mode_is_not_globally_repainted_yet(self):
        start = self.text.index("def _appliquer_couleurs")
        end = self.text.index("\ndef _appliquer_barre_titre_sombre", start)
        block = self.text[start:end]
        self.assertIn("if not sombre:", block)
        self.assertIn("return", block)

    def test_disabled_controls_use_semantic_roles(self):
        self.assertIn('GetCouleurRole("disabled", sombre=True)', self.text)
        self.assertIn('GetCouleurRole("disabled_text", sombre=True)', self.text)

    def test_existing_public_theme_and_scale_api_is_preserved(self):
        functions = {
            node.name
            for node in self.tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        required = {
            "GetEchelle", "SetEchelle", "GetApparence", "SetApparence",
            "GetTheme", "SetTheme", "GetValeur", "GetCouleurRole",
            "AppliquerAffichage", "AppliquerAffichageGlobal",
            "InstallerGestionAffichage",
        }
        self.assertTrue(required.issubset(functions), sorted(required - functions))


if __name__ == "__main__":
    unittest.main()
