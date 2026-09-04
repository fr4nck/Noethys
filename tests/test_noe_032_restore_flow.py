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

    def GetListeTables(self):
        return []

    def ExecuterReq(self, req):
        self.resultat = []
        return 0

    def ResultatReq(self):
        return self.resultat


class _FakeProcess(object):
    returncode = 0

    def communicate(self):
        return b"", None


class _MysqlProcess(object):
    returncode = 0

    def __init__(self, args, state, mode):
        self.args = args
        self.state = state
        self.mode = mode

    def communicate(self):
        chemin = re.search(r'<\s+"([^"]+)"', self.args).group(1)
        sql = Path(chemin).read_text(encoding="utf-8")
        jeton = re.search(r"^-- NOETHYS-RESTORE-END-V1 ([0-9a-f]{32})$", sql, re.MULTILINE).group(1)
        marqueur = "__noethys_restore_%s" % jeton

        tables = re.findall(
            r"\bCREATE\s+TABLE\s+(?:`[^`]+`\s*\.\s*)?`([^`]+)`",
            sql,
            re.IGNORECASE,
        )
        vues = re.findall(
            r"\bCREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(?:`[^`]+`\s*\.\s*)?`([^`]+)`",
            sql,
            re.IGNORECASE,
        )
        objetsSecondaires = {
            "triggers": re.findall(
                r"\bTRIGGER\s+(?:`[^`]+`\s*\.\s*)?`([^`]+)`", sql, re.IGNORECASE
            ),
            "procedures": re.findall(
                r"\bPROCEDURE\s+(?:`[^`]+`\s*\.\s*)?`([^`]+)`", sql, re.IGNORECASE
            ),
            "fonctions": re.findall(
                r"\bFUNCTION\s+(?:`[^`]+`\s*\.\s*)?`([^`]+)`", sql, re.IGNORECASE
            ),
            "evenements": re.findall(
                r"\bEVENT\s+(?:`[^`]+`\s*\.\s*)?`([^`]+)`", sql, re.IGNORECASE
            ),
        }
        tablesMetier = [nom.lower() for nom in tables if nom.lower() != marqueur.lower()]

        if self.mode == "complete":
            self.state["tables"].update(tablesMetier)
            self.state["vues"].update(nom.lower() for nom in vues)
            for categorie, noms in objetsSecondaires.items():
                self.state[categorie].update(nom.lower() for nom in noms)
            self.state["tables"].add(marqueur.lower())
            self.state["marqueurs"][marqueur.lower()] = jeton
        elif self.mode == "interrupt_after_first":
            if tablesMetier:
                self.state["tables"].add(tablesMetier[0])
        elif self.mode == "marker_but_missing_last":
            self.state["tables"].update(tablesMetier[:-1])
            self.state["vues"].update(nom.lower() for nom in vues)
            for categorie, noms in objetsSecondaires.items():
                self.state[categorie].update(nom.lower() for nom in noms)
            self.state["tables"].add(marqueur.lower())
            self.state["marqueurs"][marqueur.lower()] = jeton
        elif self.mode == "marker_but_missing_event":
            self.state["tables"].update(tablesMetier)
            self.state["vues"].update(nom.lower() for nom in vues)
            for categorie, noms in objetsSecondaires.items():
                if categorie != "evenements":
                    self.state[categorie].update(nom.lower() for nom in noms)
            self.state["tables"].add(marqueur.lower())
            self.state["marqueurs"][marqueur.lower()] = jeton
        else:
            raise AssertionError("mode mysql simulé inconnu : %s" % self.mode)

        return b"", None


def _new_state():
    return {
        "tables": set(),
        "vues": set(),
        "marqueurs": {},
        "triggers": set(),
        "procedures": set(),
        "fonctions": set(),
        "evenements": set(),
    }


