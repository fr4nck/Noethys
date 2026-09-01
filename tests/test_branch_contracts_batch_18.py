# -*- coding: utf-8 -*-
"""Batch 18 — Utils/UTILS_Stats_modeles.py::GetHTML — html (branch_assignment_gap).

Seuls les modes "affichage" et "impression" initialisaient `html` avant ce
correctif ; un mode inconnu (typo, évolution future d'un appelant) laissait
`html` non affecté puis provoquait un `UnboundLocalError` opaque au moment du
`return html`. Le contrat de `GetHTML` (confirmé par tous les appels existants
dans le dépôt : `mode="affichage"` par défaut ou `mode="impression"`) est
maintenant explicite : un mode hors contrat lève une `ValueError` lisible au
lieu de l'`UnboundLocalError` silencieux.
"""
import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
AUDIT = ROOT / "scripts" / "audit_branch_assignment_gaps.py"

spec = importlib.util.spec_from_file_location("audit_branch_assignment_gaps", AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

TARGET = ("Utils/UTILS_Stats_modeles.py", "GetHTML", "html")


def _install_stub_modules():
    saved = {name: sys.modules.get(name) for name in (
        "wx", "wx.html", "Chemins", "Ctrl", "Ctrl.CTRL_Bouton_image", "PIL", "PIL.Image",
        "GestionDB", "Utils", "Utils.UTILS_Dates", "Utils.UTILS_Traduction",
        "numpy", "matplotlib", "matplotlib.pyplot",
    )}

    wx = types.ModuleType("wx")

    class _FileSystem(object):
        @staticmethod
        def AddHandler(handler):
            return None

    class _MemoryFSHandler(object):
        pass

    wx.FileSystem = _FileSystem
    wx.MemoryFSHandler = _MemoryFSHandler
    wx.Frame = object
    sys.modules["wx"] = wx
    sys.modules["wx.html"] = types.ModuleType("wx.html")

    sys.modules["Chemins"] = types.ModuleType("Chemins")

    ctrl_pkg = types.ModuleType("Ctrl")
    ctrl_bouton_image = types.ModuleType("Ctrl.CTRL_Bouton_image")
    sys.modules["Ctrl"] = ctrl_pkg
    sys.modules["Ctrl.CTRL_Bouton_image"] = ctrl_bouton_image

    pil_pkg = types.ModuleType("PIL")
    pil_image = types.ModuleType("PIL.Image")
    sys.modules["PIL"] = pil_pkg
    sys.modules["PIL.Image"] = pil_image

    sys.modules["GestionDB"] = types.ModuleType("GestionDB")

    utils_pkg = types.ModuleType("Utils")
    utils_pkg.__path__ = []  # marque le module comme un paquet
    utils_traduction = types.ModuleType("Utils.UTILS_Traduction")
    utils_traduction._ = lambda texte: texte
    utils_dates = types.ModuleType("Utils.UTILS_Dates")
    sys.modules["Utils"] = utils_pkg
    sys.modules["Utils.UTILS_Traduction"] = utils_traduction
    sys.modules["Utils.UTILS_Dates"] = utils_dates

    numpy_stub = types.ModuleType("numpy")
    for name in ("arange", "sqrt", "array", "asarray", "ones", "exp", "convolve", "linspace"):
        setattr(numpy_stub, name, lambda *a, **k: None)
    sys.modules["numpy"] = numpy_stub

    matplotlib_stub = types.ModuleType("matplotlib")
    matplotlib_stub.use = lambda *a, **k: None
    matplotlib_pyplot = types.ModuleType("matplotlib.pyplot")
    matplotlib_stub.pyplot = matplotlib_pyplot
    sys.modules["matplotlib"] = matplotlib_stub
    sys.modules["matplotlib.pyplot"] = matplotlib_pyplot

    return saved


def _restore_stub_modules(saved):
    for name, module in saved.items():
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module


def _load_module():
    saved = _install_stub_modules()
    try:
        sys.path.insert(0, str(NOETHYS))
        try:
            spec = importlib.util.spec_from_file_location(
                "UTILS_Stats_modeles_batch18", NOETHYS / "Utils" / "UTILS_Stats_modeles.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        finally:
            sys.path.remove(str(NOETHYS))
    finally:
        _restore_stub_modules(saved)


class TestBatch18StatsGetHTML(unittest.TestCase):
    def test_targeted_finding_disappears(self):
        path = NOETHYS / "Utils/UTILS_Stats_modeles.py"
        remaining = {
            (item["file"], item["function"], item["name"])
            for item in audit.scan_file(path, NOETHYS)
            if (item["file"], item["function"], item["name"]) == TARGET
        }
        self.assertEqual(remaining, set())

    def test_unsupported_mode_raises_explicit_error_instead_of_unbound_local(self):
        module = _load_module()
        html_obj = module.HTML(liste_objets=[])
        html_obj.SetParametres({"listeActivites": [1]})
        with self.assertRaises(ValueError):
            html_obj.GetHTML(mode="typo_mode")

    def test_affichage_mode_still_returns_html_unchanged(self):
        module = _load_module()
        html_obj = module.HTML(liste_objets=[])
        html_obj.SetParametres({"listeActivites": [1]})
        resultat = html_obj.GetHTML(mode="affichage")
        self.assertIn("<HTML>", resultat)
        self.assertIn("</HTML>", resultat)

    def test_empty_activites_short_circuits_before_mode_check(self):
        module = _load_module()
        html_obj = module.HTML(liste_objets=[])
        html_obj.SetParametres({"listeActivites": []})
        self.assertEqual(html_obj.GetHTML(mode="typo_mode"), "")


if __name__ == "__main__":
    unittest.main()
