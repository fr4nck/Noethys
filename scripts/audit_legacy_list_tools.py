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
SOURCE_HISTORIQUE = "Ctrl/CTRL_ObjectListView.py"
CODES_ECRAN = {
    "ctrl_outils_historique",
    "barre_recherche_historique",
    "import_ctrl_outils_historique",
}


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


def _est_source_historique(path: Path, root: Path) -> bool:
    try:
        relatif = path.relative_to(root).as_posix()
    except ValueError:
        relatif = path.as_posix()
    return relatif == SOURCE_HISTORIQUE or relatif.endswith("/" + SOURCE_HISTORIQUE)


def scan(root: Path) -> list[dict[str, object]]:
    findings = []
    for path in sorted(root.rglob("*.py")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        items = scan_file(path)
        if _est_source_historique(path, root):
            # La définition historique n'est pas un écran restant à migrer.
            # On ne conserve ici que ses anciens assets afin de matérialiser le
            # dernier raccord central encore à retirer une fois les appels partis.
            items = [item for item in items if item["code"] == "assets_filtre_16px"]
        findings.extend(items)
    return findings


def summarize(findings: list[dict[str, object]]) -> dict[str, int]:
    counts = {code: 0 for code in PATTERNS}
    for item in findings:
        counts[str(item["code"])] += 1
    return counts


def screens(findings: list[dict[str, object]]) -> list[str]:
    """Retourne les écrans encore raccordés aux anciens outils, sans doublons."""
    return sorted({
        str(item["path"])
        for item in findings
        if item["code"] in CODES_ECRAN
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="noethys")
    parser.add_argument("--json", dest="json_path", default=None)
    args = parser.parse_args()

    root = Path(args.root)
    findings = scan(root)
    counts = summarize(findings)
    legacy_screens = screens(findings)

    for item in findings:
        print(
            "{code} {path}:{line}: {text}".format(**item)
        )

    print("\nDette outils de listes :")
    for code in PATTERNS:
        print(f"- {code}: {counts[code]}")
    print(f"- ecrans_metier_restants: {len(legacy_screens)}")

    if args.json_path:
        output = Path(args.json_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                {
                    "summary": counts,
                    "screens": legacy_screens,
                    "findings": findings,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