def _make_stateful_db(state):
    class _StatefulDB(object):
        echec = 0
        isNetwork = True

        def __init__(self, *args, **kwargs):
            self.resultat = []

        def Close(self):
            pass

        def GetListeTables(self):
            return [(nom,) for nom in sorted(state["tables"] | state["vues"])]

        def ExecuterReq(self, req):
            reqUpper = req.upper()
            self.resultat = []

            if reqUpper.startswith("SELECT `JETON` FROM"):
                correspondance = re.search(r"FROM\s+`([^`]+)`", req, re.IGNORECASE)
                nomTable = correspondance.group(1).lower()
                jeton = state["marqueurs"].get(nomTable)
                if jeton is None:
                    return 0
                self.resultat = [(jeton,)]
                return 1

            if reqUpper.startswith("SHOW FULL TABLES"):
                self.resultat = [(nom, "BASE TABLE") for nom in sorted(state["tables"])]
                self.resultat.extend((nom, "VIEW") for nom in sorted(state["vues"]))
                return 1

            if "INFORMATION_SCHEMA.TRIGGERS" in reqUpper:
                self.resultat = [(nom,) for nom in sorted(state["triggers"])]
                return 1

            if "INFORMATION_SCHEMA.ROUTINES" in reqUpper:
                self.resultat = [(nom, "PROCEDURE") for nom in sorted(state["procedures"])]
                self.resultat.extend((nom, "FUNCTION") for nom in sorted(state["fonctions"]))
                return 1

            if "INFORMATION_SCHEMA.EVENTS" in reqUpper:
                self.resultat = [(nom,) for nom in sorted(state["evenements"])]
                return 1

            if reqUpper.startswith("DROP TABLE IF EXISTS"):
                correspondance = re.search(r"`([^`]+)`", req)
                nomTable = correspondance.group(1).lower()
                state["tables"].discard(nomTable)
                state["marqueurs"].pop(nomTable, None)
                return 1

            return 1

        def ResultatReq(self):
            return self.resultat

    return _StatefulDB


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


def _prepare_network_restore(module, state, mode):
    module.GetListeFichiersReseau = lambda values: []
    module.GetRepertoireMySQL = lambda values: "/fake/mysql/"
    module.CreationFichierLoginTemp = lambda **kwargs: Path(kwargs["nomFichier"]).write_text("[client]\n")
    module.GestionDB.DB = _make_stateful_db(state)

    def popen(args, **kwargs):
        return _MysqlProcess(args, state, mode)

    return popen


def _write_archive(archive, sql):
    with zipfile.ZipFile(str(archive), "w") as zf:
        zf.writestr("demo_data.sql", sql)


def _write_enveloped_archive(module, root, archive, sql):
    dump = root / "source.sql"
    dump.write_bytes(sql)
    module._AjouterManifesteIntegriteSQL(str(dump))
    _write_archive(archive, dump.read_bytes())


def _sql_with_all_supported_objects():
    return (
        b"CREATE TABLE `base_table` (`id` INTEGER);\n"
        b"CREATE VIEW `sample_view` AS SELECT `id` FROM `base_table`;\n"
        b"DELIMITER ;;\n"
        b"CREATE DEFINER=`root`@`localhost` TRIGGER `sample_trigger` "
        b"BEFORE INSERT ON `base_table` FOR EACH ROW SET NEW.`id` = NEW.`id`;;\n"
        b"CREATE PROCEDURE `sample_procedure`() BEGIN SELECT 1; END;;\n"
        b"CREATE FUNCTION `sample_function`() RETURNS INTEGER DETERMINISTIC RETURN 1;;\n"
        b"CREATE EVENT `sample_event` ON SCHEDULE EVERY 1 DAY "
        b"DO INSERT INTO `base_table` (`id`) VALUES (1);;\n"
        b"DELIMITER ;\n"
    )


