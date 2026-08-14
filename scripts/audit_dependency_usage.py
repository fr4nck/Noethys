#!/usr/bin/env python3
"""Inventorie les imports externes réellement utilisés par Noethys.

Le script utilise uniquement la bibliothèque standard. Il compare les imports
trouvés dans ``noethys/`` avec ``requirements.txt`` et signale les dépendances
potentiellement absentes ou inutilisées. Le résultat est informatif.

Les modules internes sont détectés récursivement afin de tenir compte des anciens
imports "à plat" de Noethys (par exemple CellEditor, OLVEvent, wxSchedule...).
"""
from __future__ import annotations

import ast
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys"
REQUIREMENTS = ROOT / "requirements.txt"
BUILD_REQUIREMENTS = ROOT / "requirements-build.txt"
SKIP_DIRS = {".git", "build", "dist", "__pycache__", "venv", ".venv"}

# Correspondance nom PyPI -> racine de module importée.
DIST_TO_MODULE = {
    "pillow": "PIL",
    "python-dateutil": "dateutil",
    "mysqlclient": "MySQLdb",
    "mysql-connector-python": "mysql",
    "opencv-python": "cv2",
    "pycryptodome": "Crypto",
    "xlsxwriter": "xlsxwriter",
    "sqlalchemy": "sqlalchemy",
    "wxpython": "wx",
    "twisted": "twisted",
    "pyserial": "serial",
    "pyscard": "smartcard",
    "mailjet-rest": "mailjet_rest",
}


def iter_python_files(root: Path):
    for path in root.rglob("*.py"):
        if not any(part in SKIP_DIRS for part in path.parts):
            yield path


def imported_roots(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
    except (OSError, SyntaxError):
        return set()
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def requirement_modules(path: Path) -> dict[str, str]:
    modules: dict[str, str] = {}
    if not path.exists():
        return modules
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        dist = re.split(r"[<>=!~\[]", line, maxsplit=1)[0].strip()
        key = dist.lower().replace("_", "-")
        modules[dist] = DIST_TO_MODULE.get(key, dist.replace("-", "_"))
    return modules


def local_module_names() -> set[str]:
    names: set[str] = set()
    for path in iter_python_files(SOURCE):
        names.add(path.stem)
    for path in SOURCE.rglob("*"):
        if path.is_dir() and not any(part in SKIP_DIRS for part in path.parts):
            names.add(path.name)
    return names


def main() -> int:
    counts: Counter[str] = Counter()
    for path in iter_python_files(SOURCE):
        counts.update(imported_roots(path))

    local_modules = local_module_names()
    stdlib = set(getattr(sys, "stdlib_module_names", ()))

    external = {
        name for name in counts
        if name not in stdlib and name not in local_modules and not name.startswith("noethys")
    }

    runtime_declared = requirement_modules(REQUIREMENTS)
    build_declared = requirement_modules(BUILD_REQUIREMENTS)
    declared = {**runtime_declared, **build_declared}
    declared_modules = set(declared.values())

    print("Imports externes détectés")
    for name in sorted(external):
        print(f"- {name}: {counts[name]}")

    print("\nDépendances déclarées mais non détectées directement")
    for dist, module in sorted(runtime_declared.items()):
        if module not in external:
            print(f"- {dist} (module {module})")

    print("\nImports externes sans dépendance déclarée évidente")
    missing = sorted(external - declared_modules)
    for name in missing:
        print(f"- {name}")

    print(f"\nRésumé: {len(external)} module(s) externe(s), {len(missing)} sans déclaration évidente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
