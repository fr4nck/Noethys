#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Qualifie les candidats ``branch_assignment_gap`` par corrélation de garde.

L'inventaire de base privilégie volontairement le rappel : une variable définie
uniquement dans une branche reste signalée dès qu'une lecture ultérieure est
visible. Une grande partie des faux positifs historiques suit toutefois un
contrat simple et sûr : la définition et la lecture sont protégées par la même
condition (ou par une condition ultérieure plus restrictive).

Ce module ne supprime aucune occurrence. Il requalifie seulement les candidats
dont la garde corrélée est démontrable dans l'AST. Les autres restent ``high``
et doivent être revus humainement.
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


def _negated(expr):
    return ast.UnaryOp(op=ast.Not(), operand=expr)


def _test_implies(candidate, required):
    """Vrai si ``candidate`` contient explicitement ``required`` comme garde.

    On reste volontairement conservateur : égalité structurelle ou conjonction
    ``required and ...`` seulement. Aucun raisonnement algébrique n'est tenté.
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


def _load_is_protected_by_correlated_guard(tree, finding):
    original = None
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and node.lineno == finding["if_line"]:
            original = node
            break
    if original is None:
        return False

    line = finding["line"]
    name = finding["name"]
    branch = finding["detail"]
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

        if branch == "body_only":
            if in_body and _test_implies(node.test, original.test):
                return True
            if in_else and _test_implies(node.test, negated_original):
                return True
        elif branch == "else_only":
            if in_else and _same_expr(node.test, original.test):
                return True
            if in_body and _test_implies(node.test, negated_original):
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
                result["reason"] = "la première lecture est protégée par la même garde ou une conjonction plus restrictive"
            else:
                result["classification"] = "review"
                result["priority"] = "high"
                result["reason"] = "aucune garde corrélée démontrable ne protège la première lecture"
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