class RestoreFlowTests(unittest.TestCase):
    def test_sql_analysis_tracks_only_top_level_objects_with_crlf_delimiters(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            dump = root / "legacy.sql"
            dump.write_bytes(
                b"CREATE TABLE `base_table` (`id` INTEGER);\r\n"
                b"DELIMITER ;;\r\n"
                b"/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ "
                b"/*!50003 TRIGGER `sample_trigger` BEFORE INSERT ON `base_table` "
                b"FOR EACH ROW\r\nBEGIN\r\n"
                b"  SET @texte = 'CREATE TABLE `not_a_real_table` (id INTEGER)';\r\n"
                b"END */;;\r\n"
                b"DELIMITER ;\r\n"
                b"/*!50001 CREATE ALGORITHM=UNDEFINED */\r\n"
                b"/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */\r\n"
                b"/*!50001 VIEW `sample_view` AS SELECT `id` FROM `base_table` */;\r\n"
            )
            module = _load_module(data_dir, temp_dir)

            analyse, erreur = module._AnalyserDumpSQL(str(dump))

            self.assertIsNone(erreur)
            self.assertFalse(analyse["avec_manifeste"])
            self.assertEqual(analyse["objets"]["tables"], {"base_table"})
            self.assertEqual(analyse["objets"]["vues"], {"sample_view"})
            self.assertEqual(analyse["objets"]["triggers"], {"sample_trigger"})

    def test_restore_with_no_selected_files_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            archive = root / "backup.nod"
            with zipfile.ZipFile(str(archive), "w"):
                pass

            module = _load_module(data_dir, temp_dir)
            result = module.Restauration(fichier=str(archive))

            self.assertEqual(result, [])

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

    def test_network_restore_accepts_complete_dump_with_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            archive = root / "backup.nod"
            module = _load_module(data_dir, temp_dir)
            _write_enveloped_archive(
                module,
                root,
                archive,
                b"CREATE TABLE `first_table` (id INTEGER);\nCREATE TABLE `second_table` (id INTEGER);\n",
            )
            state = _new_state()
            popen = _prepare_network_restore(module, state, "complete")
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "test"}

            with mock.patch.object(module.subprocess, "Popen", side_effect=popen):
                result = module.Restauration(
                    fichier=str(archive),
                    listeFichiersReseau=["demo_data.sql"],
                    dictConnexion=params,
                )

            self.assertEqual(result, ["demo_data"])
            self.assertEqual(state["tables"], {"first_table", "second_table"})
            self.assertEqual(state["marqueurs"], {})

    def test_network_restore_verifies_all_expected_object_categories(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            archive = root / "backup.nod"
            module = _load_module(data_dir, temp_dir)
            _write_enveloped_archive(module, root, archive, _sql_with_all_supported_objects())
            state = _new_state()
            popen = _prepare_network_restore(module, state, "complete")
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "test"}

            with mock.patch.object(module.subprocess, "Popen", side_effect=popen):
                result = module.Restauration(
                    fichier=str(archive),
                    listeFichiersReseau=["demo_data.sql"],
                    dictConnexion=params,
                )

            self.assertEqual(result, ["demo_data"])
            self.assertEqual(state["tables"], {"base_table"})
            self.assertEqual(state["vues"], {"sample_view"})
            self.assertEqual(state["triggers"], {"sample_trigger"})
            self.assertEqual(state["procedures"], {"sample_procedure"})
            self.assertEqual(state["fonctions"], {"sample_function"})
            self.assertEqual(state["evenements"], {"sample_event"})
            self.assertEqual(state["marqueurs"], {})

    def test_network_restore_rejects_missing_expected_event_after_terminal_marker(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            archive = root / "backup.nod"
            module = _load_module(data_dir, temp_dir)
            _write_enveloped_archive(module, root, archive, _sql_with_all_supported_objects())
            state = _new_state()
            popen = _prepare_network_restore(module, state, "marker_but_missing_event")
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "test"}

            with mock.patch.object(module.subprocess, "Popen", side_effect=popen):
                result = module.Restauration(
                    fichier=str(archive),
                    listeFichiersReseau=["demo_data.sql"],
                    dictConnexion=params,
                )

            self.assertFalse(result)
            self.assertEqual(state["evenements"], set())
            self.assertEqual(state["marqueurs"], {})

    def test_network_restore_accepts_legacy_dump_without_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            archive = root / "backup.nod"
            _write_archive(archive, b"CREATE TABLE `legacy_table` (id INTEGER);\n")
            module = _load_module(data_dir, temp_dir)
            state = _new_state()
            popen = _prepare_network_restore(module, state, "complete")
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "test"}

            with mock.patch.object(module.subprocess, "Popen", side_effect=popen):
                result = module.Restauration(
                    fichier=str(archive),
                    listeFichiersReseau=["demo_data.sql"],
                    dictConnexion=params,
                )

            self.assertEqual(result, ["demo_data"])
            self.assertEqual(state["tables"], {"legacy_table"})
            self.assertEqual(state["marqueurs"], {})

    def test_network_restore_rejects_interruption_after_some_create_table(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            archive = root / "backup.nod"
            module = _load_module(data_dir, temp_dir)
            _write_enveloped_archive(
                module,
                root,
                archive,
                b"CREATE TABLE `first_table` (id INTEGER);\nCREATE TABLE `second_table` (id INTEGER);\n",
            )
            state = _new_state()
            popen = _prepare_network_restore(module, state, "interrupt_after_first")
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "test"}

            with mock.patch.object(module.subprocess, "Popen", side_effect=popen) as mockedPopen:
                result = module.Restauration(
                    fichier=str(archive),
                    listeFichiersReseau=["demo_data.sql"],
                    dictConnexion=params,
                )

            self.assertFalse(result)
            mockedPopen.assert_called_once()
            self.assertEqual(state["tables"], {"first_table"})
            self.assertEqual(state["marqueurs"], {})

    def test_network_restore_rejects_terminal_marker_with_missing_expected_object(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            archive = root / "backup.nod"
            module = _load_module(data_dir, temp_dir)
            _write_enveloped_archive(
                module,
                root,
                archive,
                b"CREATE TABLE `first_table` (id INTEGER);\nCREATE TABLE `second_table` (id INTEGER);\n",
            )
            state = _new_state()
            popen = _prepare_network_restore(module, state, "marker_but_missing_last")
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "test"}

            with mock.patch.object(module.subprocess, "Popen", side_effect=popen):
                result = module.Restauration(
                    fichier=str(archive),
                    listeFichiersReseau=["demo_data.sql"],
                    dictConnexion=params,
                )

            self.assertFalse(result)
            self.assertEqual(state["tables"], {"first_table"})
            self.assertEqual(state["marqueurs"], {})

    def test_network_restore_rejects_truncated_manifest_dump_before_mysql(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            archive = root / "backup.nod"
            module = _load_module(data_dir, temp_dir)
            dump = root / "source.sql"
            dump.write_bytes(
                b"CREATE TABLE `first_table` (id INTEGER);\nCREATE TABLE `second_table` (id INTEGER);\n"
            )
            module._AjouterManifesteIntegriteSQL(str(dump))
            contenu = dump.read_bytes()
            contenuTronque = contenu[:contenu.index(b"CREATE TABLE `second_table`")]
            _write_archive(archive, contenuTronque)
            module.GetListeFichiersReseau = lambda values: []
            module.GetRepertoireMySQL = lambda values: "/fake/mysql/"
            module.CreationFichierLoginTemp = lambda **kwargs: Path(kwargs["nomFichier"]).write_text("[client]\n")
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "test"}

            with mock.patch.object(module.GestionDB, "DB") as mockedDB, mock.patch.object(module.subprocess, "Popen") as mockedPopen:
                result = module.Restauration(
                    fichier=str(archive),
                    listeFichiersReseau=["demo_data.sql"],
                    dictConnexion=params,
                )

            self.assertFalse(result)
            mockedDB.assert_not_called()
            mockedPopen.assert_not_called()
            self.assertFalse((temp_dir / "restoretemp").exists())

    def test_network_restore_rejects_legacy_sql_truncated_mid_statement(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            archive = root / "backup.nod"
            _write_archive(archive, b"CREATE TABLE `broken_table` (id INTEGER")
            module = _load_module(data_dir, temp_dir)
            module.GetListeFichiersReseau = lambda values: []
            module.GetRepertoireMySQL = lambda values: "/fake/mysql/"
            module.CreationFichierLoginTemp = lambda **kwargs: Path(kwargs["nomFichier"]).write_text("[client]\n")
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "test"}

            with mock.patch.object(module.GestionDB, "DB") as mockedDB, mock.patch.object(module.subprocess, "Popen") as mockedPopen:
                result = module.Restauration(
                    fichier=str(archive),
                    listeFichiersReseau=["demo_data.sql"],
                    dictConnexion=params,
                )

            self.assertFalse(result)
            mockedDB.assert_not_called()
            mockedPopen.assert_not_called()

    def test_network_restore_rejects_noop_sql_before_mysql(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            archive = root / "backup.nod"
            _write_archive(archive, b"SELECT 1;")

            module = _load_module(data_dir, temp_dir)
            module.GetListeFichiersReseau = lambda values: ["demo_data"]
            module.GetRepertoireMySQL = lambda values: "/fake/mysql/"
            module.CreationFichierLoginTemp = lambda **kwargs: Path(kwargs["nomFichier"]).write_text("[client]\n")
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "test"}

            with mock.patch.object(module.subprocess, "Popen", return_value=_FakeProcess()) as popen:
                result = module.Restauration(
                    fichier=str(archive),
                    listeFichiersReseau=["demo_data.sql"],
                    dictConnexion=params,
                )

            self.assertFalse(result)
            popen.assert_not_called()
            self.assertFalse((temp_dir / "restoretemp").exists())

    def test_network_restore_noop_does_not_create_missing_database(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            archive = root / "backup.nod"
            _write_archive(archive, b"SELECT 1;")

            module = _load_module(data_dir, temp_dir)
            module.GetListeFichiersReseau = lambda values: []
            module.GetRepertoireMySQL = lambda values: "/fake/mysql/"
            module.CreationFichierLoginTemp = lambda **kwargs: Path(kwargs["nomFichier"]).write_text("[client]\n")
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "test"}

            with mock.patch.object(module.GestionDB, "DB") as db, mock.patch.object(module.subprocess, "Popen", return_value=_FakeProcess()) as popen:
                result = module.Restauration(
                    fichier=str(archive),
                    listeFichiersReseau=["demo_data.sql"],
                    dictConnexion=params,
                )

            self.assertFalse(result)
            db.assert_not_called()
            popen.assert_not_called()
            self.assertFalse((temp_dir / "restoretemp").exists())

    def test_network_restore_rejects_mysql_success_without_terminal_marker(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            data_dir = root / "data"
            temp_dir = root / "temp"
            data_dir.mkdir()
            temp_dir.mkdir()
            archive = root / "backup.nod"
            _write_archive(archive, b"CREATE TABLE `test_restore` (id INTEGER);\n")

            module = _load_module(data_dir, temp_dir)
            module.GetListeFichiersReseau = lambda values: ["demo_data"]
            module.GetRepertoireMySQL = lambda values: "/fake/mysql/"
            module.CreationFichierLoginTemp = lambda **kwargs: Path(kwargs["nomFichier"]).write_text("[client]\n")
            state = _new_state()
            module.GestionDB.DB = _make_stateful_db(state)
            params = {"host": "localhost", "port": 3306, "user": "test", "password": "test"}

            with mock.patch.object(module.subprocess, "Popen", return_value=_FakeProcess()) as popen:
                result = module.Restauration(
                    fichier=str(archive),
                    listeFichiersReseau=["demo_data.sql"],
                    dictConnexion=params,
                )

            self.assertFalse(result)
            popen.assert_called_once()
            self.assertFalse((temp_dir / "restoretemp").exists())


if __name__ == "__main__":
    unittest.main()
