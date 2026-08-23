#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inventorie les raccords encore dépendants des outils de listes historiques.

L'objectif n'est pas de faire échouer la CI : ce script fournit une dette
mesurable pour terminer la migration Repens écran par écran sans chercher des
usages à la main.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PATTERNS = {
    "ctrl_outils_historique": re.compile(r"\bCTRL_ObjectListView\.CTRL_Outils\b"),
    "barre_recherche_historique": re.compile(r"\bCTRL_ObjectListView\.BarreRecherche\b"),
    "import_ctrl_outils_historique": re.compile(
        r"from\s+Ctrl\.CTRL_ObjectListView\s+import\s+[^\n]*(?:CTRL_Outils|BarreRecherche)"
    ),
    "assets_filtre_16px": re.compile(
        r"Images/16x16/(?:Filtre(?:_[0-9]+|_supprimer)?|Cocher|Decocher)\.png"
    ),
}

SKIP_DIRS = {".git", "build", "dist", "__pycache__", ".venv", "venv"}


def scan_file(path: Path) -> list[dict[str, object]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    findings = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for code, pattern in PATTERNS.items():
            if pattern.search(line):
                findings.append({
                    "code": code,
                    "path": path.as_posix(),
                    "line": lineno,
                    "text": line.strip(),
                })
    return findings


def scan(root: Path) -> list[dict[str, object]]:
    findings = []
    for path in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        # Le module historique lui-même est la source à remplacer, pas un écran
        # métier restant à migrer. Les assets qu'il contient sont néanmoins
        # comptés séparément afin de matérialiser le dernier raccord central.
        findings.extend(scan_file(path))
    return findings


def summarize(findings: list[dict[str, object]]) -> dict[str, int]:
    counts = {code: 0 for code in PATTERNS}
    for item in findings:
        counts[str(item["code"])] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="noethys")
    parser.add_argument("--json", dest="json_path", default=None)
    args = parser.parse_args()

    root = Path(args.root)
    findings = scan(root)
    counts = summarize(findings)

    for item in findings:
        print(
            "{code} {path}:{line}: {text}".format(**item)
        )

    print("\nDette outils de listes :")
    for code in PATTERNS:
        print(f"- {code}: {counts[code]}")

    if args.json_path:
        output = Path(args.json_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                {"summary": counts, "findings": findings},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
