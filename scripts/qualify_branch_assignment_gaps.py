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
import ast
import hashlib
import json
import tokenize
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
    ('Dlg/DLG_Saisie_portail_demande.py', 'MAJ_informations', 'dict_periodes', 'body_only', '0343a39678fbf0f9bf748fec2787518bfd7b996f259d2e928f4066c1880bb363'): (
        "la lecture n'est atteinte qu'en itérant des paiements de type période ; ce même ensemble non vide initialise dict_periodes juste avant"
    ),
    ('Dlg/DLG_Saisie_portail_demande.py', 'MAJ_informations', 'dict_factures', 'body_only', '661e61d415ec7daa109e89d5e9c5eca87e624e3b09fa3f1eae7f51ee5bb27372'): (
        "la lecture n'est atteinte qu'en itérant des paiements de type facture ; ce même ensemble non vide initialise dict_factures juste avant"
    ),
    ('Dlg/DLG_Saisie_portail_demande.py', 'Traitement_recus', 'reponse', 'body_only', '7bf64ac505cc641391cd756a60032158c26c9b976868e45a9c95574c2c33b321'): (
        "les chemins continuants sont couverts par methode_envoi != 'email' ou methode_envoi == 'email' ; chacun définit reponse avant le retour"
    ),
    ('Dlg/DLG_Saisie_portail_demande.py', 'Traitement_factures', 'reponse', 'body_only', '84ef787a336bf91244a97181fa077d299621266533e4532f3e7fe73694d90398'): (
        "les chemins continuants sont couverts par methode_envoi != 'email' ou methode_envoi == 'email' ; chacun définit reponse avant le retour"
    ),
}

def _candidate_fingerprint(root, item):
    """Empreinte la structure AST qui justifie une qualification explicite.

    Les numéros de ligne servent uniquement à retrouver les nœuds signalés par
    le scanner. Ils ne participent pas à l'empreinte : un déplacement de code
    reste donc stable, tandis qu'une modification du branchement ou de la
    lecture rend automatiquement l'entrée de registre obsolète.
    """
    path = Path(root) / item["file"]
    try:
        with tokenize.open(path) as stream:
            tree = ast.parse(stream.read(), filename=str(path))
    except (OSError, SyntaxError, UnicodeError):
        return None

    functions = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == item["function"]
    ]
    for function in functions:
        if_node = next((
            node for node in ast.walk(function)
            if isinstance(node, ast.If)
            and getattr(node, "lineno", None) == item["if_line"]
        ), None)
        if if_node is None:
            continue

        candidates = []
        for node in ast.walk(function):
            if not isinstance(node, ast.stmt):
                continue
            found = any(
                isinstance(child, ast.Name)
                and child.id == item["name"]
                and getattr(child, "lineno", None) == item["line"]
                and isinstance(child.ctx, (ast.Load, ast.Del))
                for child in ast.walk(node)
            )
            if found:
                start = getattr(node, "lineno", item["line"])
                end = getattr(node, "end_lineno", start)
                candidates.append((end - start, len(list(ast.walk(node))), node))
        if not candidates:
            continue

        event_node = min(candidates, key=lambda entry: (entry[0], entry[1]))[2]
        payload = "|".join((
            item["function"],
            item["name"],
            item["detail"],
            ast.dump(if_node, include_attributes=False),
            ast.dump(event_node, include_attributes=False),
        ))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return None


def qualification_key(item, root=ROOT):
    return (
        item["file"],
        item["function"],
        item["name"],
        item["detail"],
        _candidate_fingerprint(root, item),
    )


def build_report(root=ROOT):
    raw = base.build_report(root)
    key_counts = Counter(qualification_key(item, root) for item in raw["findings"])
    matched = set()
    findings = []

    for item in raw["findings"]:
        result = dict(item)
        key = qualification_key(item, root)
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
