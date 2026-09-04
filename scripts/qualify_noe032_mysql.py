#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Qualification NOE-032c contre un vrai serveur MySQL jetable.

Ce script n'utilise aucune base Noethys existante. Il crée des bases temporaires,
importe du SQL avec le vrai client mysql, puis exerce les postconditions de
UTILS_Sauvegarde sur les catalogues réels du serveur.
"""

import argparse
import importlib.util
import os
import subprocess
import sys
import tempfile
import types
import uuid


def _run_mysql(host, port, user, password, sql=None, database=None, stdin_path=None):
    cmd = [
        "mysql",
        "--protocol=TCP",
        "-h", host,
        "-P", str(port),
        "-u", user,
        "-p%s" % password,
        "--batch",
        "--raw",
        "--skip-column-names",
    ]
    if database:
        cmd.append(database)
    if sql is not None:
        cmd.extend(["-e", sql])
        return subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if stdin_path is not None:
        with open(stdin_path, "rb") as stream:
            return subprocess.run(cmd, check=False, stdin=stream, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    raise ValueError("sql ou stdin_path requis")


def _install_import_stubs():
    sys.modules.setdefault("Chemins", types.ModuleType("Chemins"))

    wx = types.ModuleType("wx")
    wx.OK = 0
    wx.ICON_ERROR = 0
    wx.YES_NO = 0
    wx.NO_DEFAULT = 0
    wx.ICON_EXCLAMATION = 0
    wx.ID_YES = 1
    wx.MessageBox = lambda *args, **kwargs: wx.ID_YES
    sys.modules["wx"] = wx

    gestiondb = types.ModuleType("GestionDB")
    sys.modules["GestionDB"] = gestiondb

    utils_pkg = types.ModuleType("Utils")
    utils_pkg.__path__ = []
    sys.modules["Utils"] = utils_pkg

    traduction = types.ModuleType("Utils.UTILS_Traduction")
    traduction._ = lambda texte: texte
    sys.modules["Utils.UTILS_Traduction"] = traduction

    for name in (
        "UTILS_Fichiers",
        "UTILS_Config",
        "UTILS_Cryptage_fichier",
        "UTILS_Envoi_email",
        "UTILS_Customize",
    ):
        module = types.ModuleType("Utils.%s" % name)
        setattr(utils_pkg, name, module)
        sys.modules["Utils.%s" % name] = module

    return gestiondb


def _load_backup_module(repo_root):
    gestiondb = _install_import_stubs()
    path = os.path.join(repo_root, "noethys", "Utils", "UTILS_Sauvegarde.py")
    spec = importlib.util.spec_from_file_location("noe032_utils_sauvegarde", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, gestiondb


def _split_network_name(value):
    prefix, database = value.split("[RESEAU]", 1)
    port, host, user, password = prefix.split(";", 3)
    return host, int(port), user, password, database


class CliDB:
    def __init__(self, nom_fichier):
        self.host, self.port, self.user, self.password, self.database = _split_network_name(nom_fichier)
        self._result = []
        probe = _run_mysql(self.host, self.port, self.user, self.password, "SELECT 1;", self.database)
        self.echec = 0 if probe.returncode == 0 else 1

    def ExecuterReq(self, requete):
        proc = _run_mysql(self.host, self.port, self.user, self.password, requete, self.database)
        if proc.returncode != 0:
            self._result = []
            return 0
        rows = []
        for line in proc.stdout.splitlines():
            rows.append(tuple(part for part in line.split("\t")))
        self._result = rows
        return 1

    def ResultatReq(self):
        return self._result

    def Close(self):
        return None


def _fixture_sql(database):
    return """\
