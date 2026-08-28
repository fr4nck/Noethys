#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Qualifie les candidats ``branch_assignment_gap`` par corrélation de garde.

L'inventaire de base privilégie volontairement le rappel : une variable définie
uniquement dans une branche reste signalée dès qu'une lecture ultérieure est
visible. Une partie des faux positifs historiques suit toutefois un contrat
simple et sûr : la définition et la lecture sont protégées par une même garde
répétable, ou par une condition ultérieure qui implique explicitement la garde
d'origine.

Ce module ne supprime aucune occurrence. Il requalifie seulement les candidats
dont la garde corrélée est démontrable dans l'AST, dont la branche concernée
garantit réellement la définition et dont les dépendances visibles de la garde
ne sont pas modifiées sur le chemin sans affectation ni entre les deux tests.

La notion de garde répétable est volontairement stricte : seules les identités
(``is`` / ``is not``) entre noms et singletons constants, éventuellement
combinées par ``and``/``or``/``not``, sont considérées sans comportement Python
dynamique. Les lectures d'attribut, sous-scripts, comparaisons riches, appels et
truthiness d'objets restent ``high``. De même, aucune corrélation n'est abaissée
si l'un des deux tests se trouve dans une boucle : les back-edges rendent
l'ordre linéaire des lignes insuffisant pour prouver la stabilité.
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter, defaultdict
from pathlib import Path

try:
    from scripts import audit_branch_assignment_gaps as base
    from scripts.audit_source_coverage import SourceAuditSession
except ModuleNotFoundError:
    import audit_branch_assignment_gaps as base
    from audit_source_coverage import SourceAuditSession

ROOT = base.NOETHYS


def _same_expr(left, right):
    return ast.dump(left, include_attributes=False) == ast.dump(right, include_attributes=False)


def _expr_key(node):
    """Clé structurelle indépendante du contexte Load/Store de l'AST."""
    if isinstance(node, ast.Name):
        return ("name", node.id)
    if isinstance(node, ast.Attribute):
        return ("attribute", _expr_key(node.value), node.attr)
    if isinstance(node, ast.Subscript):
        return (
            "subscript",
            _expr_key(node.value),
            ast.dump(node.slice, include_attributes=False),
        )
    return ("expr", ast.dump(node, include_attributes=False))


def _negated(expr):
    return ast.UnaryOp(op=ast.Not(), operand=expr)


def _stable_identity_operand(node):
    if isinstance(node, ast.Name):
        return True
    if isinstance(node, ast.Constant) and node.value in (None, True, False):
        return True
    return False


def _guard_is_repeatable(test):
    """Vrai uniquement pour une garde sans évaluation Python dynamique.

    Même ``obj.ready``, ``state[key]``, ``left == right`` ou un simple
    ``if obj`` peuvent invoquer respectivement descriptor/property,
    ``__getitem__``, comparaison riche ou ``__bool__``. On ne peut donc pas
    prouver qu'une seconde évaluation donnera le même résultat à partir du seul
    AST. L'identité entre noms/singletons ne déclenche pas ces protocoles.
    """
    if isinstance(test, ast.Compare) and len(test.ops) == 1 and len(test.comparators) == 1:
        return (
            isinstance(test.ops[0], (ast.Is, ast.IsNot))
            and _stable_identity_operand(test.left)
            and _stable_identity_operand(test.comparators[0])
        )
    if isinstance(test, ast.BoolOp) and isinstance(test.op, (ast.And, ast.Or)):
        return all(_guard_is_repeatable(value) for value in test.values)
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        return _guard_is_repeatable(test.operand)
    if isinstance(test, ast.Constant) and isinstance(test.value, bool):
        return True
    return False


def _test_implies(candidate, required):
    """Vrai si ``candidate`` contient explicitement ``required`` comme garde."""
    if _same_expr(candidate, required):
        return True
    if isinstance(candidate, ast.BoolOp) and isinstance(candidate.op, ast.And):
        return any(_test_implies(value, required) for value in candidate.values)
    return False


def _line_in_statements(statements, line):
    for statement in statements:
        start = getattr(statement, "lineno", 0)
        end = getattr(statement, "end_lineno", start)
        if start and start <= line <= end:
            return True
    return False


def _name_loaded(node, name):
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id == name and isinstance(child.ctx, ast.Load):
            return True
    return False


def _guard_dependencies(test):
    """Expressions dont une réaffectation explicite peut changer la garde."""
    dependencies = set()
    for node in ast.walk(test):
        if isinstance(node, (ast.Name, ast.Attribute, ast.Subscript)):
            dependencies.add(_expr_key(node))
    return dependencies


def _target_dependencies(target):
    keys = set()
    for node in ast.walk(target):
        if isinstance(node, (ast.Name, ast.Attribute, ast.Subscript)):
            keys.add(_expr_key(node))
    return keys


def _expression_dependencies(expression):
    keys = set()
    for node in ast.walk(expression):
        if isinstance(node, (ast.Name, ast.Attribute, ast.Subscript)):
            keys.add(_expr_key(node))
    return keys


