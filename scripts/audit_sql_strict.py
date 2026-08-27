#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Noe-001 - Audit SQL strict

Analyse les chaînes SQL Python contenant un ``GROUP BY`` et distingue :

- SAFE    : tous les GROUP BY de la chaîne sont compatibles avec une lecture
            stricte (chaque expression SELECT non agrégée est groupée) ;
- REVIEW  : au moins un GROUP BY sélectionne une expression non agrégée qui
            n'est pas groupée, contient un HAVING conservateur, ou n'a pas pu
            être analysé avec certitude ;
- DEDUPE  : GROUP BY strict-compatible sans agrégat, utilisé comme mécanisme
            de dédoublonnage historique et potentiellement simplifiable en
            DISTINCT, sans constituer à lui seul une incompatibilité stricte.

Les sous-requêtes sont analysées dans leur propre portée. L'analyse ne tente
pas d'inférer les dépendances fonctionnelles propres à un moteur SQL. Le script
ne modifie aucun fichier ni aucune base. La couverture des sources Python est
bloquante : aucun fichier non lu/non parsé ne peut produire zéro candidat.
"""

import argparse
import ast
from pathlib import Path
import re

try:
    from scripts.audit_source_coverage import SourceAuditSession
except ModuleNotFoundError:
    from audit_source_coverage import SourceAuditSession

ROOT = Path(__file__).resolve().parents[1]

SELECT_RE = re.compile(r"\bSELECT\b", re.IGNORECASE)
GROUP_BY_RE = re.compile(r"\bGROUP\s+BY\b", re.IGNORECASE)
HAVING_RE = re.compile(r"\bHAVING\b", re.IGNORECASE)
AGGREGATE_RE = re.compile(r"\b(SUM|COUNT|AVG|MIN|MAX)\s*\(", re.IGNORECASE)
AS_ALIAS_RE = re.compile(r"\s+AS\s+[A-Za-z_][A-Za-z0-9_]*\s*$", re.IGNORECASE)
SIMPLE_TRAILING_ALIAS_RE = re.compile(
    r"^(.*(?:\)|\]|`|\"|'|[A-Za-z0-9_.]))\s+([A-Za-z_][A-Za-z0-9_]*)\s*$",
    re.DOTALL,
)
SAFE_CONSTANT_RE = re.compile(
    r"^(?:NULL|TRUE|FALSE|-?\d+(?:\.\d+)?|'(?:[^']|'')*'|\"(?:[^\"]|\"\")*\")$",
    re.IGNORECASE | re.DOTALL,
)

CLAUSE_KEYWORDS = (
    "HAVING",
    "ORDER BY",
    "LIMIT",
    "UNION",
    "PROCEDURE",
    "INTO OUTFILE",
)


def _is_ident_char(char):
    return char.isalnum() or char == "_"


def _keyword_matches(sql, pos, keyword):
    parts = keyword.split()
    cursor = pos
    for index, part in enumerate(parts):
        end = cursor + len(part)
        if sql[cursor:end].lower() != part.lower():
            return None
        if end < len(sql) and _is_ident_char(sql[end]):
            return None
        if index == 0 and cursor > 0 and _is_ident_char(sql[cursor - 1]):
            return None
        cursor = end
        if index != len(parts) - 1:
            if cursor >= len(sql) or not sql[cursor].isspace():
                return None
            while cursor < len(sql) and sql[cursor].isspace():
                cursor += 1
    return cursor


def _find_top_level_keyword(sql, keyword, start=0):
    depth = 0
    quote = None
    pos = start
    while pos < len(sql):
        char = sql[pos]
        if quote:
            if char == quote:
                if pos + 1 < len(sql) and sql[pos + 1] == quote:
                    pos += 2
                    continue
                quote = None
            elif char == "\\" and quote in ("'", '"') and pos + 1 < len(sql):
                pos += 2
                continue
            pos += 1
            continue

        if char in ("'", '"', "`"):
            quote = char
            pos += 1
            continue
        if char == "(":
            depth += 1
            pos += 1
            continue
        if char == ")":
            if depth:
                depth -= 1
            pos += 1
            continue
        if depth == 0:
            end = _keyword_matches(sql, pos, keyword)
            if end is not None:
                return pos, end
        pos += 1
    return None


def _split_top_level_csv(text):
    items = []
    current = []
    depth = 0
    quote = None
    pos = 0
    while pos < len(text):
        char = text[pos]
        if quote:
            current.append(char)
            if char == quote:
                if pos + 1 < len(text) and text[pos + 1] == quote:
                    current.append(text[pos + 1])
                    pos += 2
                    continue
                quote = None
            elif char == "\\" and quote in ("'", '"') and pos + 1 < len(text):
                current.append(text[pos + 1])
                pos += 2
                continue
            pos += 1
            continue

        if char in ("'", '"', "`"):
            quote = char
            current.append(char)
        elif char == "(":
            depth += 1
            current.append(char)
        elif char == ")":
            if depth:
                depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            item = "".join(current).strip()
            if item:
                items.append(item)
            current = []
        else:
            current.append(char)
        pos += 1

    item = "".join(current).strip()
    if item:
        items.append(item)
    return items


def _parenthesized_selects(sql):
    stack = []
    quote = None
    results = []
    seen = set()
    pos = 0
    while pos < len(sql):
        char = sql[pos]
        if quote:
            if char == quote:
                if pos + 1 < len(sql) and sql[pos + 1] == quote:
                    pos += 2
                    continue
                quote = None
            elif char == "\\" and quote in ("'", '"') and pos + 1 < len(sql):
                pos += 2
                continue
            pos += 1
            continue
        if char in ("'", '"', "`"):
            quote = char
        elif char == "(":
            stack.append(pos)
        elif char == ")" and stack:
            start = stack.pop()
            inner = sql[start + 1:pos].strip()
            if SELECT_RE.search(inner) and GROUP_BY_RE.search(inner):
                key = " ".join(inner.split())
                if key not in seen:
                    seen.add(key)
                    results.append(inner)
        pos += 1
    return results


def _strip_alias(expression):
    expr = expression.strip()
    stripped = AS_ALIAS_RE.sub("", expr).strip()
    if stripped != expr:
        return stripped

    match = SIMPLE_TRAILING_ALIAS_RE.match(expr)
    if match:
        left, _alias = match.groups()
        left = left.strip()
        if "(" in left or ")" in left or " " in left:
            return left
    return expr


def _strip_wrapping_parentheses(expression):
    expr = expression.strip()
    while expr.startswith("(") and expr.endswith(")"):
        depth = 0
        quote = None
        closes_at_end = False
        for index, char in enumerate(expr):
            if quote:
                if char == quote:
                    quote = None
                continue
            if char in ("'", '"', "`"):
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    closes_at_end = index == len(expr) - 1
                    break
        if not closes_at_end:
            break
        expr = expr[1:-1].strip()
    return expr


def _normalize_expression(expression):
    expr = _strip_wrapping_parentheses(_strip_alias(expression))
    expr = expr.replace("`", "")
    expr = re.sub(r"\s+", " ", expr).strip().lower()
    expr = re.sub(r"\s*\.\s*", ".", expr)
    expr = re.sub(r"\s*=\s*", "=", expr)
    return expr


def _is_safe_constant(expression):
    return bool(SAFE_CONSTANT_RE.match(expression.strip()))


def _extract_select_and_group(sql):
    select_match = _find_top_level_keyword(sql, "SELECT")
    if select_match is None:
        return None
    from_match = _find_top_level_keyword(sql, "FROM", select_match[1])
    if from_match is None:
        return None
    group_match = _find_top_level_keyword(sql, "GROUP BY", from_match[1])
    if group_match is None:
        return None

    group_end = len(sql)
    semicolon = sql.find(";", group_match[1])
    if semicolon != -1:
        group_end = semicolon
    for keyword in CLAUSE_KEYWORDS:
        match = _find_top_level_keyword(sql, keyword, group_match[1])
        if match is not None:
            group_end = min(group_end, match[0])

    select_text = sql[select_match[1]:from_match[0]].strip()
    group_text = sql[group_match[1]:group_end].strip()
    if not select_text or not group_text:
        return None
    return _split_top_level_csv(select_text), _split_top_level_csv(group_text)


def _analyze_scope(sql):
    parsed = _extract_select_and_group(sql)
    if parsed is None:
        return None

    select_items, group_items = parsed
    normalized_group = {_normalize_expression(item) for item in group_items}
    ungrouped = []
    has_aggregate = False

    for item in select_items:
        if AGGREGATE_RE.search(item):
            has_aggregate = True
            continue
        stripped = _strip_alias(item)
        if _is_safe_constant(stripped):
            continue
        if _normalize_expression(stripped) not in normalized_group:
            ungrouped.append(stripped.strip())

    having = _find_top_level_keyword(sql, "HAVING") is not None
    if ungrouped:
        return {
            "classification": "REVIEW",
            "reason": "Expression(s) SELECT non agrégée(s) absente(s) du GROUP BY",
            "ungrouped": ungrouped,
        }
    if having:
        return {
            "classification": "REVIEW",
            "reason": "SELECT compatible, mais HAVING présent : revue manuelle conservatrice",
            "ungrouped": [],
        }
    if has_aggregate:
        return {
            "classification": "SAFE",
            "reason": "Toutes les expressions SELECT non agrégées sont présentes dans le GROUP BY",
            "ungrouped": [],
        }
    return {
        "classification": "DEDUPE",
        "reason": "GROUP BY sans agrégat et strict-compatible : dédoublonnage historique",
        "ungrouped": [],
    }


def _collect_group_scopes(sql, seen=None):
    if seen is None:
        seen = set()
    key = " ".join(sql.split())
    if key in seen:
        return []
    seen.add(key)

    scopes = []
    scope = _analyze_scope(sql)
    if scope is not None:
        scopes.append(scope)
    for inner in _parenthesized_selects(sql):
        scopes.extend(_collect_group_scopes(inner, seen))
    return scopes


class SQLCandidate(object):
    def __init__(self, path, line, sql):
        self.path = path
        self.line = line
        self.sql = sql
        self.scopes = _collect_group_scopes(sql)
        self._classify()

    def _classify(self):
        if not self.scopes:
            self.classification = "REVIEW"
            self.reason = "GROUP BY détecté mais portée SQL non analysable avec certitude"
            self.ungrouped_items = []
            return

        reviews = [scope for scope in self.scopes if scope["classification"] == "REVIEW"]
        if reviews:
            self.classification = "REVIEW"
            first = reviews[0]
            self.ungrouped_items = first.get("ungrouped", [])
            if self.ungrouped_items:
                preview = ", ".join(self.ungrouped_items[:4])
                if len(self.ungrouped_items) > 4:
                    preview += ", ..."
                self.reason = "%s : %s" % (first["reason"], preview)
            else:
                self.reason = first["reason"]
            return

        self.ungrouped_items = []
        if any(scope["classification"] == "DEDUPE" for scope in self.scopes):
            self.classification = "DEDUPE"
            self.reason = "GROUP BY strict-compatible sans agrégat : dédoublonnage historique à conserver ou simplifier"
            return

        self.classification = "SAFE"
        self.reason = "Tous les GROUP BY analysés sont strict-compatibles"

    @property
    def risk(self):
        if self.classification == "REVIEW":
            return "HIGH"
        if self.classification == "DEDUPE":
            return "MEDIUM"
        return "SAFE"

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


def extract_sql_candidates_from_tree(path, tree):
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


def extract_sql_candidates(path):
    session = SourceAuditSession([path])
    loaded = session.parse(path)
    session.require_complete()
    assert loaded is not None
    _source, tree = loaded
    return extract_sql_candidates_from_tree(path, tree)


def iter_python_files(root):
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts or ".git" in path.parts:
            continue
        yield path


def _scan_with_session(root):
    session = SourceAuditSession(iter_python_files(root))
    candidates = []
    for path in session.paths:
        loaded = session.parse(path)
        if loaded is None:
            continue
        _source, tree = loaded
        candidates.extend(extract_sql_candidates_from_tree(path, tree))
    order = {"REVIEW": 0, "DEDUPE": 1, "SAFE": 2}
    candidates.sort(key=lambda item: (order[item.classification], str(item.path), item.line))
    return candidates, session


def scan(root):
    candidates, session = _scan_with_session(root)
    session.require_complete()
    return candidates


def _filtered(candidates, only):
    if only == "all":
        return candidates
    wanted = only.upper()
    return [item for item in candidates if item.classification == wanted]


def _relative_path(item, root):
    try:
        return item.path.relative_to(root)
    except ValueError:
        return item.path


def _counts(candidates):
    return {
        name: sum(1 for item in candidates if item.classification == name)
        for name in ("REVIEW", "DEDUPE", "SAFE")
    }


def print_text(candidates, root, only="all"):
    shown = _filtered(candidates, only)
    if not shown:
        print("Aucun candidat pour le filtre %s." % only)
    for item in shown:
        relative = _relative_path(item, root)
        print("[%s] %s:%d" % (item.classification, relative, item.line))
        print("  %s" % item.reason)
        print("  %s" % item.summary())

    counts = _counts(candidates)
    print(
        "\nTotal: %d candidat(s) — REVIEW=%d, DEDUPE=%d, SAFE=%d"
        % (len(candidates), counts["REVIEW"], counts["DEDUPE"], counts["SAFE"])
    )
    if only != "all":
        print("Affichés (%s): %d" % (only.upper(), len(shown)))


def print_markdown(candidates, root, only="all"):
    shown = _filtered(candidates, only)
    print("# Audit SQL strict — candidats GROUP BY")
    print("")
    print("| Classe | Fichier | Ligne | Motif |")
    print("|---|---|---:|---|")
    for item in shown:
        relative = _relative_path(item, root)
        reason = item.reason.replace("|", "\\|")
        print("| %s | `%s` | %d | %s |" % (item.classification, relative, item.line, reason))
    counts = _counts(candidates)
    print("")
    print(
        "Total : **%d** candidat(s) — REVIEW=%d, DEDUPE=%d, SAFE=%d."
        % (len(candidates), counts["REVIEW"], counts["DEDUPE"], counts["SAFE"])
    )


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
    parser.add_argument(
        "--only",
        choices=("all", "review", "dedupe", "safe"),
        default="all",
        help="N'afficher qu'une classe tout en conservant les totaux globaux",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    candidates, session = _scan_with_session(root)
    session.report(prefix="Couverture audit SQL strict")
    session.require_complete()
    if args.format == "markdown":
        print_markdown(candidates, root, args.only)
    else:
        print_text(candidates, root, args.only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
