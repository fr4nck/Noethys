#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Classe les alertes de ``audit_runtime_patterns`` pour une passe de hardening.

L'audit historique privilégie le rappel : il signale volontairement des motifs
qui peuvent être sûrs. Ce module ne masque pas ces occurrences : il les classe
afin que la passe anti-bugs consacre la revue humaine aux chemins réellement
ambigus. Les lectures complémentaires réutilisent le contrat de couverture des
sources et ne tolèrent aucun décodage/parsing silencieusement dégradé.
"""

from __future__ import annotations

import ast
import json
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

from scripts import audit_runtime_patterns as base
from scripts.audit_source_coverage import SourceAuditSession

ROOT = base.NOETHYS_ROOT


@lru_cache(maxsize=None)
def _loaded_source(relpath: str):
    path = ROOT / relpath
    session = SourceAuditSession([path])
    loaded = session.parse(path)
    session.require_complete()
    assert loaded is not None
    return loaded


def _source_lines(relpath: str) -> list[str]:
    source, _tree = _loaded_source(relpath)
    return source.splitlines()


def _source_tree(relpath: str):
    _source, tree = _loaded_source(relpath)
    return tree


def _sql_window(lines: list[str], line_1based: int, lookback: int = 35) -> str:
    start = max(0, line_1based - lookback - 1)
    end = min(len(lines), line_1based)
    return "\n".join(lines[start:end]).upper()


def _last_select_window(lines: list[str], line_1based: int) -> str:
    context = _sql_window(lines, line_1based)
    pos = context.rfind("SELECT")
    return context[pos:] if pos >= 0 else ""


def _single_row_aggregate(lines: list[str], line_1based: int) -> bool:
    query = _last_select_window(lines, line_1based)
    if not query or "GROUP BY" in query:
        return False
    return bool(re.search(r"\b(?:COUNT|SUM|MIN|MAX|AVG)\s*\(", query))


def _primary_key_lookup(lines: list[str], line_1based: int) -> bool:
    query = _last_select_window(lines, line_1based)
    if not query or "GROUP BY" in query:
        return False
    return bool(re.search(r"\bWHERE\b[^;\n]*(?:\b[A-Z_]+\.)?ID[A-Z0-9_]*\s*=\s*%[DS]", query))


def _same_line_guard(varname: str, line: str) -> bool:
    var = re.escape(varname)
    if re.search(rf"\b{var}\s*\[[^]]+\].*\bif\s+{var}\b", line):
        return True
    if re.search(rf"\bif\s+{var}\b.*\band\b.*\b{var}\s*\[", line):
        return True
    if re.search(rf"\bif\s+not\s+{var}\b.*\bor\b.*\b{var}\s*\[", line):
        return True
    if re.search(rf"\blen\s*\(\s*{var}\s*\).*\b(?:or|and)\b.*\b{var}\s*\[", line):
        return True
    return False


def _line_inside(node, line: int) -> bool:
    start = getattr(node, "lineno", 0)
    end = getattr(node, "end_lineno", start)
    return bool(start and start <= line <= end)


def _inside_handled_try(relpath: str, line: int) -> bool:
    tree = _source_tree(relpath)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try) or not node.handlers:
            continue
        for statement in node.body:
            if _line_inside(statement, line):
                return True
    return False


def _inside_main_guard(relpath: str, line: int) -> bool:
    tree = _source_tree(relpath)
    for node in ast.walk(tree):
        if not isinstance(node, ast.If) or not _line_inside(node, line):
            continue
        try:
            text = ast.unparse(node.test)
        except Exception:
            text = ""
        if "__name__" in text and "__main__" in text:
            return True
    return False


def _selection_index_from_same_list(lines: list[str], line_access: int, varname: str) -> bool:
    if not varname or not (0 < line_access <= len(lines)):
        return False
    access = lines[line_access - 1]
    if not re.search(rf"\b{re.escape(varname)}\s*\[\s*index\s*\]", access):
        return False
    start = max(0, line_access - 18)
    context = "\n".join(lines[start:line_access])
    return bool(
        re.search(r"\bindex\s*=\s*\w+\.GetSelection\s*\(\s*\)", context)
        or re.search(r"\bfor\s+index\s+in\s+\w+\.GetSelections\s*\(\s*\)", context)
    )


def classify_result_unguarded(item: dict) -> dict:
    result = dict(item)
    lines = _source_lines(item["file"])
    line = item["line"]
    if _inside_handled_try(item["file"], line):
        result["classification"] = "guarded_exception"
        result["priority"] = "low"
        result["reason"] = "l'indexation est dans un try doté d'un handler"
    elif _inside_main_guard(item["file"], line):
        result["classification"] = "demo_only"
        result["priority"] = "low"
        result["reason"] = "chemin de démonstration __main__, hors runtime applicatif"
    elif _single_row_aggregate(lines, line):
        result["classification"] = "aggregate_single_row"
        result["priority"] = "low"
        result["reason"] = "agrégat SQL sans GROUP BY : une ligne de résultat est garantie"
    elif _primary_key_lookup(lines, line):
        result["classification"] = "entity_lookup_invariant"
        result["priority"] = "medium"
        result["reason"] = "lookup d'une entité par identifiant : invariant métier à valider en recette, pas bug statique démontré"
    else:
        result["classification"] = "review"
        result["priority"] = "high"
        result["reason"] = "indexation directe sans garde démontrée"
    return result


def classify_result_assign(item: dict) -> dict:
    result = dict(item)
    lines = _source_lines(item["file"])
    m = re.match(r"\s*(\w+)\s*=", item.get("snippet_assign", ""))
    varname = m.group(1) if m else ""
    access_line = ""
    line_access = item.get("line_access", 0)
    if 0 < line_access <= len(lines):
        access_line = lines[line_access - 1]

    if varname and _same_line_guard(varname, access_line):
        result["classification"] = "guarded_same_line"
        result["priority"] = "low"
        result["reason"] = "l'indexation est protégée par court-circuit/ternaire sur la même ligne"
    elif _inside_handled_try(item["file"], line_access):
        result["classification"] = "guarded_exception"
        result["priority"] = "low"
        result["reason"] = "l'indexation est dans un try doté d'un handler"
    elif _inside_main_guard(item["file"], line_access):
        result["classification"] = "demo_only"
        result["priority"] = "low"
        result["reason"] = "chemin de démonstration __main__, hors runtime applicatif"
    elif varname and _selection_index_from_same_list(lines, line_access, varname):
        result["classification"] = "dialog_selection"
        result["priority"] = "low"
        result["reason"] = "l'index provient de la sélection du dialogue construit depuis la même liste"
    elif _single_row_aggregate(lines, item.get("line_assign", 0)):
        result["classification"] = "aggregate_single_row"
        result["priority"] = "low"
        result["reason"] = "agrégat SQL sans GROUP BY : une ligne de résultat est garantie"
    elif _primary_key_lookup(lines, item.get("line_assign", 0)):
        result["classification"] = "entity_lookup_invariant"
        result["priority"] = "medium"
        result["reason"] = "lookup d'une entité par identifiant : invariant métier à valider en recette, pas bug statique démontré"
    else:
        result["classification"] = "review"
        result["priority"] = "high"
        result["reason"] = "résultat indexé sans garde démontrée par l'audit"
    return result


def _bare_except_shapes(relpath: str) -> dict[int, str]:
    _source, tree = _loaded_source(relpath)
    shapes: dict[int, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler) or node.type is not None:
            continue
        body = node.body
        if len(body) == 1 and isinstance(body[0], ast.Pass):
            shape = "silent_pass"
        elif any(isinstance(child, (ast.Return, ast.Continue, ast.Break)) for stmt in body for child in ast.walk(stmt)):
            shape = "fallback_control_flow"
        else:
            shape = "broad_handler"
        shapes[node.lineno] = shape
    return shapes


def classify_bare_except(items: list[dict]) -> list[dict]:
    by_file: dict[str, list[dict]] = {}
    for item in items:
        by_file.setdefault(item["file"], []).append(item)

    output = []
    for relpath, file_items in by_file.items():
        shapes = _bare_except_shapes(relpath)
        lines = _source_lines(relpath)
        for item in file_items:
            result = dict(item)
            shape = shapes.get(item["line"], "review")
            start = max(0, item["line"] - 8)
            context = "\n".join(lines[start:item["line"]]) if lines else ""
            if shape == "silent_pass" and re.search(r"\bimport\s+[A-Za-z_]", context):
                classification = "optional_import"
                priority = "low"
            elif shape == "silent_pass":
                classification = "silent_pass"
                priority = "medium"
            elif shape == "fallback_control_flow":
                classification = "fallback_control_flow"
                priority = "medium"
            else:
                classification = "broad_handler"
                priority = "high"
            result["classification"] = classification
            result["priority"] = priority
            output.append(result)
    return output


def build_report() -> dict:
    raw = base.run_audit()
    classified = {
        "RESULT_UNGUARDED": [classify_result_unguarded(item) for item in raw["RESULT_UNGUARDED"]],
        "RESULT_ASSIGN": [classify_result_assign(item) for item in raw["RESULT_ASSIGN"]],
        "BARE_EXCEPT": classify_bare_except(raw["BARE_EXCEPT"]),
    }

    summary = {}
    for kind, items in classified.items():
        summary[kind] = {
            "total": len(items),
            "classifications": dict(Counter(item["classification"] for item in items)),
            "priorities": dict(Counter(item["priority"] for item in items)),
        }

    return {
        "summary": summary,
        "zero_debt": {key: len(raw[key]) for key in (
            "DB_UNCLOSED", "PY2_BUILTINS", "UNSAFE_EXEC", "INVALID_ESCAPE", "ENCODING_MBCS"
        )},
        "findings": classified,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default="", metavar="FILE")
    args = parser.parse_args()

    # Le socle runtime affiche ici la preuve agrégée trouvés=lus=parsés.
    raw_coverage = base._coverage_session(ROOT)
    raw_coverage.report(prefix="Couverture classement runtime")
    raw_coverage.require_complete()

    report = build_report()
    for kind, data in report["summary"].items():
        print(f"{kind}: {data['total']} — {data['classifications']}")
    print(f"zero-debt: {report['zero_debt']}")

    if args.json:
        path = Path(args.json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Rapport JSON exporté : {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
