# -*- coding: utf-8 -*-
"""Contrats structurels de DLG_Inscription sans dépendre de wxPython."""

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys" / "Dlg" / "DLG_Inscription.py"


class InscriptionControllerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text(encoding="utf-8")
        ast.parse(cls.text)
        start = cls.text.index("class Page_Activite(wx.Panel):")
        end = cls.text.index("\n# -----------------------------------------------------------------------------------------------------------------", start)
        cls.page_activite = cls.text[start:end]

    def test_dialog_injects_business_controller_into_notebook(self):
        self.assertIn(
            "CTRL_Parametres(self, controller=self, mode=mode",
            self.text,
        )
        self.assertIn(
            "Page_Activite(self, controller=self.controller",
            self.text,
        )

    def test_page_activite_does_not_reach_business_state_through_wx_ancestry(self):
        for forbidden in (
            "self.parent.parent",
            "self.GetGrandParent()",
            "self.parent.mode",
            "self.parent.IDindividu",
            "self.parent.cp",
            "self.parent.ville",
        ):
            self.assertNotIn(forbidden, self.page_activite)
        self.assertIn("self.controller.ctrl_famille", self.page_activite)
        self.assertIn("self.controller.ctrl_statut", self.page_activite)

    def test_nested_controls_receive_page_controller_explicitly(self):
        self.assertIn("CTRL_Activite(self, controller=self)", self.page_activite)
        self.assertIn('ListBox(self, controller=self, type="groupes")', self.page_activite)
        self.assertIn('ListBox(self, controller=self, type="categories")', self.page_activite)
        self.assertIn("def __init__(self, parent, controller, type=\"groupes\")", self.text)
        self.assertIn("def __init__(self, parent, controller):", self.text)

    def test_resolved_address_is_used_for_tariff_category_selection(self):
        self.assertIn("self.cp = cp", self.page_activite)
        self.assertIn("self.ville = ville", self.page_activite)
        self.assertIn("UTILS_Titulaires.GetCoordsIndividu(self.IDindividu)", self.page_activite)
        self.assertIn(
            "self.ctrl_categories.SelectCategorieSelonVille(self.cp, self.ville)",
            self.page_activite,
        )


if __name__ == "__main__":
    unittest.main()
