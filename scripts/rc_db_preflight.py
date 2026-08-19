#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Préflight RC unifié sur une copie de base Noethys.

Ce script regroupe les validations encore nécessaires avant la RC :

- Noe-002 : exécution en lecture seule de la requête OL_Reglements réécrite,
  avec contrôle de sa forme à 26 colonnes ;
- Noe-003 : diagnostic non nominatif des cotisations partageant une prestation ;
- Noe-004 : inventaire, EXPLAIN et chronométrages des candidats d'index ;
- Noe-030 : structure, volumes, agrégats et empreinte de schéma.

Aucune migration et aucune écriture métier ne sont exécutées. Pour SQLite la
copie est ouverte en ``mode=ro`` ; pour MySQL/MariaDB, un compte SQL limité à
SELECT reste recommandé pour ajouter une garantie côté serveur.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

OL_REGLEMENTS_PROBE = """
SELECT
    reglements.IDreglement, reglements.IDcompte_payeur, reglements.date,
    reglements.IDmode, modes_reglements.label,
    reglements.IDemetteur, emetteurs.nom,
    reglements.numero_piece, reglements.montant,
    payeurs.IDpayeur, payeurs.nom,
    reglements.observations, numero_quittancier, IDprestation_frais,
    reglements.IDcompte, date_differe, encaissement_attente,
    reglements.IDdepot, depots.date, depots.nom, depots.verrouillage,
    date_saisie, IDutilisateur,
    ventilation_totaux.total_ventilation,
    reglements.IDprelevement,
    comptes_payeurs.IDfamille
FROM reglements
LEFT JOIN (
    SELECT IDreglement, SUM(montant) AS total_ventilation
    FROM ventilation
    GROUP BY IDreglement
) ventilation_totaux ON reglements.IDreglement = ventilation_totaux.IDreglement
LEFT JOIN modes_reglements ON reglements.IDmode = modes_reglements.IDmode
LEFT JOIN emetteurs ON reglements.IDemetteur = emetteurs.IDemetteur
LEFT JOIN payeurs ON reglements.IDpayeur = payeurs.IDpayeur
LEFT JOIN depots ON reglements.IDdepot = depots.IDdepot
LEFT JOIN comptes_payeurs
    ON comptes_payeurs.IDcompte_payeur = reglements.IDcompte_payeur
LIMIT 25
""".strip()


