#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Noe-001 - Audit SQL strict

Analyse les fichiers Python pour identifier les requêtes potentiellement
sensibles à ONLY_FULL_GROUP_BY.

Le script ne modifie aucun fichier.
"""

import argparse
import ast
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

SELECT_RE = re.compile(r"\bSELECT\b", re.IGNORECASE)
GROUP_BY_RE = re.compile(r"\bGROUP\s+BY\b", re.IGNORECASE)
HAVING_RE = re.compile(r"\bHAVING\b", re.IGNORECASE)
AGGREGATE_RE = re.compile(r"\b(SUM|COUNT|AVG|MIN|MAX)\s*\(", re.IGNORECASE)


class SQLCandidate(object):
    def __init__(self, path, line, sql):
        self.path = path
        self.line = line
        self.sql = sql
        self.has_aggregate = bool(AGGREGATE_RE.search(sql))
        self.has_having = bool(HAVING_RE.search(sql))

    @property
    def risk(self):
        if self.has_aggregate:
            return "HIGH"
        return "MEDIUM"

    @property
    def reason(self):
        if self.has_aggregate:
            return "GROUP BY avec agrégat : vérifier les colonnes SELECT non agrégées"
        return "GROUP BY sans agrégat : probable dédoublonnage historique à simplifier"

    def summary(self):
        compact = " ".join(self.sql.split())
        if len(compact) > 180:
            compact = compact[:177] + "..."
        return compact


def _string_value(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if hasattr(ast, "Str") and isinstance(node, ast.Str):
        return node.s
    return None


def extract_sql_candidates(path):
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return []

    candidates = []
    seen = set()
    for node in ast.walk(tree):
        sql = _string_value(node)
        if not sql:
            continue
        if not SELECT_RE.search(sql) or not GROUP_BY_RE.search(sql):
            continue

        line = getattr(node, "lineno", 1)
        key = (line, sql)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(SQLCandidate(path, line, sql))

    candidates.sort(key=lambda item: item.line)
    return candidates


def iter_python_files(root):
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if ".git" in path.parts:
            continue
        yield path


def scan(root):
    candidates = []
    for path in iter_python_files(root):
        candidates.extend(extract_sql_candidates(path))
    candidates.sort(key=lambda item: (item.risk != "HIGH", str(item.path), item.line))
    return candidates


def print_text(candidates, root):
    if not candidates:
        print("Aucun candidat GROUP BY détecté.")
        return

    for item in candidates:
        try:
            relative = item.path.relative_to(root)
        except ValueError:
            relative = item.path
        print("[%s] %s:%d" % (item.risk, relative, item.line))
        print("  %s" % item.reason)
        print("  %s" % item.summary())

    high = sum(1 for item in candidates if item.risk == "HIGH")
    medium = len(candidates) - high
    print("\nTotal: %d candidat(s) — HIGH=%d, MEDIUM=%d" % (len(candidates), high, medium))


def print_markdown(candidates, root):
    print("# Audit SQL strict — candidats GROUP BY")
    print("")
    print("| Risque | Fichier | Ligne | Motif |")
    print("|---|---|---:|---|")
    for item in candidates:
        try:
            relative = item.path.relative_to(root)
        except ValueError:
            relative = item.path
        reason = item.reason.replace("|", "\\|")
        print("| %s | `%s` | %d | %s |" % (item.risk, relative, item.line, reason))
    print("")
    print("Total : **%d** candidat(s)." % len(candidates))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit Noe-001 des GROUP BY SQL")
    parser.add_argument(
        "--root",
        default=str(ROOT),
        help="Racine à analyser (défaut : dépôt Noethys)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "markdown"),
        default="text",
        help="Format de sortie",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    candidates = scan(root)
    if args.format == "markdown":
        print_markdown(candidates, root)
    else:
        print_text(candidates, root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
