#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit des motifs runtime dangereux dans Noethys.

Méthodologie adaptée de fr4nck/Teamworks-CCNS (scripts/audit_runtime_risks.py).
Analyse statique par expressions régulières + AST.

Motifs audités
--------------
1.  RESULT_UNGUARDED   : DB.ResultatReq()[N] sans vérification de longueur préalable.
2.  RESULT_ASSIGN      : liste = DB.ResultatReq() suivi de liste[N] sans garde len/if.
3.  DB_UNCLOSED        : GestionDB.DB() ouvert dans une fonction sans DB.Close() appelé.
4.  BARE_EXCEPT        : clause ``except:`` sans type d'exception.
5.  PY2_BUILTINS       : appels directs à unicode(), basestring(), raw_input() sans garde six.
6.  UNSAFE_EXEC        : eval() ou exec() (hors commentaires).
7.  INVALID_ESCAPE     : séquences d'échappement invalides (\\c, \\i, \\., \\ ...).
8.  ENCODING_MBCS      : fichiers déclarés # -*- coding: mbcs -*- (Windows-only).

Répertoires tiers exclus
------------------------
- ObjectListView/   (Philip Piper, tiers)
- Outils/           (wxScheduler, ultimatelistctrl, COM typelibs — tiers)

Usage
-----
    python scripts/audit_runtime_patterns.py [--fail-on MOTIF[,MOTIF...]] [--json FILE]

    --fail-on  : exit(1) si l'un des motifs listés présente des occurrences.
                 Valeurs acceptées : RESULT_UNGUARDED, RESULT_ASSIGN, DB_UNCLOSED,
                                     BARE_EXCEPT, PY2_BUILTINS, UNSAFE_EXEC,
                                     INVALID_ESCAPE, ENCODING_MBCS
    --json     : exporte le rapport complet dans un fichier JSON.

