# -*- coding: utf-8 -*-
import importlib.util
import sys
import tempfile
import types
import unittest
import zipfile
from pathlib import Path
from unittest import mock


class _Dialog(object):
    def __init__(self, *args, **kwargs):
        pass

    def ShowModal(self):
        return 5103  # wx.ID_YES

    def Destroy(self):
        pass


class _Progress(_Dialog):
    def Update(self, *args, **kwargs):
        return True


class _FakeDB(object):
    echec = 0
    isNetwork = False

    def __init__(self, *args, **kwargs):
        pass

    def Close(self):
        pass


class _FakeProcess(object):
    returncode = 0

    def communicate(self):
        return b"", None


def _install_stub_modules(data_dir, temp_dir):
    wx = types.ModuleType("wx")
    wx.ID_YES = 5103
    wx.YES_NO = wx.CANCEL = wx.NO_DEFAULT = wx.ICON_EXCLAMATION = 0
    wx.OK = wx.ICON_ERROR = wx.PD_SMOOTH = wx.PD_AUTO_HIDE = wx.PD_APP_MODAL = 0
    wx.MessageDialog = _Dialog
    wx.ProgressDialog = _Progress
    sys.modules["wx"] = wx

    six = types.ModuleType("six")
    six.PY2 = False
    six.PY3 = True
    sys.modules["six"] = six

    sys.modules["Chemins"] = types.ModuleType("Chemins")

    gestion = types.ModuleType("GestionDB")
    gestion.DB = _FakeDB
    sys.modules["GestionDB"] = gestion

    utils_pkg = types.ModuleType("Utils")
    utils_pkg.__path__ = []
    sys.modules["Utils"] = utils_pkg

    traduction = types.ModuleType("Utils.UTILS_Traduction")
    traduction._ = lambda value: value
    sys.modules["Utils.UTILS_Traduction"] = traduction

    fichiers = types.ModuleType("Utils.UTILS_Fichiers")
    fichiers.GetRepData = lambda fichier=None: str(data_dir / fichier) if fichier else str(data_dir)
    fichiers.GetRepTemp = lambda fichier=None: str(temp_dir / fichier) if fichier else str(temp_dir)
    sys.modules["Utils.UTILS_Fichiers"] = fichiers
    utils_pkg.UTILS_Fichiers = fichiers

    config = types.ModuleType("Utils.UTILS_Config")
    sys.modules["Utils.UTILS_Config"] = config
    utils_pkg.UTILS_Config = config

    cryptage = types.ModuleType("Utils.UTILS_Cryptage_fichier")
    sys.modules["Utils.UTILS_Cryptage_fichier"] = cryptage
    utils_pkg.UTILS_Cryptage_fichier = cryptage

    email = types.ModuleType("Utils.UTILS_Envoi_email")
    email.Message = lambda **kwargs: kwargs
    sys.modules["Utils.UTILS_Envoi_email"] = email
    utils_pkg.UTILS_Envoi_email = email

    customize = types.ModuleType("Utils.UTILS_Customize")
    customize.GetValeur = lambda *args, **kwargs: None
    sys.modules["Utils.UTILS_Customize"] = customize
    utils_pkg.UTILS_Customize = customize


def _load_module(data_dir, temp_dir):
    _install_stub_modules(data_dir, temp_dir)
    path = Path(__file__).resolve().parents[1] / "noethys" / "Utils" / "UTILS_Sauvegarde.py"
    spec = importlib.util.spec_from_file_location("noe032_sauvegarde", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RestoreFlowTests(unittest.TestCase):
    def test_local_restore_extracts_and_reports_restored_file(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            archive = root / "backup.nod"
            with zipfile.ZipFile(str(archive), "w") as zf:
                zf.writestr("demo_DATA.dat", b"restored")

            module = _load_module(data_dir, temp_dir)
            result = module.Restauration(
                fichier=str(archive),
                listeFichiersLocaux=["demo_DATA.dat"],
            )

            self.assertEqual(result, ["demo_DATA"])
            self.assertEqual((data_dir / "demo_DATA.dat").read_bytes(), b"restored")

    def test_local_restore_can_replace_existing_file_after_confirmation(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            (data_dir / "demo_DATA.dat").write_bytes(b"old")
            archive = root / "backup.nod"
            with zipfile.ZipFile(str(archive), "w") as zf:
                zf.writestr("demo_DATA.dat", b"new")

            module = _load_module(data_dir, temp_dir)
            result = module.Restauration(
                fichier=str(archive),
                listeFichiersLocaux=["demo_DATA.dat"],
            )

            self.assertEqual(result, ["demo_DATA"])
            self.assertEqual((data_dir / "demo_DATA.dat").read_bytes(), b"new")

    def test_network_restore_reports_success_when_mysql_import_succeeds(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            archive = root / "backup.nod"
            with zipfile.ZipFile(str(archive), "w") as zf:
                zf.writestr("demo_data.sql", b"SELECT 1;")

            module = _load_module(data_dir, temp_dir)
            module.GetListeFichiersReseau = lambda values: []
            module.GetRepertoireMySQL = lambda values: "/fake/mysql/"
            module.CreationFichierLoginTemp = lambda **kwargs: Path(kwargs["nomFichier"]).write_text("[client]\n")
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "test"}

            with mock.patch.object(module.subprocess, "Popen", return_value=_FakeProcess()):
                result = module.Restauration(
                    fichier=str(archive),
                    listeFichiersReseau=["demo_data.sql"],
                    dictConnexion=params,
                )

            self.assertEqual(result, ["demo_data"])


if __name__ == "__main__":
    unittest.main()
