"""Lance la ligne Qt Activités sans importer wx/GestionDB.

Le pont lit la configuration Noethys historique, ouvre SQLite ou MySQL avec
les pilotes Python modernes puis présente la liste et les pages Qt déjà
migrées de la fiche activité.
"""

from __future__ import annotations

import base64
import configparser
import datetime as dt
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Sequence

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QStyle, QToolBar

from .activities_prototype import (
    ActivitiesWindow,
    ActivityRepository,
    ActivityRow,
    _parse_args,
)
from .activity_visuals import apply_activity_visuals


ROOT = Path(__file__).resolve().parents[1]
NOETHYS_DIR = ROOT / "noethys"


def _user_config_dir() -> Path:
    portable = NOETHYS_DIR / "Portable"
    if portable.is_dir():
        return portable
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("Variable APPDATA introuvable : impossible de localiser Config.json.")
    return Path(appdata) / "noethys"


def _load_config() -> dict:
    path = _user_config_dir() / "Config.json"
    if not path.is_file():
        raise RuntimeError(f"Configuration Noethys introuvable : {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Impossible de lire {path} : {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"Configuration Noethys invalide : {path}")
    return data


def _custom_data_dir() -> Path | None:
    path = _user_config_dir() / "Customize.ini"
    if not path.is_file():
        return None
    parser = configparser.ConfigParser()
    try:
        parser.read(path, encoding="utf-8")
        value = parser.get("repertoire_donnees", "chemin", fallback="").strip()
    except Exception:
        return None
    if value and Path(value).is_dir():
        return Path(value)
    return None


def _data_database_name(name: str) -> str:
    """Reproduit le suffixe ``DATA`` ajouté par ``GestionDB.DB()``."""
    normalized = name.strip()
    if normalized.lower().endswith("_data"):
        return normalized
    return f"{normalized}_DATA"


def _local_database_path(name: str) -> Path:
    filename = f"{_data_database_name(name)}.dat"
    portable_data = NOETHYS_DIR / "Portable" / "Data" / filename
    if portable_data.is_file():
        return portable_data

    custom = _custom_data_dir()
    if custom is not None:
        candidate = custom / filename
        if candidate.is_file():
            return candidate

    program_data = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "noethys" / filename
    if program_data.is_file():
        return program_data

    raise RuntimeError(
        "Base locale Noethys introuvable. Chemins testés :\n"
        f"- {portable_data}\n"
        f"- {custom / filename if custom else '(aucun répertoire personnalisé)'}\n"
        f"- {program_data}"
    )


def _decode_network_password(password: str) -> str:
    """Reproduit DecodeMdpReseau sans importer GestionDB/wx."""
    if not password.startswith("#64#"):
        return password
    try:
        return base64.b64decode(password[4:]).decode("utf-8")
    except Exception as exc:
        raise RuntimeError("Le mot de passe réseau enregistré par Noethys est illisible.") from exc


def _query(only_open: bool, placeholder: str) -> tuple[str, tuple[object, ...]]:
    sql = "SELECT IDactivite, nom, abrege, date_debut, date_fin FROM activites"
    params: tuple[object, ...] = ()
    if only_open:
        sql += f" WHERE date_fin >= {placeholder}"
        params = (dt.date.today().isoformat(),)
    sql += " ORDER BY date_fin, nom"
    return sql, params


class NativeConfiguredActivityRepository(ActivityRepository):
    """Lecture de la base configurée, sans importer le runtime wx."""

    def fetch(self, only_open: bool = False) -> list[ActivityRow]:
        config = _load_config()
        name = str(config.get("nomFichier") or "").strip()
        if not name:
            raise RuntimeError("Config.json ne contient aucun 'nomFichier' actif.")

        if "[RESEAU]" in name:
            rows = self._fetch_mysql(name, only_open)
        else:
            rows = self._fetch_sqlite(name, only_open)
        return [ActivityRow.from_db_row(row) for row in rows]

    def _fetch_sqlite(self, name: str, only_open: bool) -> Sequence[Sequence[object]]:
        database = _local_database_path(name)
        sql, params = _query(only_open, "?")
        with sqlite3.connect(database) as connection:
            return connection.execute(sql, params).fetchall()

    def _fetch_mysql(self, descriptor: str, only_open: bool) -> Sequence[Sequence[object]]:
        try:
            import mysql.connector
        except ImportError as exc:
            raise RuntimeError(
                "mysql-connector-python manque dans l'environnement Qt. "
                "Relancez : .\\.venv\\Scripts\\python.exe -m pip install -r requirements-qt.txt"
            ) from exc

        before, database = descriptor.split("[RESEAU]", 1)
        try:
            port, host, user, encoded_password = before.split(";", 3)
        except ValueError as exc:
            raise RuntimeError("Descripteur réseau Noethys invalide dans Config.json.") from exc

        sql, params = _query(only_open, "%s")
        connect_params = {
            "host": host,
            "port": int(port),
            "user": user,
            "password": _decode_network_password(encoded_password),
            "database": _data_database_name(database).lower(),
            "use_unicode": True,
        }
        ca_path = _user_config_dir() / "ca-cert.pem"
        if ca_path.is_file():
            connect_params["ssl_ca"] = str(ca_path)

        connection = mysql.connector.connect(**connect_params)
        try:
            cursor = connection.cursor()
            try:
                cursor.execute(sql, params)
                return cursor.fetchall()
            finally:
                cursor.close()
        finally:
            connection.close()


class NativeActivitiesWindow(ActivitiesWindow):
    """Liste Qt enrichie des pages déjà migrées de la fiche activité."""

    def __init__(
        self,
        repository: ActivityRepository,
        *,
        editor_sqlite_path: Path | None = None,
        initial_open_only: bool = False,
        requested_theme: str | None = None,
    ):
        self.editor_sqlite_path = editor_sqlite_path
        super().__init__(
            repository,
            initial_open_only=initial_open_only,
            requested_theme=requested_theme,
        )

        self.modify_action = self.deferred_actions[1]
        self.modify_action.setEnabled(False)
        self.modify_action.setToolTip("Modifier l'activité sélectionnée")
        self.modify_action.setIcon(
            self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        )
        self.modify_action.triggered.connect(self._edit_selected)

        toolbar = self.findChild(QToolBar)
        if toolbar is not None:
            toolbar.insertAction(self.export_text_action, self.modify_action)
            toolbar.insertSeparator(self.export_text_action)

        selection_model = self.table.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(self._sync_modify_action)
        self.table.doubleClicked.connect(self._edit_selected)
        self._sync_modify_action()

    def _selected_activity_id(self) -> int | None:
        index = self.table.currentIndex()
        if not index.isValid():
            return None
        source_index = self.proxy.mapToSource(index)
        if not source_index.isValid():
            return None
        return self.model.row_at(source_index.row()).activity_id

    def _sync_modify_action(self, *_args) -> None:
        self.modify_action.setEnabled(self._selected_activity_id() is not None)

    def _edit_selected(self, *_args) -> None:
        activity_id = self._selected_activity_id()
        if activity_id is None:
            return

        try:
            from .activity_editor import NativeActivityEditorRepository
            from .activity_units import ActivityEditorDialog

            editor_repository = NativeActivityEditorRepository(self.editor_sqlite_path)
            dialog = ActivityEditorDialog(editor_repository, activity_id, self)
        except Exception as exc:
            QMessageBox.critical(self, "Modification impossible", str(exc))
            return

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.reload()
            self._sync_modify_action()


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    app = QApplication(sys.argv[:1])
    app.setApplicationName("Noethys Qt — Activités")
    app.setOrganizationName("Noethys")

    if args.sqlite:
        from .activities_prototype import SqliteActivityRepository

        repository: ActivityRepository = SqliteActivityRepository(args.sqlite)
    else:
        repository = NativeConfiguredActivityRepository()

    window = NativeActivitiesWindow(
        repository,
        editor_sqlite_path=args.sqlite,
        initial_open_only=args.open_only,
        requested_theme=args.theme,
    )
    apply_activity_visuals(window)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
