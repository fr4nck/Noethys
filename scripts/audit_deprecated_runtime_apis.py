#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Détecte des API Python historiques supprimées ou cassantes en Python moderne.

Le périmètre est volontairement limité aux motifs dont le remplacement est
sémantiquement clair. L'objectif n'est pas de signaler toutes les dépréciations,
mais les appels susceptibles de tomber immédiatement en AttributeError.
La couverture des fichiers analysés est bloquante.
"""

from __future__ import annotations

import ast
import json
from collections import Counter
from pathlib import Path

try:
    from scripts.audit_source_coverage import SourceAuditSession
except ModuleNotFoundError:
    from audit_source_coverage import SourceAuditSession

ROOT = Path(__file__).resolve().parents[1] / "noethys"
EXCLUDED_PARTS = {"ObjectListView", "Outils"}

ATTRIBUTE_RULES = {
    "isAlive": ("thread_isAlive", "Thread.isAlive() a été remplacé par is_alive()"),
    "isSet": ("event_isSet", "Event.isSet() a été remplacé par is_set()"),
    "clock": ("time_clock", "time.clock() a été supprimé en Python 3.8"),
    "getargspec": ("inspect_getargspec", "inspect.getargspec() a été supprimé"),
    "formatargspec": ("inspect_formatargspec", "inspect.formatargspec() a été supprimé"),
    "encodestring": ("base64_encodestring", "base64.encodestring() a été supprimé"),
    "decodestring": ("base64_decodestring", "base64.decodestring() a été supprimé"),
}


def iter_python_files(root=ROOT):
    for path in root.rglob("*.py"):
        relative = path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        yield path


def _qualified_name(node):
    parts = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def scan_tree(source, tree, path, root=ROOT):
    lines = source.splitlines()
    rel = str(path.relative_to(root)).replace("\\", "/")
    findings = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        attr = node.func.attr
        if attr not in ATTRIBUTE_RULES:
            continue

        kind, reason = ATTRIBUTE_RULES[attr]
        qualified = _qualified_name(node.func)
        if attr == "clock" and not qualified.startswith("time."):
            continue
        if attr in {"getargspec", "formatargspec"} and not qualified.startswith("inspect."):
            continue
        if attr in {"encodestring", "decodestring"} and not qualified.startswith("base64."):
            continue

        lineno = node.lineno
        findings.append({
            "file": rel,
            "line": lineno,
            "kind": kind,
            "api": qualified,
            "reason": reason,
            "snippet": lines[lineno - 1].strip()[:160] if 0 < lineno <= len(lines) else "",
        })

    return findings


def scan_file(path, root=ROOT):
    session = SourceAuditSession([path])
    loaded = session.parse(path)
    session.require_complete()
    assert loaded is not None
    source, tree = loaded
    return scan_tree(source, tree, path, root)


def build_report(root=ROOT):
    session = SourceAuditSession(iter_python_files(root))
    findings = []
    for path in session.paths:
        loaded = session.parse(path)
        if loaded is None:
            continue
        source, tree = loaded
        findings.extend(scan_tree(source, tree, path, root))
    findings.sort(key=lambda item: (item["file"], item["line"], item["kind"]))
    return {
        "count": len(findings),
        "kinds": dict(Counter(item["kind"] for item in findings)),
        "findings": findings,
        "_coverage": session,
    }


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default="", metavar="FILE")
    parser.add_argument("--fail-on-any", action="store_true")
    args = parser.parse_args(argv)

    report = build_report()
    session = report.pop("_coverage")
    print(f"DEPRECATED_RUNTIME_API={report['count']} — {report['kinds']}")
    for item in report["findings"]:
        print(f"- {item['file']}:{item['line']} {item['api']} — {item['reason']}")
    session.report(prefix="Couverture audit API runtime dépréciées")
    session.require_complete()

    if args.json:
        output = Path(args.json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    return 1 if args.fail_on_any and report["count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
