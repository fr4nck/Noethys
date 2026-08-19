# -*- coding: utf-8 -*-
import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path


def _load_utils_files(root):
    chemins = types.ModuleType("Chemins")
    chemins.GetMainPath = lambda fichier="": str(Path(root) / fichier)
    chemins.GetStaticPath = lambda fichier="": str(Path(root) / "Static" / fichier)
    sys.modules["Chemins"] = chemins

    utils_pkg = types.ModuleType("Utils")
    utils_pkg.__path__ = []
    sys.modules["Utils"] = utils_pkg

    customize = types.ModuleType("Utils.UTILS_Customize")
    customize.GetValeur = lambda *args, **kwargs: ""
    sys.modules["Utils.UTILS_Customize"] = customize
    utils_pkg.UTILS_Customize = customize

    appdirs = types.ModuleType("appdirs")
    appdirs.site_data_dir = lambda **kwargs: str(Path(root) / "outside-site-data")
    appdirs.user_data_dir = lambda **kwargs: str(Path(root) / "outside-user-data")
    appdirs.user_config_dir = lambda **kwargs: str(Path(root) / "outside-user-config")
    sys.modules["appdirs"] = appdirs

    six = types.ModuleType("six")
    six.PY2 = False
    six.PY3 = True
    sys.modules["six"] = six

    path = Path(__file__).resolve().parents[1] / "noethys" / "Utils" / "UTILS_Fichiers.py"
    spec = importlib.util.spec_from_file_location("noe041_utils_fichiers", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PortablePathsTests(unittest.TestCase):
    def test_portable_marker_isolates_config_and_data(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            portable = root / "Portable"
            portable.mkdir()
            module = _load_utils_files(root)

            self.assertEqual(Path(module.GetRepUtilisateur("Config.json")), portable / "Config.json")
            self.assertEqual(Path(module.GetRepData("demo_DATA.dat")), portable / "Data" / "demo_DATA.dat")
            self.assertTrue((portable / "Data").is_dir())

    def test_portable_runtime_subdirectories_are_created_on_demand(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            portable = root / "Portable"
            portable.mkdir()
            module = _load_utils_files(root)

            expected = {
                "Temp": module.GetRepTemp("journal.tmp"),
                "Updates": module.GetRepUpdates("update.bin"),
                "Lang": module.GetRepLang("fr.xlang"),
                "Sync": module.GetRepSync("sync.json"),
                "Extensions": module.GetRepExtensions("plugin.py"),
            }
            for dirname, path in expected.items():
                self.assertEqual(Path(path).parent, portable / dirname)
                self.assertTrue((portable / dirname).is_dir())

    def test_portable_mode_does_not_use_appdirs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "Portable").mkdir()
            module = _load_utils_files(root)

            config = Path(module.GetRepUtilisateur("Config.json"))
            data = Path(module.GetRepData("demo.dat"))
            self.assertNotIn("outside-", str(config))
            self.assertNotIn("outside-", str(data))


if __name__ == "__main__":
    unittest.main()
