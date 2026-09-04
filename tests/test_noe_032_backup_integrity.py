# -*- coding: utf-8 -*-
import importlib.util
import re
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
        self.resultat = []

    def Close(self):
        pass

    def ExecuterReq(self, req):
        self.resultat = []
        return 1

    def ResultatReq(self):
        return self.resultat


class _FailProcess(object):
    returncode = 1

    def communicate(self):
        return b"simulated failure", None


class _DumpProcess(object):
    returncode = 0

    def __init__(self, args):
        self.args = args

    def communicate(self):
        chemin = re.search(r'>\s+"([^"]+)"', self.args).group(1)
        Path(chemin).write_bytes(b"CREATE TABLE `test_restore` (id INTEGER);\n")
        return b"", None


class _FailingTransport(object):
    def __init__(self, *args, **kwargs):
        self.closed = False

    def Connecter(self):
        pass

    def Envoyer(self, message):
        raise RuntimeError("simulated email failure")

    def Fermer(self):
        self.closed = True


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
    gestion.DecodeMdpReseau = lambda value: value
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
    email.GetAdresseExpDefaut = lambda: {
        "moteur": "smtp",
        "smtp": "localhost",
        "port": 25,
        "utilisateur": "test",
        "motdepasse": "test",
        "adresse": "test@example.invalid",
        "startTLS": False,
        "parametres": {},
    }
    sys.modules["Utils.UTILS_Envoi_email"] = email
    utils_pkg.UTILS_Envoi_email = email

    customize = types.ModuleType("Utils.UTILS_Customize")
    customize.GetValeur = lambda *args, **kwargs: None
    sys.modules["Utils.UTILS_Customize"] = customize
    utils_pkg.UTILS_Customize = customize


