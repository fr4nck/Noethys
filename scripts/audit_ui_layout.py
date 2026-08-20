#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventorie la dette de layout wxPython à éliminer pendant la refonte UI.

L'audit ne modifie rien et n'échoue pas par défaut. Il sert de liste de travail
exhaustive : tailles figées, toolbars dimensionnées localement, double-clics de
grille fragiles et combinaisons de flags connues pour produire des layouts
bloqués. L'objectif est de faire diminuer ces compteurs à mesure que les
composants communs remplacent les géométries historiques.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
EXCLUS = {"ObjectListView", "Outils", "__pycache__"}

PATTERNS = {
    "toolbar_bitmap_fixed": re.compile(r"SetToolBitmapSize\s*\(\s*(?:wx\.Size\s*\()?\s*\(?\s*(?:16|20|24|32|40|48)\s*,"),
    "aui_pane_fixed_size": re.compile(r"\.(?:MinSize|BestSize)\s*\(\s*\(\s*-?\d+\s*,\s*-?\d+"),
    "window_fixed_min_size": re.compile(r"\.SetMinSize\s*\(\s*\(\s*-?\d+\s*,\s*-?\d+"),
    "align_expand_conflict": re.compile(r"wx\.ALIGN_(?:CENTER|CENTRE)_VERTICAL\s*\|\s*wx\.EXPAND|wx\.EXPAND\s*\|\s*wx\.ALIGN_(?:CENTER|CENTRE)_VERTICAL"),
    "raw_grid_double_click": re.compile(r"GetGridWindow\(\)\.Bind\(wx\.EVT_LEFT_DCLICK"),
    "fixed_grid_column": re.compile(r"\.SetColSize\s*\([^,]+,\s*\d+\s*\)"),
    "legacy_grid_lines": re.compile(r"wx\.LC_HRULES\s*\|\s*wx\.LC_VRULES|wx\.LC_VRULES\s*\|\s*wx\.LC_HRULES"),
    "hardcoded_colour_role": re.compile(r"(?:SetBackgroundColour|SetForegroundColour|SetCellBackgroundColour)\s*\(\s*(?:wx\.)?Colour\s*\("),
}


def _first_party(path: Path) -> bool:
    rel = path.relative_to(NOETHYS)
    return not any(part in EXCLUS for part in rel.parts)


def scan() -> list[dict]:
    findings = []
    for path in sorted(NOETHYS.rglob("*.py")):
        if not _first_party(path):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        for lineno, raw in enumerate(lines, 1):
            code = raw.split("#", 1)[0]
            if not code.strip():
                continue
            for kind, pattern in PATTERNS.items():
                if pattern.search(code):
                    findings.append({
                        "kind": kind,
                        "file": rel,
                        "line": lineno,
                        "snippet": code.strip()[:180],
                    })
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path)
    parser.add_argument("--fail-on", action="append", default=[], help="catégorie qui doit faire échouer l'audit si encore présente")
    args = parser.parse_args()

    findings = scan()
    counts = Counter(item["kind"] for item in findings)

    print("Audit dette UI/layout")
    print("=====================")
    print("Occurrences : %d" % len(findings))
    for kind in sorted(PATTERNS):
        print("  %-26s %d" % (kind + ":", counts.get(kind, 0)))

    hotspots = Counter(item["file"] for item in findings)
    print("\nFichiers prioritaires :")
    for filename, count in hotspots.most_common(20):
        print("  %4d  %s" % (count, filename))

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps({"counts": dict(counts), "findings": findings}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    categories_bloquantes = set(args.fail_on)
    inconnues = categories_bloquantes.difference(PATTERNS)
    if inconnues:
        print("\nCatégorie(s) inconnue(s) : %s" % ", ".join(sorted(inconnues)))
        return 2

    if any(counts.get(kind, 0) for kind in categories_bloquantes):
        print("\nDette UI bloquante encore présente : %s" % ", ".join(sorted(categories_bloquantes)))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