def run_tool(arguments: list[str], stdout_path: Path) -> None:
    command = [sys.executable] + arguments
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        env=os.environ.copy(),
    )
    stdout_path.write_text(completed.stdout or "", encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(
            "%s a échoué (code %d). Voir %s"
            % (Path(arguments[0]).name, completed.returncode, stdout_path)
        )


def sqlite_ol_reglements_probe(path: Path) -> dict:
    uri_path = quote(path.resolve().as_posix(), safe="/:")
    connection = sqlite3.connect("file:%s?mode=ro" % uri_path, uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        cursor = connection.execute(OL_REGLEMENTS_PROBE)
        rows = cursor.fetchall()
        columns = len(cursor.description or ())
    finally:
        connection.close()
    return {
        "status": "pass" if columns == 26 else "review",
        "columns": columns,
        "sample_rows": len(rows),
        "expected_columns": 26,
    }


def mysql_ol_reglements_probe(host: str, port: int, database: str, user: str, password: str) -> dict:
    try:
        import mysql.connector  # type: ignore
    except ImportError as exc:
        raise RuntimeError("mysql-connector-python est requis pour MySQL/MariaDB") from exc

    connection = mysql.connector.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        autocommit=False,
        connection_timeout=10,
    )
    cursor = connection.cursor()
    try:
        cursor.execute(OL_REGLEMENTS_PROBE)
        rows = cursor.fetchall()
        columns = len(cursor.description or ())
        connection.rollback()
    finally:
        cursor.close()
        connection.close()
    return {
        "status": "pass" if columns == 26 else "review",
        "columns": columns,
        "sample_rows": len(rows),
        "expected_columns": 26,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--sqlite", type=Path, help="copie SQLite .dat")
    source.add_argument("--mysql-host", help="hôte MySQL/MariaDB de la copie de recette")
    parser.add_argument("--mysql-port", type=int, default=3306)
    parser.add_argument("--mysql-database")
    parser.add_argument("--mysql-user")
    parser.add_argument("--mysql-password-env", default="NOETHYS_DB_PASSWORD")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("tmp/rc-db-preflight"),
        help="répertoire de rapports (défaut: tmp/rc-db-preflight)",
    )
    return parser.parse_args()


def build_source_args(args: argparse.Namespace) -> list[str]:
    if args.sqlite:
        return ["--sqlite", str(args.sqlite.resolve())]
    if not args.mysql_database or not args.mysql_user:
        raise RuntimeError("--mysql-database et --mysql-user sont requis avec --mysql-host")
    return [
        "--mysql-host", args.mysql_host,
        "--mysql-port", str(args.mysql_port),
        "--mysql-database", args.mysql_database,
        "--mysql-user", args.mysql_user,
        "--mysql-password-env", args.mysql_password_env,
    ]


def main() -> int:
    args = parse_args()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)

    source_args = build_source_args(args)
    recette_json = output / "noe030-recette.json"
    index_json = output / "noe004-indexes.json"
    recette_log = output / "noe030-recette.txt"
    index_log = output / "noe004-indexes.txt"

    try:
        run_tool(
            [str(SCRIPTS / "recette_existing_db_readonly.py")]
            + source_args
            + ["--json", str(recette_json)],
            recette_log,
        )
        run_tool(
            [str(SCRIPTS / "audit_db_indexes.py")]
            + source_args
            + ["--repeats", str(args.repeats), "--json", str(index_json)],
            index_log,
        )

        if args.sqlite:
            noe002 = sqlite_ol_reglements_probe(args.sqlite)
        else:
            password = os.environ.get(args.mysql_password_env)
            if password is None:
                raise RuntimeError("Variable %s absente" % args.mysql_password_env)
            noe002 = mysql_ol_reglements_probe(
                args.mysql_host,
                args.mysql_port,
                args.mysql_database,
                args.mysql_user,
                password,
            )

        recette = json.loads(recette_json.read_text(encoding="utf-8"))
        indexes = json.loads(index_json.read_text(encoding="utf-8"))

        anomalies = recette.get("business_anomalies") or {}
        shared = int(anomalies.get("cotisations_shared_prestation_count", 0) or 0)
        source = recette.get("source") or {}
        missing_core = recette.get("missing_core_tables") or []

        database_index = indexes.get("database") or {}
        candidates = database_index.get("candidates") or []
        measurements = database_index.get("measurements") or []
        covered = sum(1 for item in candidates if item.get("covered"))

        checks = {
            "noe002_ol_reglements": noe002,
            "noe003_cotisation_invariant": {
                "status": "pass" if shared == 0 else "review",
                "shared_prestation_count": shared,
            },
            "noe004_index_audit": {
                "status": "pass",
                "candidate_count": len(candidates),
                "covered_candidates": covered,
                "measured_candidates": len(measurements),
                "note": "absence d'index = mesure à examiner, pas échec automatique",
            },
            "noe030_existing_db": {
                "status": "pass" if not missing_core else "review",
                "schema_digest": recette.get("schema_digest"),
                "missing_core_tables": missing_core,
                "sqlite_unchanged": source.get("unchanged_during_audit"),
            },
        }

        overall = "PASS"
        if any(item.get("status") != "pass" for item in checks.values()):
            overall = "REVIEW"

        summary = {
            "format": 1,
            "overall": overall,
            "checks": checks,
            "reports": {
                "recette_json": str(recette_json),
                "recette_log": str(recette_log),
                "indexes_json": str(index_json),
                "indexes_log": str(index_log),
            },
        }
        summary_json = output / "RC-PREFLIGHT-SUMMARY.json"
        summary_json.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )

        lines = [
            "Noethys — préflight base avant RC",
            "=================================",
            "Résultat global : %s" % overall,
            "",
            "Noe-002 OL_Reglements : %s — %d colonnes, %d ligne(s) échantillon"
            % (noe002["status"].upper(), noe002["columns"], noe002["sample_rows"]),
            "Noe-003 cotisations : %s — %d prestation(s) partagée(s)"
            % (checks["noe003_cotisation_invariant"]["status"].upper(), shared),
            "Noe-004 index : PASS — %d/%d candidat(s) déjà couvert(s), %d mesuré(s)"
            % (covered, len(candidates), len(measurements)),
            "Noe-030 base existante : %s — schéma %s"
            % (checks["noe030_existing_db"]["status"].upper(), recette.get("schema_digest")),
        ]
        if args.sqlite:
            lines.append(
                "Copie SQLite inchangée pendant l'audit : %s"
                % ("OUI" if source.get("unchanged_during_audit") else "NON")
            )
        if shared:
            lines.extend(
                [
                    "",
                    "ACTION : des cotisations partagent une prestation ; analyser avant RC.",
                ]
            )
        lines.extend(
            [
                "",
                "Aucune migration ni écriture métier n'a été exécutée par ce préflight.",
                "Rapport détaillé : %s" % summary_json,
            ]
        )
        summary_txt = output / "RC-PREFLIGHT-SUMMARY.txt"
        summary_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return 0 if overall == "PASS" else 2

    except Exception as exc:
        error_path = output / "RC-PREFLIGHT-ERROR.txt"
        error_path.write_text("%s: %s\n" % (type(exc).__name__, exc), encoding="utf-8")
        print("ERREUR PRE-FLIGHT: %s" % exc, file=sys.stderr)
        print("Détail: %s" % error_path, file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
