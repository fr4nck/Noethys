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
7.  INVALID_ESCAPE     : séquences d'échappement invalides.
8.  ENCODING_MBCS      : fichiers déclarés # -*- coding: mbcs -*- (Windows-only).

Répertoires tiers exclus
------------------------
- ObjectListView/
- Outils/

La couverture du périmètre retenu est bloquante : aucun fichier illisible ou
non parsable n'est transformé en zéro occurrence.
"""

import json
import os
import re
import sys
from functools import lru_cache
from pathlib import Path

try:
    from scripts.audit_source_coverage import SourceAuditSession
except ModuleNotFoundError:
    from audit_source_coverage import SourceAuditSession

NOETHYS_ROOT = Path(__file__).parent.parent / "noethys"
THIRD_PARTY_DIRS = {"ObjectListView", "Outils"}
FAIL_CONDITIONS = {
    "PY2_BUILTINS": 0,
}
_VALID_ESCAPES = set("nrtbfvauU0123456789x'\"\\")
_INVALID_ESCAPE_RE = re.compile(
    r'"[^"\\]*(?:\\(?![nrtbfvauU0123456789x\'\"\\])[^"\\]*)*"'
    r"|'[^'\\]*(?:\\(?![nrtbfvauU0123456789x\'\"\\])[^'\\]*)*'"
)


def iter_python_files(root: Path):
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [
            d for d in dirs
            if d != "__pycache__"
            and d not in THIRD_PARTY_DIRS
        ]
        for fname in files:
            if fname.endswith(".py"):
                yield Path(dirpath) / fname


@lru_cache(maxsize=None)
def _source_text(path: Path) -> str:
    session = SourceAuditSession([path])
    loaded = session.parse(path)
    session.require_complete()
    assert loaded is not None
    source, _tree = loaded
    return source


def check_encoding_mbcs(path: Path, root: Path) -> list:
    issues = []
    first_line = path.read_bytes().split(b"\n")[0].decode("ascii", errors="strict")
    if "coding: mbcs" in first_line or "coding:mbcs" in first_line:
        issues.append({
            "file": str(path.relative_to(root)),
            "line": 1,
            "snippet": first_line.strip(),
        })
    return issues


def _is_in_py2_only_block(lines: list, lineno_0indexed: int) -> bool:
    for j in range(lineno_0indexed - 1, max(-1, lineno_0indexed - 15), -1):
        s = lines[j].strip()
        if re.match(r"if\s+six\.PY2\s*:", s):
            return True
        if s == "else:":
            for k in range(j - 1, max(-1, j - 10), -1):
                prev = lines[k].strip()
                if re.match(r"if\s+six\.PY3\s*:", prev):
                    return True
    return False


def _has_six_xrange_compat(lines: list) -> bool:
    for raw in lines:
        if re.search(
            r"^\s*from\s+six\.moves\s+import\s+.*(?:\brange\s+as\s+xrange\b|\bxrange\b)",
            raw,
        ):
            return True
    return False


def check_text_patterns(path: Path, root: Path) -> dict:
    results = {
        "RESULT_UNGUARDED": [],
        "BARE_EXCEPT": [],
        "PY2_BUILTINS": [],
        "UNSAFE_EXEC": [],
        "INVALID_ESCAPE": [],
    }

    lines = _source_text(path).splitlines()
    rel = str(path.relative_to(root))
    xrange_from_six = _has_six_xrange_compat(lines)

    for i, raw in enumerate(lines):
        stripped = raw.strip()
        if stripped.startswith("#"):
            continue

        if re.search(r"ResultatReq\s*\(\s*\)\s*\[", raw):
            results["RESULT_UNGUARDED"].append(
                {"file": rel, "line": i + 1, "snippet": stripped[:120]}
            )

        if re.match(r"\s*except\s*:", raw):
            results["BARE_EXCEPT"].append(
                {"file": rel, "line": i + 1, "snippet": stripped[:120]}
            )

        if re.search(r"\bunicode\s*\(", raw) and '"unicode"' not in raw and "'unicode'" not in raw:
            if not _is_in_py2_only_block(lines, i):
                results["PY2_BUILTINS"].append(
                    {"file": rel, "line": i + 1,
                     "builtin": "unicode", "snippet": stripped[:120]}
                )

        if re.search(r"\bbasestring\b", raw) and '"basestring"' not in raw and "'basestring'" not in raw:
            if not _is_in_py2_only_block(lines, i):
                results["PY2_BUILTINS"].append(
                    {"file": rel, "line": i + 1,
                     "builtin": "basestring", "snippet": stripped[:120]}
                )

        if re.search(r"(?<!\.)raw_input\s*\(", raw):
            if not _is_in_py2_only_block(lines, i):
                results["PY2_BUILTINS"].append(
                    {"file": rel, "line": i + 1,
                     "builtin": "raw_input", "snippet": stripped[:120]}
                )

        if re.search(r"\bxrange\s*\(", raw):
            if not xrange_from_six and not _is_in_py2_only_block(lines, i):
                results["PY2_BUILTINS"].append(
                    {"file": rel, "line": i + 1,
                     "builtin": "xrange", "snippet": stripped[:120]}
                )

        code_only = raw.split("#", 1)[0]
        if re.search(r"\beval\s*\(|\bexec\s*\(", code_only):
            results["UNSAFE_EXEC"].append(
                {"file": rel, "line": i + 1, "snippet": stripped[:120]}
            )

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


def check_result_assign(path: Path, root: Path) -> list:
    issues = []
    lines = _source_text(path).splitlines()
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


def check_db_unclosed(path: Path, root: Path) -> list:
    issues = []
    lines = _source_text(path).splitlines()
    rel = str(path.relative_to(root))

    for i, line in enumerate(lines):
        m = re.match(r"^(\s*)def (\w+)\s*\(([^)]*)\):", line)
        if not m:
            continue
        indent, funcname, params = m.group(1), m.group(2), m.group(3)
        if re.search(r"\bDB\b", params):
            continue

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


def _coverage_session(root: Path):
    paths = tuple(sorted(iter_python_files(root)))
    session = SourceAuditSession(paths)
    for path in session.paths:
        session.parse(path)
    return session


def run_audit(root: Path = NOETHYS_ROOT, *, report_coverage: bool = False) -> dict:
    coverage = _coverage_session(root)
    if report_coverage:
        coverage.report(prefix="Couverture audit motifs runtime")
    coverage.require_complete()

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

    for pyfile in coverage.paths:
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

    report = run_audit(report_coverage=True)
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
