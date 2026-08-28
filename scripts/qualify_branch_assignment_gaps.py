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
ne sont pas réaffectées entre les deux tests. Les gardes à effets de bord ou
réévaluables par appel restent ``high``. Les autres cas non prouvés restent eux
aussi ``high`` et doivent être revus humainement.
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
    return ast.dump(node, include_attributes=False)


def _negated(expr):
    return ast.UnaryOp(op=ast.Not(), operand=expr)


def _guard_is_repeatable(test):
    """Exclut les gardes dont deux évaluations identiques peuvent diverger."""
    unstable_nodes = (ast.Call, ast.NamedExpr, ast.Await, ast.Yield, ast.YieldFrom)
    return not any(isinstance(node, unstable_nodes) for node in ast.walk(test))


def _test_implies(candidate, required):
    """Vrai si ``candidate`` contient explicitement ``required`` comme garde.

    On reste volontairement conservateur : égalité structurelle ou conjonction
    ``required and ...`` seulement. Aucun raisonnement algébrique n'est tenté.
    Cette implication n'est utilisée que lorsque la lecture se trouve dans le
    corps du ``if`` ; l'``else`` exige une relation exacte, car la négation d'une
    conjonction n'implique pas la négation de chacun de ses termes.
    """
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


def _guard_is_stable_between(tree, original, later):
    """Refuse une corrélation si une dépendance visible est modifiée entre les tests.

    Le contrôle couvre les réaffectations explicites et les mutations directes
    du conteneur/attribut testé (par exemple ``state.clear()``). Une garde qui
    contient elle-même un appel est rejetée en amont : deux appels textuellement
    identiques ne constituent pas une preuve de stabilité.
    """
    dependencies = _guard_dependencies(original.test)
    start = getattr(original, "end_lineno", original.lineno)
    end = later.lineno
    if end <= start:
        return True

    for node in ast.walk(tree):
        line = getattr(node, "lineno", 0)
        if not (start < line < end):
            continue

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
                return False

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            receiver = node.func.value
            if _expr_key(receiver) in dependencies:
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

    # ``assigned_names`` voit volontairement les affectations imbriquées pour
    # maximiser le rappel. Une garde extérieure identique ne suffit donc pas :
    # il faut d'abord prouver que la branche prise définit réellement le nom sur
    # tous ses chemins qui continuent.
    if not _branch_guarantees_name(original, branch, name):
        return False

    negated_original = _negated(original.test)

    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or node is original or node.lineno < original.lineno:
            continue

        # Si la première lecture est dans la condition elle-même, la garde ne
        # peut évidemment pas protéger une variable qui n'existe peut-être pas.
        if node.lineno == line and _name_loaded(node.test, name):
            continue

        in_body = _line_in_statements(node.body, line)
        in_else = _line_in_statements(node.orelse, line)
        if not (in_body or in_else):
            continue
        if not _guard_is_stable_between(tree, original, node):
            continue

        if branch == "body_only":
            # Corps : H implique G est suffisant. Else : il faut que H soit
            # exactement ``not G`` ; ``not G and X`` ne suffit pas car son else
            # contient aussi le chemin ``not G and not X``.
            if in_body and _test_implies(node.test, original.test):
                return True
            if in_else and _same_expr(node.test, negated_original):
                return True
        elif branch == "else_only":
            # La définition vient de ``not G``. Le corps accepte une condition
            # plus restrictive qui implique ``not G`` ; l'else n'est sûr ici
            # que pour le test exact ``G``.
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
                result["reason"] = "la branche garantit la définition, la garde est répétable et stable, et la première lecture est dominée par une condition sûre"
            else:
                result["classification"] = "review"
                result["priority"] = "high"
                result["reason"] = "définition de branche, répétabilité, stabilité ou implication de garde insuffisamment démontrable"
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
