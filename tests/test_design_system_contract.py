# -*- coding: utf-8 -*-
"""Contrats statiques du design system Noethys.

Les tests restent statiques afin de ne pas imposer l'initialisation wx dans les
jobs Linux qui ne font que valider l'architecture du thème.
"""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "noethys" / "Utils" / "UTILS_DesignSystem.py"
INTERFACE = ROOT / "noethys" / "Utils" / "UTILS_Interface.py"


class DesignSystemContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design_text = DESIGN.read_text(encoding="utf-8")
        cls.interface_text = INTERFACE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.design_text)

    def _tuple_strings(self, name):
        for node in self.tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == name:
                        return tuple(ast.literal_eval(node.value))
        self.fail("Constante %s absente" % name)

    def _dict_keys(self, name):
        for node in self.tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == name:
                        self.assertIsInstance(node.value, ast.Dict)
                        return {
                            ast.literal_eval(key)
                            for key in node.value.keys
                            if key is not None
                        }
        self.fail("Dictionnaire %s absent" % name)

    def test_required_semantic_roles_are_declared(self):
        roles = set(self._tuple_strings("ROLES"))
        required = {
            "surface",
            "surface_container_lowest",
            "surface_container_low",
            "surface_container",
            "surface_container_high",
            "surface_container_highest",
            "on_surface",
            "on_surface_variant",
            "primary",
            "on_primary",
            "primary_container",
            "on_primary_container",
            "outline",
            "outline_variant",
            "selection",
            "selection_text",
            "disabled",
            "disabled_text",
            "focus",
            "success",
            "warning",
            "danger",
            "info",
        }
        self.assertTrue(required.issubset(roles), sorted(required - roles))

    def test_light_and_dark_palettes_share_core_non_accent_roles(self):
        light = self._dict_keys("PALETTE_CLAIRE")
        dark = self._dict_keys("PALETTE_SOMBRE")
        expected = {
            "surface",
            "surface_container_lowest",
            "surface_container_low",
            "surface_container",
            "surface_container_high",
            "surface_container_highest",
            "on_surface",
            "on_surface_variant",
            "outline",
            "outline_variant",
            "selection",
            "selection_text",
            "disabled",
            "disabled_text",
            "focus",
            "success",
            "success_text",
            "warning",
            "warning_text",
            "danger",
            "danger_text",
            "info",
            "info_text",
        }
        self.assertTrue(expected.issubset(light), sorted(expected - light))
        self.assertTrue(expected.issubset(dark), sorted(expected - dark))

    def test_all_interactive_states_are_explicit(self):
        states = set(self._tuple_strings("ETATS_INTERACTIFS"))
        self.assertEqual(
            states,
            {"normal", "hover", "focus", "pressed", "selected", "disabled", "error"},
        )

    def test_historical_accent_themes_are_preserved(self):
        light = self._dict_keys("ACCENTS_CLAIRS")
        dark = self._dict_keys("ACCENTS_SOMBRES")
        self.assertEqual(light, {"Vert", "Bleu", "Noir"})
        self.assertEqual(dark, {"Vert", "Bleu", "Noir"})

    def test_component_surface_roles_are_centralized(self):
        roles = self._dict_keys("ROLES_COMPOSANTS")
        self.assertEqual(roles, {"data", "input", "panel", "toolbar", "button", "floating"})
        self.assertIn("def GetRoleComposant", self.design_text)

    def test_historical_ctrl_modules_are_classifiable(self):
        # Les composants Noethys portent souvent la classe générique CTRL. Le
        # contrat doit donc reconnaître aussi leur nom de module qualifié.
        for marker in ("grille", "saisie", "bouton", "barre_outils"):
            self.assertIn('"%s"' % marker, self.design_text)
        self.assertIn("classe.__module__", self.interface_text)
        self.assertIn("classe.__name__", self.interface_text)

    def test_interface_consumes_surface_hierarchy_through_central_contract(self):
        # Les rôles complets vivent dans UTILS_DesignSystem. UTILS_Interface ne
        # doit pas recopier la table : il consomme le contrat et référence
        # directement seulement les surfaces dont son moteur a besoin.
        self.assertIn("from Utils import UTILS_DesignSystem", self.interface_text)
        self.assertIn("UTILS_DesignSystem.GetCouleur", self.interface_text)
        self.assertIn("UTILS_DesignSystem.GetRoleComposant", self.interface_text)
        for role in (
            "surface_container_lowest",
            "surface_container_low",
            "surface_container_high",
        ):
            self.assertIn('"%s"' % role, self.interface_text)
        self.assertIn('"surface_container_highest"', self.design_text)

    def test_no_mobile_or_glass_defaults_are_introduced(self):
        lowered = self.design_text.lower()
        self.assertNotIn("backdrop blur", lowered)
        self.assertNotIn("glassmorphism", lowered)
        self.assertNotIn("mobile card", lowered)


if __name__ == "__main__":
    unittest.main()
