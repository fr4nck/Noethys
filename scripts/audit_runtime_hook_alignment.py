#!/usr/bin/env python3
"""Vérifie l'alignement entre les hooks runtime et les fichiers PyInstaller.

Le contrôle parcourt tous les ``*.spec`` du dépôt, extrait les chemins déclarés
dans ``runtime_hooks`` puis les compare aux fichiers ``runtime_*.py`` présents
dans ``packaging``. Il signale :

- les hooks déclarés mais absents ;
- les hooks présents mais jamais référencés ;
- les hooks déclarés plusieurs fois dans un même spec ;
- l'absence totale de fichier spec ou de déclaration runtime_hooks.

Le contrôle est informatif : un hook non référencé peut être un outil conservé
volontairement pour une variante de packaging.
"""
from __future__ import annotations

import ast
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
SKIP_DIRS = {".git", ".venv", "venv", "build", "dist", "__pycache__"}


def iter_files(pattern: str):
    for path in ROOT.rglob(pattern):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def literal_strings(node: ast.AST) -> list[str]:
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values: list[str] = []
        for item in node.elts:
            if isinstance(item, ast.Constant) and isinstance(item.value, str):
                values.append(item.value)
        return values
    return []


def hooks_from_spec(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return []

    hooks: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg == "runtime_hooks":
                hooks.extend(literal_strings(keyword.value))
    return hooks


def normalize(path: str, spec: Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = spec.parent / candidate
    return candidate.resolve()


def main() -> int:
    specs = sorted(iter_files("*.spec"))
    runtime_files = {
        path.resolve()
        for path in iter_files("runtime_*.py")
        if "packaging" in path.parts
    }

    findings: list[str] = []
    referenced: set[Path] = set()

    if not specs:
        findings.append("aucun fichier .spec trouvé")

    for spec in specs:
        hooks = hooks_from_spec(spec)
        if not hooks:
            findings.append(f"{spec.relative_to(ROOT)}: aucune déclaration runtime_hooks littérale")
            continue

        counts = Counter(hooks)
        for hook, count in counts.items():
            normalized = normalize(hook, spec)
            referenced.add(normalized)
            if count > 1:
                findings.append(
                    f"{spec.relative_to(ROOT)}: hook déclaré {count} fois : {hook}"
                )
            if not normalized.is_file():
                findings.append(
                    f"{spec.relative_to(ROOT)}: hook déclaré mais absent : {hook}"
                )

    for runtime_file in sorted(runtime_files - referenced):
        findings.append(
            f"{runtime_file.relative_to(ROOT)}: hook présent mais non référencé par un .spec"
        )

    if findings:
        for finding in findings:
            print(finding)
        print(f"\n{len(findings)} anomalie(s) d'alignement des hooks runtime.")
        return 1

    print(
        f"Alignement vérifié : {len(specs)} spec(s), "
        f"{len(runtime_files)} hook(s) runtime référencé(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
