# -*- coding: utf-8 -*-
import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path


def _load_config(root):
    chemins = types.ModuleType("Chemins")
    sys.modules["Chemins"] = chemins

    wx = types.ModuleType("wx")
    sys.modules["wx"] = wx

    six = types.ModuleType("six")
    six.PY2 = False
    sys.modules["six"] = six

    utils_pkg = types.ModuleType("Utils")
    utils_pkg.__path__ = []
    sys.modules["Utils"] = utils_pkg

    fichiers = types.ModuleType("Utils.UTILS_Fichiers")
    fichiers.GetRepUtilisateur = lambda fichier="": str(Path(root) / fichier)
    sys.modules["Utils.UTILS_Fichiers"] = fichiers
    utils_pkg.UTILS_Fichiers = fichiers

    json_utils = types.ModuleType("Utils.UTILS_Json")

    def _lire(_path):
        raise FileNotFoundError(_path)

    json_utils.Lire = _lire
    json_utils.Ecrire = lambda **kwargs: None
    sys.modules["Utils.UTILS_Json"] = json_utils
    utils_pkg.UTILS_Json = json_utils

    path = Path(__file__).resolve().parents[1] / "noethys" / "Utils" / "UTILS_Config.py"
    spec = importlib.util.spec_from_file_location("config_empty_database_contract", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConfigEmptyDatabaseContractTests(unittest.TestCase):
    def test_missing_config_keeps_historical_empty_database_name(self):
        with tempfile.TemporaryDirectory() as temp:
            module = _load_config(temp)
            cfg = module.FichierConfig()
            self.assertEqual(cfg.GetItemConfig("nomFichier"), "")

    def test_other_missing_keys_keep_their_requested_default(self):
        with tempfile.TemporaryDirectory() as temp:
            module = _load_config(temp)
            cfg = module.FichierConfig()
            self.assertIsNone(cfg.GetItemConfig("autre"))
            self.assertEqual(cfg.GetItemConfig("autre", "repli"), "repli")


if __name__ == "__main__":
    unittest.main()
