#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rassemble les inventaires statiques à relire avant de figer une RC.

Ce script ne modifie ni le code ni les bases. Il regroupe en une commande les
inventaires SQL strict, cycle de vie wxPython, anciens outils de listes et les
signatures de défauts transverses apprises dans Teamworks.

Avant tout inventaire, il impose le contrat global de couverture des sources :
tout ``noethys/**/*.py`` doit être trouvé, lu selon son encodage Python et
parsable. Les occurrences restent ensuite des diagnostics à qualifier. Les
signatures Teamworks conservent en plus leur propre mesure de couverture sur
leur périmètre applicatif afin qu'un zéro ne puisse jamais masquer un fichier
non analysé.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import audit_legacy_list_tools  # noqa: E402
from scripts import audit_source_coverage  # noqa: E402
from scripts import audit_sql_strict  # noqa: E402
from scripts import audit_teamworks_signatures  # noqa: E402
from scripts import audit_wx_lifecycle  # noqa: E402

DEFAULT_ROOT = ROOT / "noethys"
DEFAULT_OUTPUT = ROOT / "tmp" / "pre-rc-audits"
WX_HIGH_RISK = (
    "constructor_parent_callback",
    "constructor_callback_before_dependency",
    "use_after_destroy",
)


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _display_path(path: Path) -> str:
    return _relative(path, ROOT)


def _serialise_sql(item) -> dict:
    return {
        "classification": item.classification,
        "risk": item.risk,
        "path": _display_path(item.path),
        "line": item.line,
        "reason": item.reason,
        "ungrouped_items": list(item.ungrouped_items),
        "summary": item.summary(),
    }


def _normalise_legacy_findings(findings: list[dict]) -> list[dict]:
    normalised = []
    for item in findings:
        current = dict(item)
        current["path"] = _display_path(Path(str(current["path"])))
        normalised.append(current)
    return normalised


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _require_source_coverage(root: Path):
    session = audit_source_coverage.SourceAuditSession(
        audit_source_coverage.iter_python_files(root)
    )
    for path in session.paths:
        session.parse(path)
    session.report(prefix="Couverture globale des sources pré-RC")
    session.require_complete()
    return session.coverage


def collect(root: Path = DEFAULT_ROOT) -> dict:
    root = root.resolve()
    coverage = _require_source_coverage(root)

    sql_candidates = audit_sql_strict.scan(root)
    sql_counts = Counter(item.classification for item in sql_candidates)
    sql_review = [
        _serialise_sql(item)
        for item in sql_candidates
        if item.classification == "REVIEW"
    ]

    wx_findings = audit_wx_lifecycle.scan()
    wx_counts = Counter(item["kind"] for item in wx_findings)
    wx_high_risk = {
        kind: wx_counts.get(kind, 0)
        for kind in WX_HIGH_RISK
    }

    legacy_findings = _normalise_legacy_findings(
        audit_legacy_list_tools.scan(root)
    )
    legacy_counts = audit_legacy_list_tools.summarize(legacy_findings)
    legacy_screens = audit_legacy_list_tools.screens(legacy_findings)

    teamworks_report = audit_teamworks_signatures.build_report(root)
    teamworks_coverage = dict(teamworks_report["coverage"])

    return {
        "summary": {
            "source_coverage": {
                "found": coverage.found,
                "read": coverage.read,
                "parsed": coverage.parsed,
                "complete": coverage.complete,
            },
            "sql": {
                "total": len(sql_candidates),
                "REVIEW": sql_counts.get("REVIEW", 0),
                "DEDUPE": sql_counts.get("DEDUPE", 0),
                "SAFE": sql_counts.get("SAFE", 0),
            },
            "wx_lifecycle": {
                "total": len(wx_findings),
                "counts": dict(sorted(wx_counts.items())),
                "high_risk": wx_high_risk,
            },
            "legacy_list_tools": {
                "screens": len(legacy_screens),
                "counts": legacy_counts,
            },
            "teamworks_signatures": {
                "total": teamworks_report["count"],
                "kinds": dict(teamworks_report["kinds"]),
                "priorities": dict(teamworks_report["priorities"]),
                "coverage": teamworks_coverage,
            },
        },
        "sql_review": sql_review,
        "wx_findings": wx_findings,
        "legacy_findings": legacy_findings,
        "legacy_screens": legacy_screens,
        "teamworks_findings": list(teamworks_report["findings"]),
    }


def write_reports(data: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "pre-rc-summary.json", data["summary"])
    _write_json(
        output_dir / "sql-strict-review.json",
        {
            "summary": data["summary"]["sql"],
            "findings": data["sql_review"],
        },
    )
    _write_json(
        output_dir / "wx-lifecycle-audit.json",
        {
            "summary": data["summary"]["wx_lifecycle"],
            "findings": data["wx_findings"],
        },
    )
    _write_json(
        output_dir / "legacy-list-tools-audit.json",
        {
            "summary": data["summary"]["legacy_list_tools"],
            "screens": data["legacy_screens"],
            "findings": data["legacy_findings"],
        },
    )
    _write_json(
        output_dir / "teamworks-signatures-audit.json",
        {
            "summary": data["summary"]["teamworks_signatures"],
            "findings": data["teamworks_findings"],
        },
    )


def print_summary(data: dict, output_dir: Path) -> None:
    summary = data["summary"]
    coverage = summary["source_coverage"]
    sql = summary["sql"]
    wx = summary["wx_lifecycle"]
    legacy = summary["legacy_list_tools"]
    teamworks = summary["teamworks_signatures"]
    teamworks_coverage = teamworks["coverage"]

    print("Inventaires statiques pré-RC")
    print("===========================")
    print(
        "Sources     : {found} trouvés = {read} lus = {parsed} parsés".format(
            **coverage
        )
    )
    print(
        "SQL strict : {total} candidats — REVIEW={REVIEW}, DEDUPE={DEDUPE}, SAFE={SAFE}".format(
            **sql
        )
    )
    print("wxPython    : %d occurrences" % wx["total"])
    for kind in WX_HIGH_RISK:
        print("  %-40s %d" % (kind + ":", wx["high_risk"].get(kind, 0)))
    print(
        "Listes      : %d écran(s) métier encore raccordé(s) aux outils historiques"
        % legacy["screens"]
    )
    print(
        "Teamworks   : %d signature(s) — couverture %d/%d/%d — %s"
        % (
            teamworks["total"],
            teamworks_coverage["found"],
            teamworks_coverage["read"],
            teamworks_coverage["parsed"],
            "OK" if teamworks_coverage["complete"] else "ECHEC",
        )
    )
    print("Rapports    : %s" % output_dir)
    print("")
    print("Ces nombres sont des inventaires. Corriger uniquement après revue du risque concret.")


def run(root: Path = DEFAULT_ROOT, output_dir: Path = DEFAULT_OUTPUT) -> dict:
    data = collect(root)
    write_reports(data, output_dir)
    print_summary(data, output_dir)
    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regroupe les inventaires SQL/wx/listes/signatures Teamworks à relire avant une RC"
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    data = run(args.root, args.output_dir)
    if not data["summary"]["teamworks_signatures"]["coverage"]["complete"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
