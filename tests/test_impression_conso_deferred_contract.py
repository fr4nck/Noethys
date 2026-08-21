# -*- coding: utf-8 -*-
"""Contrats du sas de chargement de la liste des consommations."""

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ImpressionConsoDeferredContractTests(unittest.TestCase):
    def _read(self, path):
        text = (ROOT / path).read_text(encoding="utf-8")
        ast.parse(text)
        return text

    def test_dlg_package_routes_only_the_heavy_dialog_lazily(self):
        text = self._read("noethys/Dlg/__init__.py")
        self.assertIn("def __getattr__(name):", text)
        self.assertIn('name == "DLG_Impression_conso"', text)
        self.assertIn("DLG_Impression_conso_differe", text)
        self.assertNotIn("from .DLG_Impression_conso", text)

    def test_deferred_dialog_reuses_legacy_business_engine(self):
        text = self._read("noethys/Dlg/DLG_Impression_conso_differe.py")
        self.assertIn("class Dialog(Legacy.Dialog):", text)
        self.assertIn("Legacy = importlib.import_module", text)
        self.assertNotIn("def Impression(", text)
        self.assertNotIn("def GetParametres(", text)
        self.assertNotIn("def TriClasses(", text)

    def test_pages_and_network_initialisation_yield_to_wx_loop(self):
        text = self._read("noethys/Dlg/DLG_Impression_conso_differe.py")
        self.assertIn("class CTRL_Parametres_Differe", text)
        self.assertIn("wx.CallAfter(self._ConstruirePageSuivante)", text)
        self.assertIn("wx.CallAfter(self._InitActivites)", text)
        self.assertIn("wx.CallAfter(self._InitContexte)", text)
        self.assertIn("wx.CallAfter(self._InitProfil)", text)
        self.assertIn("wx.CallAfter(self._FinChargement)", text)
        self.assertIn("self._ActiverActions(False)", text)
        self.assertIn("self._ActiverActions(True)", text)

    def test_events_are_loaded_once_with_final_date_context(self):
        text = self._read("noethys/Dlg/DLG_Impression_conso_differe.py")
        self.assertIn("ctrl_evenements.listeActivites = sorted(liste_activites)", text)
        self.assertIn("ctrl_evenements.SetDates(listeDates=self._dates_initiales)", text)
        self.assertNotIn("ctrl_evenements.SetActivites(liste_activites)", text)


if __name__ == "__main__":
    unittest.main()
