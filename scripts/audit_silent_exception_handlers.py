#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventorie les ``except Exception: pass`` silencieux du code applicatif.

Le remplacement des anciens ``except:`` nus empêche désormais d'avaler les
BaseException. Cet audit cherche ensuite les erreurs encore réellement
masquées, sans classer comme critique chaque simple affectation ou repli UI.
La couverture des sources est bloquante.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter
from pathlib import Path

try:
    from scripts.audit_source_coverage import SourceAuditSession
except ModuleNotFoundError:
    from audit_source_coverage import SourceAuditSession

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
EXCLUDED_PARTS = {"ObjectListView", "Outils"}
CLEANUP_METHODS = {
    "Close", "Destroy", "Stop", "disconnect", "Disconnect", "Unbind",
    "ReleaseMouse", "Thaw", "EndModal", "Remove", "Detach",
}
BUSINESS_MUTATION_METHODS = {
    "ReqInsert", "ReqMAJ", "ReqDEL", "Commit",
    "Sauvegarde", "Enregistrer", "Supprimer", "Ajouter", "Modifier",
}
FILESYSTEM_MUTATION_CALLS = {"os.rename", "os.replace", "shutil.move"}
SQL_WRITE_RE = re.compile(r"\b(?:INSERT|UPDATE|DELETE|REPLACE|ALTER|DROP|CREATE|TRUNCATE)\b", re.IGNORECASE)


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


def _qualified_name(node):
    parts = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def _called_methods(body):
    methods = []
    for stmt in body:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                methods.append(node.func.attr)
    return methods


def _called_qualified_names(body):
    names = []
    for stmt in body:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                name = _qualified_name(node.func)
                if name:
                    names.append(name)
    return names


def _is_cleanup(body):
    methods = _called_methods(body)
    return bool(methods) and all(method in CLEANUP_METHODS for method in methods)


def _contains_business_mutation(body):
    return any(method in BUSINESS_MUTATION_METHODS for method in _called_methods(body))


def _contains_filesystem_mutation(body):
    return any(name in FILESYSTEM_MUTATION_CALLS for name in _called_qualified_names(body))


def _contains_silent_sql_write(body, source):
    has_execute = any(method == "ExecuterReq" for method in _called_methods(body))
    if not has_execute:
        return False
    fragments = []
    for stmt in body:
        segment = ast.get_source_segment(source, stmt)
        if segment:
            fragments.append(segment)
    return bool(SQL_WRITE_RE.search("\n".join(fragments)))


def _contains_assignment(body):
    return any(
        isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
        for stmt in body
        for node in ast.walk(stmt)
    )


def _snippet(lines, start, end):
    start = max(1, start)
    end = min(len(lines), end)
    return "\n".join(f"{i:05d}: {lines[i - 1]}" for i in range(start, end + 1))


def _scan_loaded(source, tree, path, root=NOETHYS):
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
            elif _contains_business_mutation(node.body) or _contains_silent_sql_write(node.body, source):
                classification, priority = "silent_business_mutation", "high"
                reason = "écriture DB ou mutation métier masquée par un pass silencieux"
            elif _contains_filesystem_mutation(node.body):
                classification, priority = "silent_filesystem_mutation", "high"
                reason = "renommage/déplacement persistant masqué : migration potentiellement incomplète"
            elif _contains_assignment(node.body):
                classification, priority = "silent_state_fallback", "medium"
                reason = "calcul/affectation ignoré : repli implicite à vérifier"
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


def scan_file(path, root=NOETHYS):
    session = SourceAuditSession([path])
    loaded = session.parse(path)
    session.require_complete()
    assert loaded is not None
    source, tree = loaded
    return _scan_loaded(source, tree, path, root)


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


def _coverage_session(root=NOETHYS):
    session = SourceAuditSession(iter_python_files(root))
    for path in session.paths:
        session.parse(path)
    return session


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default="", metavar="FILE")
    parser.add_argument("--fail-on-high", action="store_true")
    args = parser.parse_args(argv)

    coverage = _coverage_session()
    coverage.report(prefix="Couverture audit handlers silencieux")
    coverage.require_complete()

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