Seuils CI configurés
--------------------
- PY2_BUILTINS  : fail si > 0 (aucun appel Python 2 non-gardé toléré)
- DB_UNCLOSED   : informatif (seuil à abaisser au fil des corrections)
"""

import json
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

NOETHYS_ROOT = Path(__file__).parent.parent / "noethys"

# Répertoires tiers — exclus de l'audit
THIRD_PARTY_DIRS = {"ObjectListView", "Outils"}

# Motifs qui déclenchent exit(1) si des occurrences sont trouvées.
FAIL_CONDITIONS = {
    "PY2_BUILTINS": 0,  # Zéro tolérance pour les appels Python 2 non-gardés
}

# Séquences d'échappement invalides en Python 3.12+
# (exclut les valides: \n \r \t \b \f \v \a \u \U \x \0-\9 \' \" \\)
_VALID_ESCAPES = set("nrtbfvauU0123456789x'\"\\")
_INVALID_ESCAPE_RE = re.compile(
    r'"[^"\\]*(?:\\(?![nrtbfvauU0123456789x\'\"\\])[^"\\]*)*"'
    r"|'[^'\\]*(?:\\(?![nrtbfvauU0123456789x\'\"\\])[^'\\]*)*'"
)


# ---------------------------------------------------------------------------
# Collecte des fichiers
# ---------------------------------------------------------------------------

def iter_python_files(root: Path):
    """Yield all .py files under root (skip __pycache__ and third-party dirs)."""
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [
            d for d in dirs
            if d != "__pycache__"
            and d not in THIRD_PARTY_DIRS
        ]
        for fname in files:
            if fname.endswith(".py"):
                yield Path(dirpath) / fname


# ---------------------------------------------------------------------------
# Motif 8 : encodage mbcs
# ---------------------------------------------------------------------------

def check_encoding_mbcs(path: Path, root: Path) -> list:
    issues = []
    try:
        first_line = path.read_bytes().split(b"\n")[0].decode("ascii", errors="replace")
        if "coding: mbcs" in first_line or "coding:mbcs" in first_line:
            issues.append({
                "file": str(path.relative_to(root)),
                "line": 1,
                "snippet": first_line.strip(),
            })
    except Exception:
        pass
    return issues


# ---------------------------------------------------------------------------
# Analyses textuelles ligne par ligne
# ---------------------------------------------------------------------------

def _is_in_py2_only_block(lines: list, lineno_0indexed: int) -> bool:
    """
    Heuristic: return True if a line appears inside a ``if six.PY2:`` block
    or in the ``else:`` branch of a ``if six.PY3:`` block.
    Looks back up to 15 lines for the conditional.
    """
    for j in range(lineno_0indexed - 1, max(-1, lineno_0indexed - 15), -1):
        s = lines[j].strip()
        if re.match(r"if\s+six\.PY2\s*:", s):
            return True
        # else: after if six.PY3: — scan back further to find the conditional
        if s == "else:":
            for k in range(j - 1, max(-1, j - 10), -1):
                prev = lines[k].strip()
                if re.match(r"if\s+six\.PY3\s*:", prev):
                    return True
    return False


def _has_six_xrange_compat(lines: list) -> bool:
    """Détecte une importation explicite de xrange fournie par six.moves."""
    for raw in lines:
        if re.search(
            r"^\s*from\s+six\.moves\s+import\s+.*(?:\brange\s+as\s+xrange\b|\bxrange\b)",
            raw,
        ):
            return True
    return False


def check_text_patterns(path: Path, root: Path) -> dict:
    """Returns dict of pattern_name -> list of {file, line, snippet}."""
    results = {
        "RESULT_UNGUARDED": [],
        "BARE_EXCEPT": [],
        "PY2_BUILTINS": [],
        "UNSAFE_EXEC": [],
        "INVALID_ESCAPE": [],
    }

    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return results

    rel = str(path.relative_to(root))
    xrange_from_six = _has_six_xrange_compat(lines)

    for i, raw in enumerate(lines):
        stripped = raw.strip()

        # Skip pure comment lines
        if stripped.startswith("#"):
            continue

        # 1. RESULT_UNGUARDED: ResultatReq()[N] direct (not preceded by len check)
        if re.search(r"ResultatReq\s*\(\s*\)\s*\[", raw):
            results["RESULT_UNGUARDED"].append(
                {"file": rel, "line": i + 1, "snippet": stripped[:120]}
            )

        # 4. BARE_EXCEPT
        if re.match(r"\s*except\s*:", raw):
            results["BARE_EXCEPT"].append(
                {"file": rel, "line": i + 1, "snippet": stripped[:120]}
            )

        # 5a. unicode() call — only flag actual function calls, not strings/docstrings
        #     and only if not in a six.PY2-only guarded block
        if re.search(r"\bunicode\s*\(", raw) and '"unicode"' not in raw and "'unicode'" not in raw:
            if not _is_in_py2_only_block(lines, i):
                results["PY2_BUILTINS"].append(
                    {"file": rel, "line": i + 1,
                     "builtin": "unicode", "snippet": stripped[:120]}
                )

        # 5b. basestring — in isinstance/type context (not in strings)
        if re.search(r"\bbasestring\b", raw) and '"basestring"' not in raw and "'basestring'" not in raw:
            if not _is_in_py2_only_block(lines, i):
                results["PY2_BUILTINS"].append(
                    {"file": rel, "line": i + 1,
                     "builtin": "basestring", "snippet": stripped[:120]}
                )

        # 5c. raw_input() — standalone call, et seulement hors branche Python 2.
        if re.search(r"(?<!\.)raw_input\s*\(", raw):
            if not _is_in_py2_only_block(lines, i):
                results["PY2_BUILTINS"].append(
                    {"file": rel, "line": i + 1,
                     "builtin": "raw_input", "snippet": stripped[:120]}
                )

        # 5d. xrange() — six.moves fournit une compatibilité Python 3 légitime.
        if re.search(r"\bxrange\s*\(", raw):
            if not xrange_from_six and not _is_in_py2_only_block(lines, i):
                results["PY2_BUILTINS"].append(
                    {"file": rel, "line": i + 1,
                     "builtin": "xrange", "snippet": stripped[:120]}
                )

        # 6. UNSAFE_EXEC
        code_only = raw.split("#", 1)[0]
        if re.search(r"\beval\s*\(|\bexec\s*\(", code_only):
            results["UNSAFE_EXEC"].append(
                {"file": rel, "line": i + 1, "snippet": stripped[:120]}
            )

        # 7. INVALID_ESCAPE — simple heuristic on lines containing strings
        if ("'" in raw or '"' in raw):
            for m in re.finditer(r'(?<!r)(?<!b)"([^"\\]|\\.)*"'
                                 r"|(?<!r)(?<!b)'([^'\\]|\\.)*'", raw):
                s = m.group(0)
                for esc in re.finditer(r"\\(.)", s):
                    c = esc.group(1)
                    if c not in _VALID_ESCAPES:
                        results["INVALID_ESCAPE"].append(
                            {"file": rel, "line": i + 1, "snippet": stripped[:120]}
                        )
                        break

    return results


# ---------------------------------------------------------------------------
# Motif 2 : ResultatReq assign + unguarded access
# ---------------------------------------------------------------------------

def check_result_assign(path: Path, root: Path) -> list:
    """Detect: var = ResultatReq() followed by var[N] without length guard."""
    issues = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return issues

    rel = str(path.relative_to(root))

    for i, line in enumerate(lines):
        m = re.match(r"\s*(\w+)\s*=\s*(?:\w+\.)*ResultatReq\(\)\s*$", line)
        if not m:
            continue
        varname = re.escape(m.group(1))
        for j in range(i + 1, min(i + 8, len(lines))):
            nextline = lines[j]
            if re.search(rf"\b{varname}\s*\[", nextline):
                between = "\n".join(lines[i + 1:j])
                if not re.search(
                    rf"(if\s+.*{varname}|len\s*\(\s*{varname})", between
                ):
                    issues.append({
                        "file": rel,
                        "line_assign": i + 1,
                        "line_access": j + 1,
                        "snippet_assign": lines[i].strip()[:100],
                        "snippet_access": nextline.strip()[:100],
                    })
                break

    return issues


# ---------------------------------------------------------------------------
# Motif 3 : connexions DB non fermées
# ---------------------------------------------------------------------------

def check_db_unclosed(path: Path, root: Path) -> list:
    """
    Detect functions/methods that open GestionDB.DB() without calling DB.Close().
    Excludes functions that receive DB as parameter (caller owns the connection).
    """
    issues = []
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
    except Exception:
        return issues

    rel = str(path.relative_to(root))

    for i, line in enumerate(lines):
        m = re.match(r"^(\s*)def (\w+)\s*\(([^)]*)\):", line)
        if not m:
            continue
        indent, funcname, params = m.group(1), m.group(2), m.group(3)
        # Skip: DB received as argument (caller is responsible for Close)
        if re.search(r"\bDB\b", params):
            continue

        # Collect function body until next same-level def/class
        body_lines = []
        for j in range(i + 1, len(lines)):
            bline = lines[j]
            if bline.strip() == "":
                body_lines.append(bline)
                continue
            bm = re.match(r"^(\s*)(def |class )", bline)
            if bm and len(bm.group(1)) <= len(indent):
                break
            body_lines.append(bline)
        body = "\n".join(body_lines)

        opens = bool(re.search(r"\bDB[T]?\s*=\s*GestionDB\.DB\s*\(", body))
        closes = bool(re.search(r"\bDB[T]?\.(?:Close|close)\s*\(\)", body))

        if opens and not closes:
            issues.append({
                "file": rel,
                "line": i + 1,
                "function": funcname,
                "snippet": line.strip()[:100],
            })

    return issues


# ---------------------------------------------------------------------------
# Runner principal
# ---------------------------------------------------------------------------

def run_audit(root: Path = NOETHYS_ROOT) -> dict:
    report = {
        "RESULT_UNGUARDED": [],
        "RESULT_ASSIGN": [],
        "DB_UNCLOSED": [],
        "BARE_EXCEPT": [],
        "PY2_BUILTINS": [],
        "UNSAFE_EXEC": [],
        "INVALID_ESCAPE": [],
        "ENCODING_MBCS": [],
    }

    for pyfile in sorted(iter_python_files(root)):
        report["ENCODING_MBCS"].extend(check_encoding_mbcs(pyfile, root))
        text = check_text_patterns(pyfile, root)
        for key in ("RESULT_UNGUARDED", "BARE_EXCEPT", "PY2_BUILTINS",
                    "UNSAFE_EXEC", "INVALID_ESCAPE"):
            report[key].extend(text[key])
        report["RESULT_ASSIGN"].extend(check_result_assign(pyfile, root))
        report["DB_UNCLOSED"].extend(check_db_unclosed(pyfile, root))

    return report


def print_report(report: dict):
    total = sum(len(v) for v in report.values())
    print(f"\n{'='*72}")
    print(f"  Audit runtime Noethys — {total} occurrence(s) trouvée(s)")
    print(f"{'='*72}\n")
    for motif, items in report.items():
        fails = motif in FAIL_CONDITIONS and len(items) > FAIL_CONDITIONS[motif]
        status = "❌ FAIL" if fails else ("⚠️  WARN" if items else "✅  OK  ")
        print(f"  {status}  {motif} : {len(items)} occurrence(s)")
        if items and fails:
            for item in items[:5]:
                loc = f"{item.get('file','?')}:{item.get('line') or item.get('line_assign','?')}"
                snip = item.get("snippet") or item.get("snippet_assign", "")
                print(f"           {loc}: {snip}")
            if len(items) > 5:
                print(f"           … et {len(items) - 5} autre(s)")
    print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--fail-on", default="",
        help="Comma-separated list of pattern keys to fail on if > 0 occurrences",
    )
    parser.add_argument(
        "--json", default="", metavar="FILE",
        help="Export full report to JSON file",
    )
    args = parser.parse_args()

    global FAIL_CONDITIONS
    if args.fail_on:
        FAIL_CONDITIONS = {k.strip(): 0 for k in args.fail_on.split(",")}

    report = run_audit()
    print_report(report)

    if args.json:
        Path(args.json).write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Rapport JSON exporté : {args.json}")

    for motif, threshold in FAIL_CONDITIONS.items():
        count = len(report.get(motif, []))
        if count > threshold:
            print(f"CI FAIL : {motif} = {count} > seuil {threshold}", file=sys.stderr)
            sys.exit(1)

    print("Audit terminé — aucun seuil CI dépassé.")
    sys.exit(0)


if __name__ == "__main__":
    main()
