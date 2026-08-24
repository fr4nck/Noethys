#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventorie les ``except Exception: pass`` silencieux du code applicatif.

Le remplacement des anciens ``except:`` nus empêche désormais d'avaler les
BaseException, mais un handler ``Exception`` silencieux peut encore masquer un
bug métier. Cet audit sépare les imports optionnels et nettoyages best-effort
des suppressions silencieuses de runtime à relire.
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
EXCLUDED_PARTS = {"ObjectListView", "Outils"}
CLEANUP_METHODS = {
    "Close", "Destroy", "Stop", "disconnect", "Disconnect", "Unbind",
    "ReleaseMouse", "Thaw", "EndModal", "Remove", "Detach",
}


def iter_python_files(root=NOETHYS):
    for path in root.rglob("*.py"):
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        yield path


def _is_silent(handler):
    return len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass)


def _is_optional_import(body):
    if not body:
        return False
    return all(isinstance(stmt, (ast.Import, ast.ImportFrom)) for stmt in body)


def _called_methods(body):
    methods = []
    for stmt in body:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                methods.append(node.func.attr)
    return methods


def _is_cleanup(body):
    methods = _called_methods(body)
    return bool(methods) and all(method in CLEANUP_METHODS for method in methods)


def _contains_db_or_mutation(body):
    for stmt in body:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr in {
                    "ExecuterReq", "ReqInsert", "ReqMAJ", "ReqDEL", "Commit",
                    "Sauvegarde", "Enregistrer", "Supprimer", "Ajouter", "Modifier",
                }:
                    return True
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                return True
    return False


def _snippet(lines, start, end):
    start = max(1, start)
    end = min(len(lines), end)
    return "\n".join(f"{i:05d}: {lines[i - 1]}" for i in range(start, end + 1))


def scan_file(path, root=NOETHYS):
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError):
        return []
    lines = source.splitlines()
    relpath = str(path.relative_to(root)).replace("\\", "/")
    findings = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        for handler in node.handlers:
            if not _is_silent(handler):
                continue

            if _is_optional_import(node.body):
                classification, priority = "optional_import", "low"
                reason = "import optionnel explicitement toléré"
            elif _is_cleanup(node.body):
                classification, priority = "best_effort_cleanup", "low"
                reason = "nettoyage de ressource best-effort"
            elif _contains_db_or_mutation(node.body):
                classification, priority = "silent_runtime_mutation", "high"
                reason = "opération/affectation runtime masquée par un pass silencieux"
            else:
                classification, priority = "silent_runtime", "medium"
                reason = "exception runtime ignorée sans journal ni repli explicite"

            try_start = getattr(node, "lineno", handler.lineno)
            try_end = max((getattr(stmt, "end_lineno", getattr(stmt, "lineno", try_start)) for stmt in node.body), default=try_start)
            findings.append({
                "file": relpath,
                "try_line": try_start,
                "except_line": handler.lineno,
                "classification": classification,
                "priority": priority,
                "reason": reason,
                "snippet": _snippet(lines, try_start, min(handler.end_lineno or handler.lineno, try_end + 5)),
            })
    return findings


def scan(root=NOETHYS):
    findings = []
    for path in iter_python_files(root):
        findings.extend(scan_file(path, root))
    findings.sort(key=lambda item: (item["priority"] != "high", item["file"], item["except_line"]))
    return findings


def build_report(root=NOETHYS):
    findings = scan(root)
    return {
        "count": len(findings),
        "classifications": dict(Counter(item["classification"] for item in findings)),
        "priorities": dict(Counter(item["priority"] for item in findings)),
        "findings": findings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default="", metavar="FILE")
    parser.add_argument("--fail-on-high", action="store_true")
    args = parser.parse_args(argv)

    report = build_report()
    print(f"SILENT_EXCEPTION={report['count']} — {report['classifications']}")
    for item in report["findings"]:
        if item["priority"] == "high":
            print(f"- HIGH {item['file']}:{item['except_line']} {item['classification']}")

    if args.json:
        output = Path(args.json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Rapport JSON exporté : {output}")

    if args.fail_on_high and report["priorities"].get("high", 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