def _node_mutates_dependencies(node, dependencies):
    targets = []
    if isinstance(node, ast.Assign):
        targets.extend(node.targets)
    elif isinstance(node, ast.AnnAssign):
        targets.append(node.target)
    elif isinstance(node, ast.AugAssign):
        targets.append(node.target)
    elif isinstance(node, ast.NamedExpr):
        targets.append(node.target)
    elif isinstance(node, ast.Delete):
        targets.extend(node.targets)

    for target in targets:
        if dependencies & _target_dependencies(target):
            return True

    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Attribute):
            if _expr_key(node.func.value) in dependencies:
                return True
        call_values = list(node.args) + [keyword.value for keyword in node.keywords]
        for value in call_values:
            if dependencies & _expression_dependencies(value):
                return True
    return False


def _statements_mutate_dependencies(statements, dependencies):
    for statement in statements:
        for node in ast.walk(statement):
            if _node_mutates_dependencies(node, dependencies):
                return True
    return False


def _parent_map(tree):
    parents = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    return parents


def _inside_repeating_construct(tree, node):
    parents = _parent_map(tree)
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.For, ast.AsyncFor, ast.While)):
            return True
    return False


def _guard_is_stable_between(tree, original, later, branch):
    """Refuse une corrélation si la stabilité n'est pas prouvée."""
    # Une mutation située textuellement après le second test peut s'exécuter
    # avant sa prochaine évaluation via un back-edge de boucle. Plutôt que de
    # reconstruire un CFG complet, on garde ces cas en revue.
    if _inside_repeating_construct(tree, original) or _inside_repeating_construct(tree, later):
        return False

    dependencies = _guard_dependencies(original.test)
    unassigned_branch = original.orelse if branch == "body_only" else original.body
    if _statements_mutate_dependencies(unassigned_branch, dependencies):
        return False

    start = getattr(original, "end_lineno", original.lineno)
    end = later.lineno
    if end <= start:
        return True

    for node in ast.walk(tree):
        line = getattr(node, "lineno", 0)
        if start < line < end and _node_mutates_dependencies(node, dependencies):
            return False
    return True


def _branch_guarantees_name(original, branch, name):
    statements = original.body if branch == "body_only" else original.orelse
    return name in base.guaranteed_definitions(statements, set())


def _load_is_protected_by_correlated_guard(tree, finding):
    original = None
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and node.lineno == finding["if_line"]:
            original = node
            break
    if original is None or not _guard_is_repeatable(original.test):
        return False

    line = finding["line"]
    name = finding["name"]
    branch = finding["detail"]

    if not _branch_guarantees_name(original, branch, name):
        return False

    negated_original = _negated(original.test)

    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or node is original or node.lineno < original.lineno:
            continue
        if not _guard_is_repeatable(node.test):
            continue
        if node.lineno == line and _name_loaded(node.test, name):
            continue

        in_body = _line_in_statements(node.body, line)
        in_else = _line_in_statements(node.orelse, line)
        if not (in_body or in_else):
            continue
        if not _guard_is_stable_between(tree, original, node, branch):
            continue

        if branch == "body_only":
            if in_body and _test_implies(node.test, original.test):
                return True
            if in_else and _same_expr(node.test, negated_original):
                return True
        elif branch == "else_only":
            if in_body and _test_implies(node.test, negated_original):
                return True
            if in_else and _same_expr(node.test, original.test):
                return True

    return False


def _load_tree(path):
    session = SourceAuditSession([path])
    loaded = session.parse(path)
    session.require_complete()
    assert loaded is not None
    _source, tree = loaded
    return tree


def build_report(root=ROOT):
    raw = base.build_report(root)
    by_file = defaultdict(list)
    for item in raw["findings"]:
        by_file[item["file"]].append(item)

    qualified = []
    for relpath, items in by_file.items():
        tree = _load_tree(root / relpath)
        for item in items:
            result = dict(item)
            if _load_is_protected_by_correlated_guard(tree, item):
                result["classification"] = "correlated_guard"
                result["priority"] = "low"
                result["reason"] = "la branche garantit la définition et deux gardes à identité pure sont stables hors boucle"
            else:
                result["classification"] = "review"
                result["priority"] = "high"
                result["reason"] = "définition, répétabilité sans protocole dynamique, stabilité hors boucle ou implication de garde non démontrable"
            qualified.append(result)

    qualified.sort(key=lambda item: (item["file"], item["line"], item["name"]))
    return {
        "count": len(qualified),
        "priorities": dict(Counter(item["priority"] for item in qualified)),
        "classifications": dict(Counter(item["classification"] for item in qualified)),
        "findings": qualified,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default="", metavar="FILE")
    args = parser.parse_args(argv)

    report = build_report()
    print(f"BRANCH_ASSIGNMENT_QUALIFIED={report['count']} {report['priorities']} {report['classifications']}")
    for item in report["findings"]:
        if item["priority"] == "high":
            print(f"- REVIEW {item['file']}:{item['line']} {item['function']} — {item['name']} ({item['detail']})")

    if args.json:
        output = Path(args.json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
