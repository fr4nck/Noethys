# -*- coding: utf-8 -*-
"""Garde-fous d'architecture des contrôles transversaux migrés vers Repens."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepensSharedControlsContractTests(unittest.TestCase):
    def _read(self, relative_path):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        ast.parse(text)
        return text

    def test_shared_controls_consume_repens_facade_only(self):
        for relative_path in (
            "noethys/Ctrl/CTRL_TableauResponsive.py",
            "noethys/Ctrl/CTRL_Ticker_presents.py",
            "noethys/Ctrl/CTRL_Portail_messages.py",
            "noethys/Ctrl/CTRL_Saisie_adresse.py",
            "noethys/Ctrl/CTRL_Planning_semaine.py",
            "noethys/Ctrl/CTRL_Grille_periode.py",
            "noethys/Ctrl/CTRL_Logo.py",
            "noethys/Ctrl/CTRL_Newsticker.py",
            "noethys/Ctrl/CTRL_Assistant_base.py",
        ):
            text = self._read(relative_path)
            self.assertIn("UTILS_StyleRepens as Style", text)
            self.assertNotIn("UTILS_Interface", text)
            self.assertNotIn("UTILS_UIMetrics", text)

    def test_responsive_table_uses_repens_actions_and_drops_vertical_grid_lines(self):
        text = self._read("noethys/Ctrl/CTRL_TableauResponsive.py")
        self.assertIn("CTRL_ActionRepens", text)
        self.assertIn("Style.appliquer_liste(self)", text)
        self.assertIn("Style.appliquer_saisie(self.recherche)", text)
        self.assertNotIn("UTILS_FluentIcons", text)
        self.assertNotIn("wx.LC_VRULES", text)

    def test_teamworks_week_uses_repens_navigation_without_changing_data_source(self):
        text = self._read("noethys/Ctrl/CTRL_Planning_semaine.py")
        self.assertIn("CTRL_ActionRepens", text)
        self.assertIn('icone="arrow_left"', text)
        self.assertIn('icone="arrow_right"', text)
        self.assertIn('icone="calendar"', text)
        self.assertIn("UTILS_Teamworks_Planning.GetSemaine", text)
        self.assertIn("threading.Thread", text)
        self.assertNotIn("wx.Button", text)

    def test_address_editor_uses_repens_search_action(self):
        text = self._read("noethys/Ctrl/CTRL_Saisie_adresse.py")
        self.assertIn("CTRL_ActionRepens", text)
        self.assertIn('icone="search"', text)
        self.assertIn("Style.appliquer_saisie(ctrl)", text)
        self.assertNotIn("CTRL_Bouton_image", text)
        self.assertNotIn("_PoliceInterface", text)

    def test_period_grid_uses_native_repens_inputs_without_legacy_styles(self):
        text = self._read("noethys/Ctrl/CTRL_Grille_periode.py")
        self.assertIn("Style.appliquer_saisie(self)", text)
        self.assertIn("Style.appliquer_liste(self)", text)
        self.assertIn('Style.appliquer_fenetre(self.notebook, "surface")', text)
        self.assertNotIn("FlexGridSizer", text)
        self.assertNotIn("wx.SystemSettings.GetFont", text)

    def test_logo_uses_semantic_menu_icons_and_scaled_geometry(self):
        text = self._read("noethys/Ctrl/CTRL_Logo.py")
        self.assertIn("UTILS_IconesRepens", text)
        self.assertIn('Style.taille_icone("compact")', text)
        self.assertIn('Style.couleur("surface_container_lowest")', text)
        self.assertNotIn("Images/16x16/Ajouter.png", text)
        self.assertNotIn("Images/16x16/Supprimer.png", text)

    def test_newsticker_uses_semantic_heading_roles_and_intrinsic_height(self):
        text = self._read("noethys/Ctrl/CTRL_Newsticker.py")
        self.assertIn('Style.couleur("surface_container_low")', text)
        self.assertIn('Style.couleur("on_surface_variant")', text)
        self.assertIn('Style.police("caption")', text)
        self.assertIn('Style.hauteur_panneau("compact")', text)
        self.assertNotIn("wx.Font(6", text)
        self.assertNotIn("(200, 200, 200)", text)

    def test_assistant_foundation_owns_shared_repens_styling(self):
        text = self._read("noethys/Ctrl/CTRL_Assistant_base.py")
        self.assertIn("Style.appliquer_saisie(self)", text)
        self.assertIn('Style.appliquer_fenetre(self, "surface")', text)
        self.assertIn('role_texte="on_surface_variant"', text)
        self.assertIn("Style.cible_action(\"compact\")", text)
        self.assertIn("_TailleDpi", text)
        self.assertNotIn("wx.Font(", text)
        self.assertNotIn("(120, 120, 120)", text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)

    def test_semantic_trees_keep_business_icons_but_scale_them(self):
        for relative_path in (
            "noethys/Ctrl/CTRL_Stats_objets.py",
            "noethys/Ctrl/CTRL_Filtres_transports.py",
        ):
            text = self._read(relative_path)
            self.assertIn("UTILS_StyleRepens as Style", text)
            self.assertIn("Style.appliquer_liste(self)", text)
            self.assertIn('Style.taille_icone("inline")', text)
            self.assertNotIn("wx.WHITE", text)


if __name__ == "__main__":
    unittest.main()
