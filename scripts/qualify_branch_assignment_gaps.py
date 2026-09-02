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
correspondre à exactement un candidat brut et à l’empreinte AST complète de
la fonction qui porte son invariant ; une entrée absente, modifiée ou ambiguë est
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
    ('Dlg/DLG_Saisie_portail_demande.py', 'MAJ_informations', 'dict_periodes', 'body_only', '4779e9182f1002ee9ab536bdb9303391e030d4d4c723a43ff3b9c4ed973090f9'): (
        "la lecture n'est atteinte qu'en itérant des paiements de type période ; ce même ensemble non vide initialise dict_periodes juste avant"
    ),
    ('Dlg/DLG_Saisie_portail_demande.py', 'MAJ_informations', 'dict_factures', 'body_only', '914b011143627234ee14abea5738586b025fa49093f2b5f01cf45ace88ab46fc'): (
        "la lecture n'est atteinte qu'en itérant des paiements de type facture ; ce même ensemble non vide initialise dict_factures juste avant"
    ),
    ('Dlg/DLG_Saisie_portail_demande.py', 'Traitement_recus', 'reponse', 'body_only', '1a357b505a94693ac30e93cca69189fae6a478a1adc9b1139b6e46a5f2ba2ab0'): (
        "les chemins continuants sont couverts par methode_envoi != 'email' ou methode_envoi == 'email' ; chacun définit reponse avant le retour"
    ),
    ('Dlg/DLG_Saisie_portail_demande.py', 'Traitement_factures', 'reponse', 'body_only', '4d35390aa5af82e149c8e869939032d3ffefaf86b1598f61f7a3d743bdc983e0'): (
        "les chemins continuants sont couverts par methode_envoi != 'email' ou methode_envoi == 'email' ; chacun définit reponse avant le retour"
    ),
    ('Dlg/DLG_Ouvertures.py', 'Sauvegarde', 'prochainIDligne', 'body_only', 'be2a517abf7c8b4245b285e27a22a3a5d5022c13421bd3d4ff842cffd8bc5ae2'): (
        "prochainIDligne est initialisé lorsque DB.isNetwork est faux et sa lecture pour attribuer un IDligne est protégée par le même garde ; en mode réseau cette lecture n'est jamais atteinte"
    ),
    ('Dlg/DLG_Ouvertures.py', 'TraitementLot', 'etat', 'partial_branches', 'c0d13e7cc9b6a33b2c3404ce03b99235d6b8e8b2dbc577b51e653dcddc1551f9'): (
        "le bloc extérieur limite action à date, schema ou reinit ; date/schema affectent etat ou passent par l'except qui le replie à False, tandis que reinit passe par le else qui l'affecte aussi"
    ),
    ('Dlg/DLG_Ouvertures.py', 'TraitementLot', 'liste_temp', 'body_only', 'c0913bd34f86edcdd512abb5180f11a4d5277f0efe0c600d39cd3eba485fa64c'): (
        "la boucle sur liste_temp n'est atteinte que sous action date/schema ; chacun de ces deux chemins l'affecte dans le try et toute erreur quitte directement ce try vers l'except sans exécuter la boucle"
    ),
    ('Dlg/DLG_Ouvertures.py', 'TraitementLot', 'nbrePlaces', 'partial_branches', 'c3c4355421b4b54d0daa627449f414c23ad2d33240c8ae5e1c2c7957976a2fe9'): (
        "le bloc extérieur limite action à date, schema ou reinit ; date/schema affectent nbrePlaces ou passent par l'except qui le replie à 0, tandis que reinit passe par le else qui l'affecte à 0"
    ),
    ('Utils/UTILS_Cotisations_manquantes.py', 'GetListeCotisationsManquantes', 'date_fin', 'body_only', '52833ac4673ab36cac3451e073e6f972df167f8e77634102bb530990f98fa4d0'): (
        'la lecture de date_fin est dans le bloc gardé par A or B ; chacun des deux termes vrais affecte date_fin avant son utilisation'
    ),
    ('Utils/UTILS_Cryptage_fichier.py', 'DecrypterFichier', 'dec', 'partial_branches', 'c4ec08d2c16ced4dc3e072a66f32cdd872014748db4af9851753658dd310fe3e'): (
        'le format SV2 affecte dec dans la première branche et tout autre contenu passe par le else qui affecte dec après le chargement compatible Python 2/3'
    ),
    ('Utils/UTILS_Export_nomade.py', 'Run', 'dlgAttente', 'body_only', '0c366c92222727bc372dfac57ab219a3967d2725a9dac613a0366037bfdf1803'): (
        "dlgAttente n'est créé que si afficherDlgAttente est vrai et ses deux suppressions, en succès comme en exception, sont protégées par exactement le même garde"
    ),
    ('Utils/UTILS_Icalendar.py', '__init__', 'fichier', 'body_only', '4b3769dbe504b542a423a645cca1c8f940c592643482fcfee26964d061102c06'): (
        "fichier est lu uniquement dans le try englobant ; toute absence d'affectation ou erreur d'ouverture est capturée par l'except qui replie explicitement self.cal à None"
    ),
    ('Utils/UTILS_Impression_inscription.py', '__init__', 'paraStyleIntro', 'body_only', '3ed758b70f477a71a17f646ccb62f5f44c946ffba4702e5ca1a03a18ec89d6b5'): (
        'la lecture est sous le garde intro présent/non nul, qui implique nécessairement le premier terme du garde OR ayant créé paraStyleIntro juste avant'
    ),
    ('Utils/UTILS_Html2text.py', 'handle_tag', 'tag_style', 'body_only', '92dfcabc32019e8f2e8b08967afb57e88854c05f0a37329675fe74b201dcf8ce'): (
        "tag_style n'est lu que sous options.google_doc ; dans ce même bloc start l'affecte via element_style et le else l'affecte via le pop de tag_stack"
    ),
    ('Utils/UTILS_Html2text.py', 'handle_tag', 'parent_style', 'body_only', '9cbe4485113ef2f67dad45e6ecac66f2666c8a3a05e5e0622644ddc46fa523f3'): (
        "parent_style est initialisé à un dictionnaire vide dès l'entrée dans options.google_doc et toutes ses lectures ultérieures restent sous ce même garde"
    ),
    ('Utils/UTILS_Titulaires.py', 'GetTitulaires', 'nomsTitulaires', 'body_only', 'cd35c15e3510275978436eb40410f2403477fb4306c3dfd6db9330ae75be0084'): (
        "la lecture de nomsTitulaires est sous nbreTitulaires > 0 ; les cas 1, 2 et > 2, exhaustifs pour tout entier strictement positif, l'affectent auparavant"
    ),
}

def _candidate_fingerprint(root, item):
    """Empreinte la structure AST qui justifie une qualification explicite.

    Les numéros de ligne servent uniquement à retrouver la fonction signalée par
    le scanner. Ils ne participent pas à l'empreinte. En revanche, toute évolution
    AST de cette fonction invalide la qualification, y compris un garde ou une
    boucle environnante dont dépend l'invariant humain.
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
        # Une qualification humaine peut dépendre d'un garde ou d'une boucle
        # située avant/après le ``if`` directement signalé. On empreinte donc la
        # fonction entière plutôt qu'un voisinage local : toute évolution du flot
        # qui établit l'invariant rend l'entrée explicite obsolète et la remet en
        # ``high/review`` jusqu'à nouvelle validation humaine.
        payload = "|".join((
            item["function"],
            item["name"],
            item["detail"],
            ast.dump(function, include_attributes=False),
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
