#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Expose la file de revue des candidats ``branch_assignment_gap``.

Le scanner de base réduit déjà les faux positifs qui peuvent être prouvés par le
contrôle de flot : branches exhaustives, chemins terminants, ``try/finally``,
``with`` et portées de compréhension Python 3.

Cette seconde étape ne baisse volontairement plus la priorité d'aucun candidat
sur la seule base d'une garde répétée. Prouver qu'une garde est stable exige de
raisonner sur les protocoles Python dynamiques, les alias, les fermetures, les
mutations indirectes et les back-edges de boucle. Un heuristique incomplet peut
transformer un vrai ``UnboundLocalError`` en faux négatif ; ce coût est jugé
supérieur à celui d'une revue humaine supplémentaire.

Le contrat est donc simple : tout candidat résiduel reste ``high/review`` jusqu'à
qualification humaine ou preuve spécifique couverte par un test dédié dans le
scanner de base.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

try:
    from scripts import audit_branch_assignment_gaps as base
except ModuleNotFoundError:
    import audit_branch_assignment_gaps as base

ROOT = base.NOETHYS


def build_report(root=ROOT):
    raw = base.build_report(root)
    findings = []
    for item in raw["findings"]:
        result = dict(item)
        result["classification"] = "review"
        result["priority"] = "high"
        result["reason"] = (
            "candidat conservé : aucune corrélation de garde n'est utilisée "
            "pour masquer automatiquement un risque de variable locale absente"
        )
        findings.append(result)

    findings.sort(key=lambda item: (item["file"], item["line"], item["name"]))
    return {
        "count": len(findings),
        "priorities": dict(Counter(item["priority"] for item in findings)),
        "classifications": dict(Counter(item["classification"] for item in findings)),
        "findings": findings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default="", metavar="FILE")
    args = parser.parse_args(argv)

    report = build_report()
    print(f"BRANCH_ASSIGNMENT_QUALIFIED={report['count']} {report['priorities']} {report['classifications']}")
    for item in report["findings"]:
        print(f"- REVIEW {item['file']}:{item['line']} {item['function']} — {item['name']} ({item['detail']})")

    if args.json:
        output = Path(args.json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
