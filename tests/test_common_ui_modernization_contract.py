# -*- coding: utf-8 -*-
"""Contrats statiques de la modernisation UI progressive des contrôles communs."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CommonUIModernizationContractTests(unittest.TestCase):
    def _read(self, relative_path):
        path = ROOT / relative_path
        text = path.read_text(encoding="utf-8")
        ast.parse(text)
        return text

    def test_common_toolbar_is_native_responsive_and_opt_in_fluent(self):
        text = self._read("noethys/Utils/UTILS_Adaptations.py")
        self.assertIn("class ToolBar(wx.ToolBar)", text)
        self.assertIn("def AddFluentTool", text)
        self.assertIn("wx.TB_FLAT | wx.TB_NODIVIDER", text)
        self.assertIn("UTILS_UIMetrics.toolbar_height", text)
        self.assertNotIn("setattr(wx.ToolBar", text)

    def test_common_banner_reflows_with_box_sizer_and_central_style(self):
        text = self._read("noethys/Ctrl/CTRL_Bandeau.py")
        self.assertIn("wx.BoxSizer(wx.HORIZONTAL)", text)
        self.assertIn("wx.BoxSizer(wx.VERTICAL)", text)
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)
        self.assertNotIn("Style.px(76)", text)
        self.assertNotIn("principal.Add(contenu, 1", text)
        self.assertNotIn("FlexGridSizer", text)
        self.assertNotIn("GridSizer", text)

    def test_home_is_flat_semantic_and_drops_decorative_card(self):
        text = self._read("noethys/Ctrl/CTRL_Accueil.py")
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn('Style.police("h2")', text)
        self.assertIn('Style.couleur("primary")', text)
        self.assertIn('Style.hauteur_ligne("compact")', text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)
        self.assertNotIn("DrawRoundedRectangle", text)
        self.assertNotIn("surface_container", text)

    def test_mail_client_is_dense_responsive_and_repens_driven(self):
        text = self._read("noethys/Ctrl/CTRL_Messagerie.py")
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn("Style.appliquer_liste", text)
        self.assertIn("def _AjusteColonnes", text)
        self.assertIn("SetSashGravity", text)
        self.assertIn("wx.SP_NOBORDER", text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)
        self.assertNotIn("wx.SP_3D", text)

    def test_calendar_wrapper_consumes_repens_metrics_only(self):
        text = self._read("noethys/Ctrl/CTRL_Grille_calendrier.py")
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn('Style.appliquer_fenetre(self, "surface")', text)
        self.assertIn("Style.espace(1)", text)
        self.assertIn("Style.px(240)", text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)

    def test_list_tools_consume_repens_facade_only(self):
        text = self._read("noethys/Ctrl/CTRL_OutilsListeRepens.py")
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn("Style.appliquer_saisie(self)", text)
        self.assertIn('Style.appliquer_fenetre(self, "surface")', text)
        self.assertIn('icone="filter"', text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)

    def test_toaster_consumes_repens_typography_and_metrics(self):
        text = self._read("noethys/Ctrl/CTRL_Toaster.py")
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn('Style.couleur("surface_container_highest")', text)
        self.assertIn('Style.police("h2")', text)
        self.assertIn("Style.espace(10)", text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)
        self.assertNotIn("_PoliceSysteme", text)

    def test_business_lists_share_repens_actions_and_metrics(self):
        for relative_path in (
            "noethys/Ctrl/CTRL_Liste_inscriptions.py",
            "noethys/Ctrl/CTRL_Liste_cotisations.py",
            "noethys/Ctrl/CTRL_Liste_rappels.py",
            "noethys/Ctrl/CTRL_Liste_locations.py",
        ):
            text = self._read(relative_path)
            self.assertIn("CTRL_ActionRepens", text)
            self.assertIn("CTRL_OutilsListeRepens", text)
            self.assertIn("UTILS_StyleRepens as Style", text)
            self.assertIn('Style.appliquer_fenetre(self, "surface")', text)
            self.assertIn('icone="mail"', text)
            self.assertNotIn("CTRL_Bouton_image", text)
            self.assertNotIn("UTILS_Interface", text)
            self.assertNotIn("UTILS_UIMetrics", text)
            self.assertNotIn("tailleImage=(20, 20)", text)

    def test_messages_no_longer_use_tiny_vertical_bitmap_buttons(self):
        text = self._read("noethys/Ctrl/CTRL_Messages.py")
        self.assertIn("AddFluentTool", text)
        self.assertIn('"add"', text)
        self.assertIn('"edit"', text)
        self.assertIn('"delete"', text)
        self.assertNotIn("wx.BitmapButton", text)
        self.assertNotIn("FlexGridSizer", text)

    def test_footer_tracks_real_responsive_column_widths(self):
        text = self._read("noethys/Ctrl/CTRL_Footer.py")
        self.assertIn("GetColumnWidth(index)", text)
        self.assertIn("GetScrollPos(wx.HORIZONTAL)", text)
        self.assertIn('Style.hauteur_ligne("table")', text)
        self.assertIn('Style.couleur("on_surface_variant")', text)
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)

    def test_assistant_list_uses_available_width_without_recursive_resize(self):
        text = self._read("noethys/Ctrl/CTRL_Assistants_liste.py")
        self.assertIn("wx.EVT_SIZE", text)
        self.assertIn("GetClientSize().GetWidth()", text)
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn("Style.appliquer_liste(self)", text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)
        self.assertNotIn("SendSizeEvent", text)
        self.assertNotIn("SetSize((400", text)

    def test_common_image_button_supports_explicit_fluent_and_css_repens(self):
        text = self._read("noethys/Ctrl/CTRL_Bouton_image.py")
        self.assertIn("iconeFluent", text)
        self.assertIn("SetIconeFluent", text)
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertIn('Style.cible_action("standard")', text)
        self.assertIn('Style.etat("pressed")', text)
        self.assertNotIn("UTILS_Interface", text)
        self.assertNotIn("UTILS_UIMetrics", text)
        self.assertNotIn("EVT_ENABLE", text)

    def test_small_dialogs_are_resizable_and_not_grid_locked(self):
        for relative_path in (
            "noethys/Ctrl/CTRL_Numfacture.py",
            "noethys/Ctrl/CTRL_Identification.py",
        ):
            text = self._read(relative_path)
            self.assertIn("wx.RESIZE_BORDER", text)
            self.assertNotIn("FlexGridSizer", text)
            self.assertNotIn("GridSizer", text)

    def test_common_entry_controls_consume_repens_stylesheet(self):
        for relative_path in (
            "noethys/Ctrl/CTRL_Saisie_date.py",
            "noethys/Ctrl/CTRL_Saisie_heure.py",
            "noethys/Ctrl/CTRL_Saisie_numSecu.py",
            "noethys/Ctrl/CTRL_Saisie_mail.py",
            "noethys/Ctrl/CTRL_Saisie_tel.py",
            "noethys/Ctrl/CTRL_Saisie_euros.py",
            "noethys/Ctrl/CTRL_Saisie_compte.py",
            "noethys/Ctrl/CTRL_Saisie_civilite.py",
            "noethys/Ctrl/CTRL_Saisie_duree.py",
            "noethys/Ctrl/CTRL_Saisie_releve_bancaire.py",
            "noethys/Ctrl/CTRL_Combobox_autocomplete.py",
            "noethys/Ctrl/CTRL_Choix_modele.py",
        ):
            text = self._read(relative_path)
            self.assertIn("UTILS_StyleRepens as Style", text)
            self.assertNotIn("UTILS_Interface", text)
            self.assertNotIn("UTILS_UIMetrics", text)

    def test_common_information_and_selection_panels_consume_repens_stylesheet(self):
        for relative_path in (
            "noethys/Ctrl/CTRL_Compte_internet.py",
            "noethys/Ctrl/CTRL_CheckListBox.py",
            "noethys/Ctrl/CTRL_Selection_depots.py",
            "noethys/Ctrl/CTRL_Selection_jours.py",
        ):
            text = self._read(relative_path)
            self.assertIn("UTILS_StyleRepens as Style", text)
            self.assertNotIn("UTILS_Interface", text)
            self.assertNotIn("UTILS_UIMetrics", text)

    def test_weekday_selector_uses_repens_actions_and_semantic_spacing(self):
        text = self._read("noethys/Ctrl/CTRL_Selection_jours.py")
        self.assertIn("CTRL_ActionRepens.CTRL", text)
        self.assertIn('label=_(u"Tout")', text)
        self.assertIn('label=_(u"Aucun")', text)
        self.assertIn('Style.appliquer_fenetre(self, "surface")', text)
        self.assertIn('Style.appliquer_texte(label, role="label"', text)
        self.assertNotIn("CTRL_Bouton_image", text)
        self.assertNotIn("_PoliceInterface", text)
        self.assertNotIn("self.Fit()", text)

    def test_date_control_consumes_semantic_repens_entry_style(self):
        text = self._read("noethys/Ctrl/CTRL_Saisie_date.py")
        self.assertIn("Style.appliquer_saisie(self)", text)
        self.assertIn('Style.cible_action("compact")', text)
        self.assertIn('Style.espace(4)', text)
        self.assertNotIn("GetCouleurRole", text)
        self.assertNotIn("GetTailleTexte", text)

    def test_modern_entry_controls_drop_unused_historical_image_dependencies(self):
        for relative_path in (
            "noethys/Ctrl/CTRL_Saisie_mail.py",
            "noethys/Ctrl/CTRL_Saisie_tel.py",
            "noethys/Ctrl/CTRL_Saisie_euros.py",
            "noethys/Ctrl/CTRL_Saisie_compte.py",
            "noethys/Ctrl/CTRL_Saisie_civilite.py",
            "noethys/Ctrl/CTRL_Saisie_duree.py",
            "noethys/Ctrl/CTRL_Combobox_autocomplete.py",
            "noethys/Ctrl/CTRL_Choix_modele.py",
        ):
            text = self._read(relative_path)
            self.assertNotIn("CTRL_Bouton_image", text)
            self.assertNotIn("import Chemins", text)

    def test_identity_status_control_is_semantic_and_scalable(self):
        text = self._read("noethys/Ctrl/CTRL_Saisie_numSecu.py")
        self.assertIn('Style.couleur("success")', text)
        self.assertIn('Style.couleur("danger")', text)
        self.assertIn('Style.police("h4")', text)
        self.assertIn("Style.appliquer_saisie(self.ctrl_numsecu)", text)
        self.assertIn("wx.StaticText", text)
        self.assertNotIn("wx.StaticBitmap", text)
        self.assertNotIn("FlexGridSizer", text)

    def test_country_and_bank_statement_selectors_use_modern_action_buttons(self):
        for relative_path in (
            "noethys/Ctrl/CTRL_Saisie_pays.py",
            "noethys/Ctrl/CTRL_Saisie_releve_bancaire.py",
        ):
            text = self._read(relative_path)
            self.assertIn("CTRL_Bouton_image.CTRL", text)
            self.assertIn('iconeFluent="edit"', text)
            self.assertIn("wx.BoxSizer(wx.HORIZONTAL)", text)
            self.assertNotIn("wx.BitmapButton", text)
            self.assertNotIn("FlexGridSizer", text)

    def test_checklist_uses_repens_actions_and_no_side_bitmap_column(self):
        text = self._read("noethys/Ctrl/CTRL_CheckListBox.py")
        self.assertIn("CTRL_ActionRepens.CTRL", text)
        self.assertIn('label=_(u"Tout cocher")', text)
        self.assertIn('label=_(u"Tout décocher")', text)
        self.assertIn("UTILS_StyleRepens as Style", text)
        self.assertNotIn("wx.BitmapButton", text)
        self.assertNotIn("FlexGridSizer", text)

    def test_date_selector_uses_fluent_calendar_and_repens_menu_icons(self):
        text = self._read("noethys/Ctrl/CTRL_Saisie_date.py")
        self.assertIn('iconeFluent="calendar"', text)
        self.assertIn("GetStaticIconPath", text)
        self.assertIn('Style.taille_icone("compact")', text)
        self.assertIn('Style.taille_icone("inline")', text)
        self.assertIn("wx.BoxSizer(wx.HORIZONTAL)", text)
        self.assertNotIn("wx.BitmapButton", text)
        self.assertNotIn("FlexGridSizer", text)
        self.assertNotIn("if False else False", text)
        self.assertNotIn("ID_MOIS_ACTUELLE", text)


if __name__ == "__main__":
    unittest.main()
