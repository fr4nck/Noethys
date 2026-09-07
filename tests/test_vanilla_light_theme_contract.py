# -*- coding: utf-8 -*-
"""Contrats de stabilisation du thème clair Vanilla."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "noethys" / "Utils" / "UTILS_Config.py"
INTERFACE = ROOT / "noethys" / "Utils" / "UTILS_Interface.py"
DIALOG = ROOT / "noethys" / "Dlg" / "DLG_Echelle_interface.py"
STYLE = ROOT / "noethys" / "Utils" / "UTILS_StyleRepens.py"
AUI = ROOT / "noethys" / "Utils" / "UTILS_Aui.py"
ACTION = ROOT / "noethys" / "Ctrl" / "CTRL_ActionRepens.py"
RECHERCHE = ROOT / "noethys" / "Ctrl" / "CTRL_Recherche_individus.py"


def lire(path):
    texte = path.read_text(encoding="utf-8")
    ast.parse(texte)
    return texte


class VanillaLightThemeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = lire(CONFIG)
        cls.interface = lire(INTERFACE)
        cls.dialog = lire(DIALOG)
        cls.style = lire(STYLE)
        cls.aui = lire(AUI)
        cls.action = lire(ACTION)
        cls.recherche = lire(RECHERCHE)

    def test_preference_active_est_forcee_en_clair(self):
        self.assertIn('VANILLA_APPARENCE = "clair"', self.config)
        self.assertIn('if nomParametre == "interface_apparence":\n        return VANILLA_APPARENCE', self.config)
        self.assertIn('if nomParametre == "interface_apparence":\n        parametre = VANILLA_APPARENCE', self.config)
        self.assertIn('UTILS_Config.GetParametre("interface_apparence", "systeme")', self.interface)

    def test_rendu_sombre_wxmsw_est_explicitement_desactive(self):
        self.assertIn('wx.SystemOptions.SetOption("msw.dark-mode", 0)', self.config)
        self.assertIn('if os.name == "nt":', self.config)

    def test_dialogue_apparence_ne_permet_plus_systeme_ou_sombre(self):
        self.assertIn('self.ctrl_apparence.Enable(False)', self.dialog)
        self.assertIn('"apparence": UTILS_Interface.GetApparence()', self.dialog)
        self.assertIn('self.liste_codes_apparence.index("clair")', self.dialog)
        self.assertIn('le thème système et le mode sombre ne sont pas activés', self.dialog)

    def test_listes_champs_boutons_et_aui_restent_sur_les_roles_semantiques(self):
        self.assertIn('def appliquer_saisie(ctrl):', self.style)
        self.assertIn('ctrl.SetForegroundColour(couleur("on_surface"))', self.style)
        self.assertIn('ctrl.SetBackgroundColour(couleur("surface_container_lowest"))', self.style)
        self.assertIn('def appliquer_liste(ctrl):', self.style)
        self.assertIn('book.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))', self.aui)
        self.assertIn('book.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))', self.aui)
        self.assertIn('Style.couleur("on_surface")', self.action)
        self.assertIn('Style.couleur("surface_container_high")', self.action)
        self.assertIn('self.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))', self.recherche)

    def test_menus_restent_natifs_et_heriteront_du_wxmsw_clair(self):
        self.assertIn('menu = UTILS_Adaptations.Menu()', self.recherche)
        self.assertIn('wx.SystemOptions.SetOption("msw.dark-mode", 0)', self.config)


if __name__ == "__main__":
    unittest.main()
