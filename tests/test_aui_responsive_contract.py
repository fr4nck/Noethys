# -*- coding: utf-8 -*-
"""Contrat statique du shell AUI Repens.

Repens peut styliser le shell, mais wxAUI reste propriétaire de la géométrie
(docking, sash, flottement et perspectives utilisateur). Les tests protègent
cette séparation afin d'éviter les boucles de resize et les réécritures de
layout qui ont provoqué des interfaces instables.
"""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUI = ROOT / "noethys" / "Utils" / "UTILS_Aui.py"
RESPONSIVE = ROOT / "noethys" / "Utils" / "UTILS_Responsive.py"


class AuiResponsiveContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = AUI.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.text)
        cls.responsive_text = RESPONSIVE.read_text(encoding="utf-8")
        ast.parse(cls.responsive_text)

    def test_layout_generation_matches_native_geometry_contract(self):
        self.assertIn("PERSPECTIVE_LAYOUT_VERSION = 7", self.text)
        self.assertIn("PARAMETRE_PERSPECTIVE_VERSION", self.text)

    def test_system_toolbars_are_fixed_and_non_floating(self):
        self.assertIn('("barre_raccourcis", 0)', self.text)
        self.assertIn('("barre_utilisateur", 1)', self.text)
        self.assertIn('(\"Gripper\", (False,))', self.text)
        self.assertIn('(\"Floatable\", (False,))', self.text)
        self.assertIn('(\"DockFixed\", (True,))', self.text)

    def test_workspace_registry_is_documentary_not_geometry_engine(self):
        self.assertIn("WORKSPACE_PANES", self.text)
        for pane in ('"recherche"', '"messagerie"', '"semaine_equipe"', '"sms"'):
            self.assertIn(pane, self.text)
        self.assertNotIn("def _ConfigurerWorkspace", self.text)
        self.assertNotIn("def _ConfigurerPaneWorkspace", self.text)
        self.assertNotIn("dock_proportion", self.text)
        self.assertNotIn("poids_total", self.text)
        self.assertNotIn("GetClientSize()", self.text)

    def test_shell_does_not_install_resize_geometry_loop(self):
        self.assertNotIn("wx.EVT_SIZE", self.text)
        self.assertNotIn("_noethys_aui_responsive_pending", self.text)
        self.assertNotIn("SendSizeEvent", self.text)
        self.assertNotIn("wx.CallLater", self.text)

    def test_reequilibrage_is_only_a_native_refresh(self):
        start = self.text.index("def ReequilibrerWorkspace")
        end = self.text.index("\ndef ConfigurerManager", start)
        block = self.text[start:end]
        self.assertIn("manager.Update()", block)
        self.assertIn("fenetre.Layout()", block)
        self.assertNotIn("Show(", block)
        self.assertNotIn("Hide(", block)
        self.assertNotIn("Dock", block)
        self.assertNotIn("Position", block)
        self.assertNotIn("BestSize", block)
        self.assertNotIn("MinSize", block)

    def test_shell_uses_semantic_flat_caption_surfaces(self):
        self.assertIn("def _ConfigurerArtShell", self.text)
        self.assertIn('"AUI_DOCKART_ACTIVE_CAPTION_COLOUR", "surface_container_high"', self.text)
        self.assertIn('"AUI_DOCKART_ACTIVE_CAPTION_GRADIENT_COLOUR", "surface_container_high"', self.text)
        self.assertIn('"AUI_DOCKART_INACTIVE_CAPTION_COLOUR", "surface_container"', self.text)
        self.assertIn('"AUI_DOCKART_INACTIVE_CAPTION_GRADIENT_COLOUR", "surface_container"', self.text)
        self.assertIn('"AUI_DOCKART_BACKGROUND_COLOUR", "surface"', self.text)
        self.assertIn('"AUI_DOCKART_CAPTION_SIZE"', self.text)

    def test_toolbar_uses_distinct_semantic_surface(self):
        self.assertIn('GetCouleurRole("surface_container_low")', self.text)
        self.assertIn('GetCouleurRole("on_surface")', self.text)
        self.assertIn("AUI_TB_PLAIN_BACKGROUND", self.text)

    def test_legacy_16px_assets_have_a_20px_desktop_floor(self):
        self.assertIn("if base <= 16:", self.responsive_text)
        self.assertIn("return 20", self.responsive_text)
        self.assertIn("Les pictos historiques 16 px étaient trop petits", self.responsive_text)

    def test_perspective_loading_does_not_rewrite_geometry_after_load(self):
        start = self.text.index("def ChargerPerspective")
        block = self.text[start:]
        self.assertIn("manager.LoadPerspective(candidate)", block)
        self.assertIn("ConfigurerManager(manager)", block)
        self.assertNotIn("ReequilibrerWorkspace", block)
        self.assertNotIn("_ConfigurerWorkspace", block)


if __name__ == "__main__":
    unittest.main()
