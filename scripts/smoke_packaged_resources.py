#!/usr/bin/env python3
"""Vérifie les ressources essentielles attendues dans le bundle PyInstaller."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
SPEC = ROOT / "packaging" / "noethys.spec"

REQUIRED = {
    "Static": (NOETHYS / "Static", "Static"),
    "Versions.txt": (NOETHYS / "Versions.txt", "."),
    "Licence.txt": (NOETHYS / "Licence.txt", "."),
    "Icone.ico": (NOETHYS / "Icone.ico", "."),
}


def extract_literal_data_destinations(tree: ast.Module) -> dict[str, str]:
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
            for name in REQUIRED:
                if repr(name) in source_text or f'"{name}"' in source_text:
                    destinations[name] = destination.value
    return destinations


def main() -> int:
    failures: list[str] = []
    for name, (source, _) in REQUIRED.items():
        if not source.exists():
            failures.append(f"ressource absente : {source.relative_to(ROOT)}")

    tree = ast.parse(SPEC.read_text(encoding="utf-8"), filename=str(SPEC))
    destinations = extract_literal_data_destinations(tree)
    for name, (_, expected_destination) in REQUIRED.items():
        actual = destinations.get(name)
        if actual != expected_destination:
            failures.append(f"destination incorrecte pour {name}: {actual!r}, attendu {expected_destination!r}")

    spec_text = SPEC.read_text(encoding="utf-8")
    if 'NOETHYS = ROOT / "noethys"' not in spec_text:
        failures.append("la spec ne définit pas NOETHYS depuis ROOT")
    if 'ROOT = Path(SPECPATH).resolve().parent' not in spec_text:
        failures.append("la spec ne dérive pas ROOT du dossier contenant la spec")

    if failures:
        for failure in failures:
            print(f"ERREUR: {failure}")
        return 1
    print("Ressources PyInstaller essentielles et destinations validées.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
