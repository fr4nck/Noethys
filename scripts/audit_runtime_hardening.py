#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Classe les alertes de ``audit_runtime_patterns`` pour une passe de hardening.

L'audit historique privilégie le rappel : il signale volontairement des motifs
qui peuvent être sûrs (agrégat SQL garanti sur une ligne, garde placée sur la
même ligne, ``except: pass`` d'une dépendance optionnelle, etc.). Ce module ne
masque pas ces occurrences : il les classe afin que la passe anti-bugs puisse
consacrer la revue humaine aux chemins réellement ambigus.
"""

from __future__ import annotations

import ast
import json
import re
from collections import Counter
from pathlib import Path

from scripts import audit_runtime_patterns as base


ROOT = base.NOETHYS_ROOT


def _source_lines(relpath: str) -> list[str]:
    path = ROOT / relpath
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def _sql_window(lines: list[str], line_1based: int, lookback: int = 35) -> str:
    """Retourne le contexte SQL proche sans prétendre reconstruire le flot."""
    start = max(0, line_1based - lookback - 1)
    end = min(len(lines), line_1based)
    return "\n".join(lines[start:end]).upper()


def _single_row_aggregate(lines: list[str], line_1based: int) -> bool:
    """Agrégat SQL sans GROUP BY : SQL renvoie une ligne même sur ensemble vide."""
    context = _sql_window(lines, line_1based)
    # On se limite au dernier SELECT visible pour éviter qu'un ancien GROUP BY
    # du même bloc ne contamine la requête courante.
    pos = context.rfind("SELECT")
    if pos < 0:
        return False
    query = context[pos:]
    if "GROUP BY" in query:
        return False
    return bool(re.search(r"\b(?:COUNT|SUM|MIN|MAX|AVG)\s*\(", query))


def _same_line_guard(varname: str, line: str) -> bool:
    var = re.escape(varname)
    # Ternaires : x[0] if x else fallback
    if re.search(rf"\b{var}\s*\[[^]]+\].*\bif\s+{var}\b", line):
        return True
    # Court-circuit : if x and x[0] / if not x or x[0]
    if re.search(rf"\bif\s+{var}\b.*\band\b.*\b{var}\s*\[", line):
        return True
    if re.search(rf"\bif\s+not\s+{var}\b.*\bor\b.*\b{var}\s*\[", line):
        return True
    # Garde par longueur sur la même condition.
    if re.search(rf"\blen\s*\(\s*{var}\s*\).*\b(?:or|and)\b.*\b{var}\s*\[", line):
        return True
    return False


def classify_result_unguarded(item: dict) -> dict:
    result = dict(item)
    lines = _source_lines(item["file"])
    if _single_row_aggregate(lines, item["line"]):
        result["classification"] = "aggregate_single_row"
        result["priority"] = "low"
        result["reason"] = "agrégat SQL sans GROUP BY : une ligne de résultat est garantie"
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
    elif _single_row_aggregate(lines, item.get("line_assign", 0)):
        result["classification"] = "aggregate_single_row"
        result["priority"] = "low"
        result["reason"] = "agrégat SQL sans GROUP BY : une ligne de résultat est garantie"
    else:
        result["classification"] = "review"
        result["priority"] = "high"
        result["reason"] = "résultat indexé sans garde démontrée par l'audit"
    return result


def _bare_except_shapes(relpath: str) -> dict[int, str]:
    lines = _source_lines(relpath)
    if not lines:
        return {}
    source = "\n".join(lines)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}

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
            # Dépendance optionnelle : try/import suivi d'un except nu. On la
            # conserve dans le rapport mais elle n'est pas une erreur métier.
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
