#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Export/import a Noethys user configuration as one JSON profile.

This utility is intentionally data-free: it handles Config.json and
Customize.ini only. Databases, logs, photos and temporary files are excluded.
The profile may nevertheless contain network connection information and must be
treated as sensitive.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path
import shutil
import sys

FORMAT = "noethys-configuration-profile"
VERSION = 1


def _load_json(path: Path):
    with path.open("r", encoding="utf-8-sig") as stream:
        return json.load(stream)


def export_profile(config_dir: Path, output: Path) -> None:
    config_path = config_dir / "Config.json"
    customize_path = config_dir / "Customize.ini"

    if not config_path.is_file():
        raise SystemExit("Config.json introuvable dans %s" % config_dir)

    config = _load_json(config_path)
    if not isinstance(config, dict):
        raise SystemExit("Config.json invalide : dictionnaire JSON attendu")

    customize = None
    if customize_path.is_file():
        customize = customize_path.read_text(encoding="utf-8-sig", errors="replace")

    payload = {
        "format": FORMAT,
        "version": VERSION,
        "created_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "sensitive": True,
        "warning": "Ce fichier peut contenir des paramètres de connexion réseau. Ne pas le publier.",
        "files": {
            "Config.json": config,
            "Customize.ini": customize,
        },
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("Configuration exportée : %s" % output)
    print("ATTENTION : ce fichier est sensible et ne doit pas être publié sur GitHub.")


def _backup(path: Path, stamp: str) -> None:
    if path.is_file():
        backup = path.with_name("%s.before-import-%s%s" % (path.stem, stamp, path.suffix))
        shutil.copy2(path, backup)
        print("Sauvegarde créée : %s" % backup)


def import_profile(profile: Path, config_dir: Path) -> None:
    payload = _load_json(profile)
    if not isinstance(payload, dict):
        raise SystemExit("Profil invalide : objet JSON attendu")
    if payload.get("format") != FORMAT or payload.get("version") != VERSION:
        raise SystemExit("Profil Noethys non reconnu ou version non supportée")

    files = payload.get("files")
    if not isinstance(files, dict):
        raise SystemExit("Profil invalide : section files absente")

    config = files.get("Config.json")
    if not isinstance(config, dict):
        raise SystemExit("Profil invalide : Config.json absent ou invalide")

    customize = files.get("Customize.ini")
    if customize is not None and not isinstance(customize, str):
        raise SystemExit("Profil invalide : Customize.ini doit être du texte ou null")

    config_dir.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    config_path = config_dir / "Config.json"
    customize_path = config_dir / "Customize.ini"

    _backup(config_path, stamp)
    _backup(customize_path, stamp)

    config_path.write_text(
        json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if customize is None:
        print("Customize.ini absent du profil : fichier local conservé s'il existe.")
    else:
        customize_path.write_text(customize, encoding="utf-8")

    print("Configuration importée dans : %s" % config_dir)
    print("Relancez Noethys pour appliquer complètement le profil.")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_export = sub.add_parser("export")
    p_export.add_argument("--config-dir", required=True, type=Path)
    p_export.add_argument("--output", required=True, type=Path)

    p_import = sub.add_parser("import")
    p_import.add_argument("--config-dir", required=True, type=Path)
    p_import.add_argument("--profile", required=True, type=Path)

    args = parser.parse_args(argv)
    if args.command == "export":
        export_profile(args.config_dir.resolve(), args.output.resolve())
    else:
        import_profile(args.profile.resolve(), args.config_dir.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