CREATE TABLE `parent` (`id` INT NOT NULL PRIMARY KEY, `value` INT NOT NULL);
CREATE TABLE `audit_log` (`id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY, `parent_id` INT NOT NULL);
INSERT INTO `parent` (`id`, `value`) VALUES (1, 10);
CREATE VIEW `v_parent` AS SELECT `id`, `value` FROM `parent`;
DELIMITER $$
CREATE TRIGGER `tr_parent_ai` AFTER INSERT ON `parent`
FOR EACH ROW BEGIN
  INSERT INTO `audit_log` (`parent_id`) VALUES (NEW.`id`);
END$$
CREATE PROCEDURE `p_parent_count` ()
BEGIN
  SELECT COUNT(*) FROM `parent`;
END$$
CREATE FUNCTION `f_parent_value` (`p_id` INT) RETURNS INT
DETERMINISTIC READS SQL DATA
BEGIN
  DECLARE `v` INT;
  SELECT `value` INTO `v` FROM `parent` WHERE `id` = `p_id`;
  RETURN `v`;
END$$
CREATE EVENT `ev_parent_touch`
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP + INTERVAL 1 DAY
DO UPDATE `parent` SET `value` = `value` WHERE `id` = 1$$
DELIMITER ;
"""


def _assert(condition, message):
    if not condition:
        raise AssertionError(message)


def _create_database(conn, database):
    proc = _run_mysql(conn["host"], conn["port"], conn["user"], conn["password"],
                      "DROP DATABASE IF EXISTS `{0}`; CREATE DATABASE `{0}` CHARACTER SET utf8mb4;".format(database))
    _assert(proc.returncode == 0, "création base impossible: %s" % proc.stderr)


def _drop_database(conn, database):
    _run_mysql(conn["host"], conn["port"], conn["user"], conn["password"],
               "DROP DATABASE IF EXISTS `{0}`;".format(database))


def _import_and_verify(module, conn, database, sql_path, with_manifest):
    if with_manifest:
        module._AjouterManifesteIntegriteSQL(sql_path)

    analyse, erreur = module._AnalyserDumpSQL(sql_path)
    _assert(erreur is None, "analyse du dump refusée: %s" % erreur)
    _assert(analyse["avec_manifeste"] is with_manifest, "état manifeste inattendu")

    marqueur = module._AjouterMarqueurTerminalSQL(sql_path, database)
    proc = _run_mysql(conn["host"], conn["port"], conn["user"], conn["password"], database=database, stdin_path=sql_path)
    stderr = proc.stderr.decode("utf-8", "replace") if isinstance(proc.stderr, bytes) else proc.stderr
    _assert(proc.returncode == 0, "import mysql échoué: %s" % stderr)

    ok, diagnostic = module._VerifierPostconditionRestaurationMySQL(conn, database, marqueur, analyse["objets"])
    _assert(ok, "postcondition refusée: %s" % diagnostic)

    probe = _run_mysql(conn["host"], conn["port"], conn["user"], conn["password"],
                       "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='%s' AND TABLE_NAME='%s';" % (database, marqueur["table"]))
    _assert(probe.returncode == 0 and probe.stdout.strip() == "0", "le marqueur terminal n'a pas été nettoyé")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.environ.get("NOE032_MYSQL_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("NOE032_MYSQL_PORT", "3306")))
    parser.add_argument("--user", default=os.environ.get("NOE032_MYSQL_USER", "root"))
    parser.add_argument("--password", default=os.environ.get("NOE032_MYSQL_PASSWORD", "noethys"))
    args = parser.parse_args()

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    module, gestiondb = _load_backup_module(repo_root)
    conn = {"host": args.host, "port": str(args.port), "user": args.user, "password": args.password}
    gestiondb.DB = lambda suffixe=None, nomFichier=None: CliDB(nomFichier)

    probe = _run_mysql(args.host, args.port, args.user, args.password, "SELECT VERSION();")
    _assert(probe.returncode == 0, "serveur MySQL inaccessible: %s" % probe.stderr)
    print("Serveur:", probe.stdout.strip())

    suffix = uuid.uuid4().hex[:8]
    db_manifest = "noe032_manifest_%s" % suffix
    db_legacy = "noe032_legacy_%s" % suffix
    db_partial = "noe032_partial_%s" % suffix

    try:
        with tempfile.TemporaryDirectory(prefix="noe032-mysql-") as tempdir:
            # 1. Nouveau dump manifesté, avec tous les types d'objets contrôlés.
            _create_database(conn, db_manifest)
            manifest_path = os.path.join(tempdir, "manifest.sql")
            with open(manifest_path, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(_fixture_sql(db_manifest))
            _import_and_verify(module, conn, db_manifest, manifest_path, True)
            print("OK: dump manifesté + tables/vues/triggers/routines/événements")

            # 2. Ancien dump sans manifeste : même postcondition forte.
            _create_database(conn, db_legacy)
            legacy_path = os.path.join(tempdir, "legacy.sql")
            with open(legacy_path, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(_fixture_sql(db_legacy))
            _import_and_verify(module, conn, db_legacy, legacy_path, False)
            print("OK: ancien dump sans manifeste")

            # 3. Dump manifesté tronqué : refus avant import.
            truncated_path = os.path.join(tempdir, "truncated.sql")
            with open(truncated_path, "w", encoding="utf-8", newline="\n") as stream:
                stream.write("CREATE TABLE `t` (`id` INT);\n")
            module._AjouterManifesteIntegriteSQL(truncated_path)
            with open(truncated_path, "rb+") as stream:
                stream.seek(-12, os.SEEK_END)
                stream.truncate()
            analyse, erreur = module._AnalyserDumpSQL(truncated_path)
            _assert(analyse is None and erreur, "un dump manifesté tronqué a été accepté")
            print("OK: troncature manifestée refusée")

            # 4. Import partiel : des objets existent mais le marqueur terminal est absent.
            _create_database(conn, db_partial)
            partial_path = os.path.join(tempdir, "partial.sql")
            with open(partial_path, "w", encoding="utf-8", newline="\n") as stream:
                stream.write("CREATE TABLE `a` (`id` INT);\nCREATE TABLE `b` (`id` INT);\n")
            analyse, erreur = module._AnalyserDumpSQL(partial_path)
            _assert(erreur is None, "fixture partielle invalide: %s" % erreur)
            marqueur = {"table": "__noethys_restore_%s" % uuid.uuid4().hex, "jeton": uuid.uuid4().hex}
            proc = _run_mysql(args.host, args.port, args.user, args.password,
                              "CREATE TABLE `a` (`id` INT);", db_partial)
            _assert(proc.returncode == 0, "préparation import partiel impossible")
            ok, diagnostic = module._VerifierPostconditionRestaurationMySQL(conn, db_partial, marqueur, analyse["objets"])
            _assert(not ok and "marqueur terminal" in diagnostic, "l'import partiel n'a pas été détecté: %s" % diagnostic)
            print("OK: import partiel détecté malgré la présence d'une table")

        print("QUALIFICATION NOE-032c MYSQL: SUCCÈS")
        return 0
    finally:
        for database in (db_manifest, db_legacy, db_partial):
            _drop_database(conn, database)


if __name__ == "__main__":
    raise SystemExit(main())
