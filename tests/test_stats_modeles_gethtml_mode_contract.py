# -*- coding: utf-8 -*-
"""Test comportemental — Utils/UTILS_Stats_modeles.py::HTML.GetHTML

Contrat vérifié : seuls les modes "affichage" et "impression" initialisent
la variable locale ``html``. Après vérification exhaustive des appelants
réels (Dlg/DLG_Stats.py, unique consommateur du contrat), aucun autre mode
n'est jamais transmis : ``mode="affichage"`` (valeur par défaut) ou
``mode="impression"``. Le contrat est donc confirmé, et tout autre mode
doit désormais échouer explicitement (ValueError) plutôt que de lever un
``UnboundLocalError`` incompréhensible en fin de fonction.
"""

import importlib.util
import sys
import types
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "noethys" / "Utils" / "UTILS_Stats_modeles.py"


def _install_stub_modules():
    wx = types.ModuleType("wx")

    class _MemoryFSHandler(object):
        def __init__(self, *args, **kwargs):
            pass

    class _FileSystem(object):
        @staticmethod
        def AddHandler(*args, **kwargs):
            return None

    wx.MemoryFSHandler = _MemoryFSHandler
    wx.FileSystem = _FileSystem
    wx.Frame = object
    sys.modules["wx"] = wx

    wx_html = types.ModuleType("wx.html")
    sys.modules["wx.html"] = wx_html
    wx.html = wx_html

    chemins = types.ModuleType("Chemins")
    sys.modules["Chemins"] = chemins

    ctrl_pkg = types.ModuleType("Ctrl")
    ctrl_pkg.__path__ = []
    sys.modules["Ctrl"] = ctrl_pkg
    ctrl_bouton_image = types.ModuleType("Ctrl.CTRL_Bouton_image")
    sys.modules["Ctrl.CTRL_Bouton_image"] = ctrl_bouton_image
    ctrl_pkg.CTRL_Bouton_image = ctrl_bouton_image

    pil_pkg = types.ModuleType("PIL")
    pil_pkg.__path__ = []
    sys.modules["PIL"] = pil_pkg
    pil_image = types.ModuleType("PIL.Image")
    sys.modules["PIL.Image"] = pil_image
    pil_pkg.Image = pil_image

    gestion = types.ModuleType("GestionDB")

    class _FakeDB(object):
        def __init__(self, *args, **kwargs):
            pass

        def Close(self):
            pass

    gestion.DB = _FakeDB
    sys.modules["GestionDB"] = gestion

    utils_pkg = types.ModuleType("Utils")
    utils_pkg.__path__ = []
    sys.modules["Utils"] = utils_pkg

    traduction = types.ModuleType("Utils.UTILS_Traduction")
    traduction._ = lambda value: value
    sys.modules["Utils.UTILS_Traduction"] = traduction
    utils_pkg.UTILS_Traduction = traduction

    utils_dates = types.ModuleType("Utils.UTILS_Dates")
    sys.modules["Utils.UTILS_Dates"] = utils_dates
    utils_pkg.UTILS_Dates = utils_dates

    six = types.ModuleType("six")
    six.PY2 = False
    six.PY3 = True
    sys.modules["six"] = six

    numpy = types.ModuleType("numpy")
    for name in ("arange", "sqrt", "array", "asarray", "ones", "exp", "convolve", "linspace"):
        setattr(numpy, name, lambda *args, **kwargs: None)
    sys.modules["numpy"] = numpy

    matplotlib = types.ModuleType("matplotlib")
    matplotlib.use = lambda *args, **kwargs: None
    sys.modules["matplotlib"] = matplotlib
    matplotlib_pyplot = types.ModuleType("matplotlib.pyplot")
    sys.modules["matplotlib.pyplot"] = matplotlib_pyplot
    matplotlib.pyplot = matplotlib_pyplot


def _load_module():
    _install_stub_modules()
    spec = importlib.util.spec_from_file_location("stats_modeles_gethtml_contract", str(MODULE_PATH))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GetHTMLModeContractTests(unittest.TestCase):
    def _make_html(self, module, listeActivites=(1,)):
        html = module.HTML(liste_objets=[])
        html.SetParametres({
            "listeActivites": list(listeActivites),
            "mode": "inscrits",
            "dictActivites": {1: "Activité test"},
        })
        return html

    def test_mode_affichage_preserves_historical_behaviour(self):
        module = _load_module()
        html = self._make_html(module)
        resultat = html.GetHTML(mode="affichage")
        self.assertIn("<HTML><BODY><FONT SIZE=-1>", resultat)
        self.assertIn("</FONT></BODY></HTML>", resultat)

    def test_mode_impression_preserves_historical_behaviour(self):
        module = _load_module()
        html = self._make_html(module)
        resultat = html.GetHTML(mode="impression", selectionsCodes=[])
        self.assertIn("<HTML><BODY>", resultat)
        self.assertIn("</FONT></BODY></HTML>", resultat)

    def test_unknown_mode_raises_explicit_error_instead_of_unbound_local(self):
        module = _load_module()
        html = self._make_html(module)
        with self.assertRaises(ValueError):
            html.GetHTML(mode="autre")

    def test_empty_activites_short_circuits_before_mode_dispatch(self):
        # Comportement historique préservé : liste vide => "" sans jamais évaluer le mode.
        module = _load_module()
        html = self._make_html(module, listeActivites=())
        self.assertEqual(html.GetHTML(mode="autre"), "")


if __name__ == "__main__":
    unittest.main()
