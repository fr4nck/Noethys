#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventorie la dette UI wxPython à éliminer pendant la refonte Repens.

L'audit ne modifie rien et n'échoue pas par défaut sur les occurrences. Il sert
de liste de travail exhaustive : tailles figées, toolbars dimensionnées
localement, dépendances visuelles qui contournent la façade Repens, boutons
bitmap historiques et combinaisons de flags connues pour produire des layouts
bloqués. La couverture des sources first-party est en revanche bloquante.

La section « couverture Repens » fournit un indicateur reproductible. Il ne
prétend pas mesurer la modernisation fonctionnelle de Noethys : il mesure la
part des fichiers UI qui déclarent une dépendance de style et qui passent déjà
exclusivement par ``UTILS_StyleRepens`` plutôt que directement par
``UTILS_Interface`` / ``UTILS_UIMetrics``.
"""

from __future__ import annotations

import argparse
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
EXCLUS = {"ObjectListView", "Outils", "__pycache__"}
UI_LAYERS = {"Ctrl", "Dlg", "Ol"}

PATTERNS = {
    "toolbar_bitmap_fixed": re.compile(r"SetToolBitmapSize\s*\(\s*(?:wx\.Size\s*\()?\s*\(?\s*(?:16|20|24|32|40|48)\s*,"),
    "aui_pane_fixed_size": re.compile(r"\.(?:MinSize|BestSize)\s*\(\s*\(\s*-?\d+\s*,\s*-?\d+"),
    "window_fixed_min_size": re.compile(r"\.SetMinSize\s*\(\s*\(\s*-?\d+\s*,\s*-?\d+"),
    "align_expand_conflict": re.compile(
        r"(?:wx\.EXPAND[^#\n]*wx\.ALIGN_(?:LEFT|RIGHT|TOP|BOTTOM|CENTER|CENTRE|CENTER_HORIZONTAL|CENTRE_HORIZONTAL|CENTER_VERTICAL|CENTRE_VERTICAL)"
        r"|wx\.ALIGN_(?:LEFT|RIGHT|TOP|BOTTOM|CENTER|CENTRE|CENTER_HORIZONTAL|CENTRE_HORIZONTAL|CENTER_VERTICAL|CENTRE_VERTICAL)[^#\n]*wx\.EXPAND)"
    ),
    "sizer_assertion_suppression": re.compile(
        r"WXSUPPRESS_SIZER_FLAGS_CHECK|DisableConsistencyChecks\s*\("
    ),
    "raw_grid_double_click": re.compile(r"GetGridWindow\(\)\.Bind\(wx\.EVT_LEFT_DCLICK"),
    "fixed_grid_column": re.compile(r"\.SetColSize\s*\([^,]+,\s*\d+\s*\)"),
    "legacy_grid_lines": re.compile(r"wx\.LC_HRULES\s*\|\s*wx\.LC_VRULES|wx\.LC_VRULES\s*\|\s*wx\.LC_HRULES"),
    "hardcoded_colour_role": re.compile(r"(?:SetBackgroundColour|SetForegroundColour|SetCellBackgroundColour)\s*\(\s*(?:wx\.)?Colour\s*\("),
    "legacy_bitmap_button": re.compile(r"\bwx\.BitmapButton\s*\("),
}

LEGACY_STYLE_IMPORT = re.compile(
    r"^\s*(?:"
    r"from\s+Utils\s+import\s+.*\bUTILS_(?:Interface|UIMetrics)\b"
    r"|from\s+Utils\.UTILS_(?:Interface|UIMetrics)\s+import\b"
    r"|import\s+Utils\.UTILS_(?:Interface|UIMetrics)\b"
    r")"
)
REPENS_IMPORT = re.compile(r"\bUTILS_StyleRepens\b")


def _first_party(path: Path) -> bool:
    rel = path.relative_to(NOETHYS)
    return not any(part in EXCLUS for part in rel.parts)


def _ui_layer(path: Path) -> bool:
    rel = path.relative_to(NOETHYS)
    return bool(rel.parts) and rel.parts[0] in UI_LAYERS


def _repens_coverage(files: list[tuple[Path, list[str]]]) -> dict:
    legacy_files = set()
    repens_files = set()

    for path, lines in files:
        if not _ui_layer(path):
            continue
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        text = "\n".join(lines)
        if REPENS_IMPORT.search(text):
            repens_files.add(rel)
        if any(LEGACY_STYLE_IMPORT.search(line) for line in lines):
            legacy_files.add(rel)

    declared = legacy_files | repens_files
    clean_repens = repens_files - legacy_files
    mixed = repens_files & legacy_files
    legacy_only = legacy_files - repens_files

    def pct(value: int, total: int) -> float:
        return round((100.0 * value / total), 1) if total else 100.0

    return {
        "declared_style_files": len(declared),
        "repens_files": len(repens_files),
        "clean_repens_files": len(clean_repens),
        "mixed_files": len(mixed),
        "legacy_only_files": len(legacy_only),
        "repens_present_pct": pct(len(repens_files), len(declared)),
        "repens_clean_pct": pct(len(clean_repens), len(declared)),
        "mixed": sorted(mixed),
        "legacy_only": sorted(legacy_only),
    }


def _scan_with_session():
    paths = [path for path in sorted(NOETHYS.rglob("*.py")) if _first_party(path)]
    session = SourceAuditSession(paths)
    findings = []
    files = []

    for path in session.paths:
        loaded = session.parse(path)
        if loaded is None:
            continue
        source, _tree = loaded
        lines = source.splitlines()
        files.append((path, lines))
        rel = str(path.relative_to(ROOT)).replace("\\", "/")

        legacy_style_reported = False
        for lineno, raw in enumerate(lines, 1):
            code = raw.split("#", 1)[0]
            if not code.strip():
                continue

            if _ui_layer(path) and not legacy_style_reported and LEGACY_STYLE_IMPORT.search(code):
                findings.append({
                    "kind": "legacy_style_dependency",
                    "file": rel,
                    "line": lineno,
                    "snippet": code.strip()[:180],
                })
                legacy_style_reported = True

            for kind, pattern in PATTERNS.items():
                if pattern.search(code):
                    findings.append({
                        "kind": kind,
                        "file": rel,
                        "line": lineno,
                        "snippet": code.strip()[:180],
                    })

    return findings, _repens_coverage(files), session


def scan() -> tuple[list[dict], dict]:
    findings, repens, session = _scan_with_session()
    session.require_complete()
    return findings, repens


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path)
    parser.add_argument(
        "--fail-on",
        action="append",
        default=[],
        help="catégorie qui doit faire échouer l'audit si encore présente",
    )
    parser.add_argument(
        "--min-repens-clean",
        type=float,
        default=None,
        metavar="PCT",
        help="fait échouer l'audit si la couverture Repens exclusive est inférieure à ce pourcentage",
    )
    args = parser.parse_args()

    findings, repens, session = _scan_with_session()
    session.report(prefix="Couverture audit dette UI/layout")
    session.require_complete()
    counts = Counter(item["kind"] for item in findings)
    all_kinds = set(PATTERNS) | {"legacy_style_dependency"}

    print("Audit dette UI/layout")
    print("=====================")
    print("Occurrences : %d" % len(findings))
    for kind in sorted(all_kinds):
        print("  %-26s %d" % (kind + ":", counts.get(kind, 0)))

    print("\nCouverture Repens")
    print("=================")
    print("Fichiers UI avec dépendance de style : %d" % repens["declared_style_files"])
    print("Repens présent                       : %d (%.1f %%)" % (repens["repens_files"], repens["repens_present_pct"]))
    print("Repens exclusif                      : %d (%.1f %%)" % (repens["clean_repens_files"], repens["repens_clean_pct"]))
    print("Mixtes Repens + ancien socle         : %d" % repens["mixed_files"])
    print("Ancien socle uniquement              : %d" % repens["legacy_only_files"])

    hotspots = Counter(item["file"] for item in findings)
    print("\nFichiers prioritaires :")
    for filename, count in hotspots.most_common(20):
        print("  %4d  %s" % (count, filename))

    if repens["mixed"]:
        print("\nFichiers mixtes à terminer :")
        for filename in repens["mixed"][:20]:
            print("  %s" % filename)

    if repens["legacy_only"]:
        print("\nFichiers encore uniquement sur l'ancien socle :")
        for filename in repens["legacy_only"][:20]:
            print("  %s" % filename)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {"counts": dict(counts), "repens": repens, "findings": findings},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    categories_bloquantes = set(args.fail_on)
    inconnues = categories_bloquantes.difference(all_kinds)
    if inconnues:
        print("\nCatégorie(s) inconnue(s) : %s" % ", ".join(sorted(inconnues)))
        return 2

    if any(counts.get(kind, 0) for kind in categories_bloquantes):
        print("\nDette UI bloquante encore présente : %s" % ", ".join(sorted(categories_bloquantes)))
        return 1

    if args.min_repens_clean is not None:
        seuil = max(0.0, min(100.0, args.min_repens_clean))
        if repens["repens_clean_pct"] < seuil:
            print(
                "\nCouverture Repens exclusive insuffisante : %.1f %% < %.1f %%"
                % (repens["repens_clean_pct"], seuil)
            )
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
