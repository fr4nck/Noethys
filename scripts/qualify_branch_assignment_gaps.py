#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Expose la file de revue des candidats ``branch_assignment_gap``.

Le scanner de base réduit déjà les faux positifs qui peuvent être prouvés par le
contrôle de flot : branches exhaustives, chemins terminants, ``try/finally``,
``with`` et portées de compréhension Python 3.

Cette seconde étape ne baisse volontairement aucune priorité par heuristique.
Une occurrence ne peut sortir de ``high/review`` que via une qualification
explicite, étroite et documentée dans ``EXPLICIT_SAFE``. La clé ne contient pas
de numéro de ligne afin de résister aux déplacements de code, mais elle doit
correspondre à exactement un candidat brut ; une entrée absente ou ambiguë est
signalée et couverte par les tests du dépôt.
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


# Qualifications humaines explicites. Elles ne constituent pas une heuristique :
# chaque entrée doit être justifiée par un invariant de contrôle de flot précis
# et rester unique dans l'inventaire brut.
EXPLICIT_SAFE = {
    (
        "Dlg/DLG_Saisie_portail_demande.py",
        "MAJ_informations",
        "dict_periodes",
        "body_only",
    ): (
        "la lecture n'est atteinte qu'en itérant des paiements de type période ; "
        "ce même ensemble non vide initialise dict_periodes juste avant"
    ),
    (
        "Dlg/DLG_Saisie_portail_demande.py",
        "MAJ_informations",
        "dict_factures",
        "body_only",
    ): (
        "la lecture n'est atteinte qu'en itérant des paiements de type facture ; "
        "ce même ensemble non vide initialise dict_factures juste avant"
    ),
    (
        "Dlg/DLG_Saisie_portail_demande.py",
        "Traitement_recus",
        "reponse",
        "body_only",
    ): (
        "les chemins continuants sont couverts par methode_envoi != 'email' ou "
        "methode_envoi == 'email' ; chacun définit reponse avant le retour"
    ),
    (
        "Dlg/DLG_Saisie_portail_demande.py",
        "Traitement_factures",
        "reponse",
        "body_only",
    ): (
        "les chemins continuants sont couverts par methode_envoi != 'email' ou "
        "methode_envoi == 'email' ; chacun définit reponse avant le retour"
    ),
}


def qualification_key(item):
    return (item["file"], item["function"], item["name"], item["detail"])


def build_report(root=ROOT):
    raw = base.build_report(root)
    key_counts = Counter(qualification_key(item) for item in raw["findings"])
    matched = set()
    findings = []

    for item in raw["findings"]:
        result = dict(item)
        key = qualification_key(item)
        reason = EXPLICIT_SAFE.get(key)
        if reason is not None and key_counts[key] == 1:
            result["classification"] = "explicit_safe"
            result["priority"] = "low"
            result["reason"] = reason
            matched.add(key)
        else:
            result["classification"] = "review"
            result["priority"] = "high"
            result["reason"] = (
                "candidat conservé : aucune heuristique ne masque automatiquement "
                "un risque de variable locale absente"
            )
        findings.append(result)

    unmatched = sorted(key for key in EXPLICIT_SAFE if key_counts[key] == 0)
    ambiguous = sorted(key for key in EXPLICIT_SAFE if key_counts[key] > 1)

    findings.sort(key=lambda item: (item["file"], item["line"], item["name"]))
    return {
        "count": len(findings),
        "priorities": dict(Counter(item["priority"] for item in findings)),
        "classifications": dict(Counter(item["classification"] for item in findings)),
        "explicit_safe_registry": {
            "configured": len(EXPLICIT_SAFE),
            "matched": len(matched),
            "unmatched": [list(key) for key in unmatched],
            "ambiguous": [list(key) for key in ambiguous],
        },
        "findings": findings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default="", metavar="FILE")
    args = parser.parse_args(argv)

    report = build_report()
    print(f"BRANCH_ASSIGNMENT_QUALIFIED={report['count']} {report['priorities']} {report['classifications']}")
    for item in report["findings"]:
        label = "SAFE" if item["classification"] == "explicit_safe" else "REVIEW"
        print(f"- {label} {item['file']}:{item['line']} {item['function']} — {item['name']} ({item['detail']})")

    registry = report["explicit_safe_registry"]
    if registry["unmatched"] or registry["ambiguous"]:
        print(
            "QUALIFICATION_REGISTRY_ERROR="
            f"unmatched={len(registry['unmatched'])} ambiguous={len(registry['ambiguous'])}"
        )

    if args.json:
        output = Path(args.json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return 2 if registry["unmatched"] or registry["ambiguous"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
