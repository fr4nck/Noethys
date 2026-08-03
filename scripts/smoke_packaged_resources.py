#!/usr/bin/env python3
"""Vérifie les ressources indispensables et leur destination PyInstaller.

Ce contrôle ne construit pas l'exécutable. Il garantit que les fichiers attendus
par Chemins.py existent dans les sources et que le spec les place à la racine du
dossier portable, à côté de Noethys.exe.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
SPEC = ROOT / "packaging" / "noethys.spec"

REQUIRED = (
    NOETHYS / "Static",
    NOETHYS / "Versions.txt",
    NOETHYS / "Licence.txt",
    NOETHYS / "Icone.ico",
)

EXPECTED_DESTINATIONS = {
    "Static": "Static",
    "Versions.txt": ".",
    "Licence.txt": ".",
    "Icone.ico": ".",
}


def parse_data_destinations() -> dict[str, str]:
    tree = ast.parse(SPEC.read_text(encoding="utf-8"), filename=str(SPEC))
    destinations: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "datas" for target in node.targets):
            continue
        if not isinstance(node.value, ast.List):
            continue
        for element in node.value.elts:
            if not isinstance(element, ast.Tuple) or len(element.elts) != 2:
                continue
            source, destination = element.elts
            if not isinstance(destination, ast.Constant) or not isinstance(destination.value, str):
                continue
            source_text = ast.unparse(source)
            for name in EXPECTED_DESTINATIONS:
                if repr(name) in source_text or f'"{name}"' in source_text:
                    destinations[name] = destination.value
    return destinations


def main() -> int:
    failures: list[str] = []
    for path in REQUIRED:
        if not path.exists():
            failures.append(f"ressource absente : {path.relative_to(ROOT)}")

    destinations = parse_data_destinations()
    for name, expected in EXPECTED_DESTINATIONS.items():
        actual = destinations.get(name)
        if actual != expected:
            failures.append(
                f"destination incorrecte pour {name}: {actual!r}, attendu {expected!r}"
            )

    if failures:
        for failure in failures:
            print(f"ERREUR: {failure}")
        return 1

    print("Ressources principales présentes et correctement positionnées.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
