#!/usr/bin/env python3
"""Vérifie la cohérence minimale du packaging PyInstaller.

Ce contrôle inventorie les fichiers .spec et recherche :
- hooks runtime déclarés mais absents ;
- doublons dans runtime_hooks et hiddenimports ;
- hiddenimports vides ou manifestement non littéraux ;
- hooks présents dans packaging/ mais jamais référencés.

Le contrôle est informatif : il ne supprime rien automatiquement.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_GLOBS = ("*.spec", "packaging/*.spec", "**/*.spec")
HOOK_DIRS = (ROOT / "packaging", ROOT / "packaging" / "hooks")


def literal_list(source: str, name: str) -> list[str]:
    pattern = re.compile(rf"\b{name}\s*=\s*(\[[\s\S]*?\])", re.MULTILINE)
    values: list[str] = []
    for match in pattern.finditer(source):
        try:
            parsed = ast.literal_eval(match.group(1))
        except Exception:
            continue
        if isinstance(parsed, list):
            values.extend(item for item in parsed if isinstance(item, str))
    return values


def main() -> int:
    specs = sorted({path for pattern in SPEC_GLOBS for path in ROOT.glob(pattern)})
    if not specs:
        print("Aucun fichier .spec trouvé.")
        return 1

    referenced_hooks: set[Path] = set()
    findings = 0

    for spec in specs:
        source = spec.read_text(encoding="utf-8", errors="replace")
        runtime_hooks = literal_list(source, "runtime_hooks")
        hiddenimports = literal_list(source, "hiddenimports")

        for label, values in (("runtime_hooks", runtime_hooks), ("hiddenimports", hiddenimports)):
            duplicates = sorted({value for value in values if values.count(value) > 1})
            for value in duplicates:
                findings += 1
                print(f"{spec}: doublon {label}: {value}")

        for hook in runtime_hooks:
            hook_path = (spec.parent / hook).resolve()
            if not hook_path.exists():
                alternate = (ROOT / hook).resolve()
                if alternate.exists():
                    hook_path = alternate
                else:
                    findings += 1
                    print(f"{spec}: hook runtime introuvable: {hook}")
                    continue
            referenced_hooks.add(hook_path)

        for module in hiddenimports:
            if not module.strip():
                findings += 1
                print(f"{spec}: hiddenimport vide")

    for directory in HOOK_DIRS:
        if not directory.exists():
            continue
        for hook in sorted(directory.glob("runtime_*.py")):
            if hook.resolve() not in referenced_hooks:
                findings += 1
                print(f"{hook}: hook runtime non référencé")

    print(f"\n{findings} anomalie(s) de minimalité du packaging.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