def _load_module(data_dir, temp_dir):
    _install_stub_modules(data_dir, temp_dir)
    path = Path(__file__).resolve().parents[1] / "noethys" / "Utils" / "UTILS_Sauvegarde.py"
    spec = importlib.util.spec_from_file_location("noe032b_sauvegarde", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BackupIntegrityTests(unittest.TestCase):
    def test_network_backup_without_connection_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()

            module = _load_module(data_dir, temp_dir)
            result = module.Sauvegarde(
                listeFichiersReseau=["demo_data"],
                nom="backup",
                dictConnexion=None,
            )

            self.assertFalse(result)
            self.assertFalse((temp_dir / "backup.nod").exists())

    def test_successful_network_backup_embeds_terminal_sql_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            output_dir = root / "output"
            data_dir.mkdir()
            temp_dir.mkdir()
            output_dir.mkdir()

            module = _load_module(data_dir, temp_dir)
            module.GetRepertoireMySQL = lambda values: "/fake/mysql/"
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "secret"}

            with mock.patch.object(module.subprocess, "Popen", side_effect=lambda args, **kwargs: _DumpProcess(args)):
                result = module.Sauvegarde(
                    listeFichiersReseau=["demo_data"],
                    nom="backup",
                    repertoire=str(output_dir),
                    dictConnexion=params,
                )

            self.assertTrue(result)
            with zipfile.ZipFile(str(output_dir / "backup.nod"), "r") as zf:
                sql = zf.read("demo_data.sql")
            charge, avecManifeste, erreur = module._ExtraireChargeSQL(sql)
            self.assertIsNone(erreur)
            self.assertTrue(avecManifeste)
            self.assertEqual(charge, b"CREATE TABLE `test_restore` (id INTEGER);\n")
            self.assertFalse((temp_dir / "savetemp").exists())
            self.assertFalse((temp_dir / "backup.nod").exists())

    def test_sql_manifest_rejects_same_size_payload_tampering(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            dump = root / "source.sql"
            dump.write_bytes(b"CREATE TABLE `first_table` (id INTEGER);\n")

            module = _load_module(data_dir, temp_dir)
            module._AjouterManifesteIntegriteSQL(str(dump))
            contenu = bytearray(dump.read_bytes())
            position = contenu.index(b"first_table")
            contenu[position] = ord("x")

            charge, avecManifeste, erreur = module._ExtraireChargeSQL(bytes(contenu))

            self.assertIsNone(charge)
            self.assertTrue(avecManifeste)
            self.assertIn("empreinte", erreur)

    def test_missing_local_file_closes_zip_and_removes_partial_archive(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()

            module = _load_module(data_dir, temp_dir)
            real_zip_file = module.zipfile.ZipFile
            opened = []

            class _TrackingZip(object):
                def __init__(self, *args, **kwargs):
                    self.inner = real_zip_file(*args, **kwargs)
                    self.closed = False
                    opened.append(self)

                def write(self, *args, **kwargs):
                    return self.inner.write(*args, **kwargs)

                def close(self):
                    self.closed = True
                    self.inner.close()

            with mock.patch.object(module.zipfile, "ZipFile", _TrackingZip):
                result = module.Sauvegarde(
                    listeFichiersLocaux=["missing_DATA.dat"],
                    nom="backup",
                )

            self.assertFalse(result)
            self.assertTrue(opened[0].closed)
            self.assertFalse((temp_dir / "backup.nod").exists())

    def test_failed_network_backup_removes_login_and_temp_archive(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()

            module = _load_module(data_dir, temp_dir)
            module.GetRepertoireMySQL = lambda values: "/fake/mysql/"
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "secret"}

            with mock.patch.object(module.subprocess, "Popen", return_value=_FailProcess()) as popen:
                result = module.Sauvegarde(
                    listeFichiersReseau=["demo_data"],
                    nom="backup",
                    dictConnexion=params,
                )

            args = popen.call_args.args[0]
            self.assertLess(args.index("--opt"), args.index("--single-transaction"))
            self.assertLess(args.index("--single-transaction"), args.index("--skip-lock-tables"))
            self.assertFalse(result)
            self.assertFalse((temp_dir / "savetemp").exists())
            self.assertFalse((temp_dir / "backup.nod").exists())

    def test_popen_exception_during_backup_is_contained_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()

            module = _load_module(data_dir, temp_dir)
            module.GetRepertoireMySQL = lambda values: "/fake/mysql/"
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "secret"}

            with mock.patch.object(module.subprocess, "Popen", side_effect=OSError("mysqldump unavailable")):
                result = module.Sauvegarde(
                    listeFichiersReseau=["demo_data"],
                    nom="backup",
                    dictConnexion=params,
                )

            self.assertFalse(result)
            self.assertFalse((temp_dir / "savetemp").exists())
            self.assertFalse((temp_dir / "backup.nod").exists())

    def test_failed_network_restore_removes_login_directory(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            archive = root / "backup.nod"
            with zipfile.ZipFile(str(archive), "w") as zf:
                zf.writestr("demo_data.sql", b"CREATE TABLE `test_restore` (id INTEGER);\n")

            module = _load_module(data_dir, temp_dir)
            module.GetListeFichiersReseau = lambda values: []
            module.GetRepertoireMySQL = lambda values: "/fake/mysql/"
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "secret"}

            with mock.patch.object(module.subprocess, "Popen", return_value=_FailProcess()):
                result = module.Restauration(
                    fichier=str(archive),
                    listeFichiersReseau=["demo_data.sql"],
                    dictConnexion=params,
                )

            self.assertFalse(result)
            self.assertFalse((temp_dir / "restoretemp").exists())

    def test_popen_exception_during_restore_is_contained_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            archive = root / "backup.nod"
            with zipfile.ZipFile(str(archive), "w") as zf:
                zf.writestr("demo_data.sql", b"CREATE TABLE `test_restore` (id INTEGER);\n")

            module = _load_module(data_dir, temp_dir)
            module.GetListeFichiersReseau = lambda values: []
            module.GetRepertoireMySQL = lambda values: "/fake/mysql/"
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "secret"}

            with mock.patch.object(module.subprocess, "Popen", side_effect=OSError("mysql unavailable")):
                result = module.Restauration(
                    fichier=str(archive),
                    listeFichiersReseau=["demo_data.sql"],
                    dictConnexion=params,
                )

            self.assertFalse(result)
            self.assertFalse((temp_dir / "restoretemp").exists())

    def test_extract_exception_during_restore_is_contained_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            archive = root / "backup.nod"
            with zipfile.ZipFile(str(archive), "w") as zf:
                zf.writestr("demo_data.sql", b"CREATE TABLE `test_restore` (id INTEGER);\n")

            module = _load_module(data_dir, temp_dir)
            module.GetListeFichiersReseau = lambda values: []
            module.GetRepertoireMySQL = lambda values: "/fake/mysql/"
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "secret"}

            with mock.patch.object(module.zipfile.ZipFile, "extract", side_effect=OSError("extract failure")):
                result = module.Restauration(
                    fichier=str(archive),
                    listeFichiersReseau=["demo_data.sql"],
                    dictConnexion=params,
                )

            self.assertFalse(result)
            self.assertFalse((temp_dir / "restoretemp").exists())

    def test_failed_email_closes_transport_and_removes_temp_archive(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            (data_dir / "demo_DATA.dat").write_bytes(b"data")

            module = _load_module(data_dir, temp_dir)
            transport = _FailingTransport()
            module.UTILS_Envoi_email.Messagerie = lambda **kwargs: transport

            result = module.Sauvegarde(
                listeFichiersLocaux=["demo_DATA.dat"],
                nom="backup",
                listeEmails=["recipient@example.invalid"],
            )

            self.assertFalse(result)
            self.assertTrue(transport.closed)
            self.assertFalse((temp_dir / "backup.nod").exists())


if __name__ == "__main__":
    unittest.main()
