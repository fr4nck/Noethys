#!/usr/bin/env python3
"""Vérifie statiquement les imports locaux des modules métier critiques.

Le contrôle ne charge ni wxPython ni aucune base : il analyse l'AST et résout
les imports locaux uniquement à partir des chemins présents dans le dépôt.
La couverture des modules sélectionnés est bloquante.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

try:
    from scripts.audit_source_coverage import SourceAuditSession
except ModuleNotFoundError:
    from audit_source_coverage import SourceAuditSession

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "noethys").resolve()
KEYWORDS = (
    "famille", "individu", "inscription", "factur", "compta", "comptabil",
    "reglement", "prestation", "impression", "edition",
)
SKIP_DIRS = {".git", ".venv", "venv", "build", "dist", "__pycache__"}
LOCAL_PREFIXES = (
    "Ctrl.", "CTRL_", "Dlg.", "DLG_", "Ol.", "OL_", "Utils.", "UTILS_", "Data."
)


def is_target(path: Path) -> bool:
    name = path.stem.lower()
    return any(keyword in name for keyword in KEYWORDS)


def local_module_exists(name: str) -> bool:
    relative = Path(*name.split("."))
    return (
        (ROOT / f"{relative}.py").is_file()
        or (ROOT / relative / "__init__.py").is_file()
    )


def imported_modules_from_tree(tree: ast.AST) -> set[str]:
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            result.add(node.module)
    return result


def imported_modules(path: Path) -> set[str]:
    session = SourceAuditSession([path])
    loaded = session.parse(path)
    session.require_complete()
    assert loaded is not None
    _source, tree = loaded
    return imported_modules_from_tree(tree)


def main() -> int:
    targets = [
        path
        for path in sorted(ROOT.rglob("*.py"))
        if not any(part in SKIP_DIRS for part in path.parts) and is_target(path)
    ]
    if not targets:
        print("Aucun module métier critique détecté.")
        return 1

    session = SourceAuditSession(targets)
    failures: list[str] = []
    checked_imports = 0
    for path in session.paths:
        loaded = session.parse(path)
        if loaded is None:
            continue
        _source, tree = loaded
        for name in sorted(imported_modules_from_tree(tree)):
            if not name.startswith(LOCAL_PREFIXES):
                continue
            checked_imports += 1
            if not local_module_exists(name):
                failures.append(f"{path}: import local introuvable: {name}")

    print(f"{len(targets)} module(s) métier critique(s) trouvé(s).")
    print(f"{checked_imports} import(s) local(aux) vérifié(s).")
    session.report(prefix="Couverture audit modules métier critiques")
    if not session.coverage.complete:
        return 2

    if failures:
        print("\nAnomalies détectées :")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Graphe statique des modules métier critiques cohérent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
