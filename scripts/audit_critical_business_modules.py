#!/usr/bin/env python3
"""Vérifie statiquement le graphe des modules métier critiques de Noethys.

Le contrôle ne charge ni wxPython, ni base de données. Il cible les modules dont
le nom évoque les familles, individus, inscriptions, facturation, comptabilité
ou impressions, puis vérifie que leurs imports locaux absolus sont résolvables.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "noethys").resolve()
KEYWORDS = (
    "famille", "individu", "inscription", "factur", "compta", "comptabil",
    "reglement", "prestation", "impression", "edition",
)
SKIP_DIRS = {".git", ".venv", "venv", "build", "dist", "__pycache__"}
LOCAL_PREFIXES = ("Ctrl.", "CTRL_", "Dlg.", "DLG_", "Ol.", "OL_", "Utils.", "UTILS_", "Data.")


def is_target(path: Path) -> bool:
    name = path.stem.lower()
    return any(keyword in name for keyword in KEYWORDS)


def module_exists(name: str) -> bool:
    if importlib.util.find_spec(name) is not None:
        return True
    relative = Path(*name.split("."))
    return (ROOT / f"{relative}.py").is_file() or (ROOT / relative / "__init__.py").is_file()


def imported_modules(path: Path) -> set[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            result.add(node.module)
    return result


def main() -> int:
    sys.path.insert(0, str(ROOT))
    targets = [
        path for path in sorted(ROOT.rglob("*.py"))
        if not any(part in SKIP_DIRS for part in path.parts) and is_target(path)
    ]
    if not targets:
        print("Aucun module métier critique détecté.")
        return 1

    failures: list[str] = []
    checked_imports = 0
    for path in targets:
        try:
            imports = imported_modules(path)
        except (OSError, SyntaxError) as err:
            failures.append(f"{path}: analyse impossible: {err}")
            continue
        for name in sorted(imports):
            if not name.startswith(LOCAL_PREFIXES):
                continue
            checked_imports += 1
            if not module_exists(name):
                failures.append(f"{path}: import local introuvable: {name}")

    print(f"{len(targets)} module(s) métier critique(s) analysé(s).")
    print(f"{checked_imports} import(s) local(aux) vérifié(s).")
    if failures:
        print("\nAnomalies détectées :")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Graphe statique des modules métier critiques cohérent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
