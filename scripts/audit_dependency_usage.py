#!/usr/bin/env python3
"""Inventorie les imports externes réellement utilisés par Noethys.

Le résultat fonctionnel reste informatif. En revanche, la couverture des
fichiers Python est bloquante : aucun fichier non lu ou non parsé ne peut être
assimilé à une absence d'import.
"""
from __future__ import annotations

import ast
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    from scripts.audit_source_coverage import SourceAuditSession, iter_python_files
except ModuleNotFoundError:
    from audit_source_coverage import SourceAuditSession, iter_python_files

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "noethys"
REQUIREMENTS = ROOT / "requirements.txt"
BUILD_REQUIREMENTS = ROOT / "requirements-build.txt"
SKIP_DIRS = {".git", "build", "dist", "__pycache__", "venv", ".venv"}

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
    "pywin32": "win32com",
}


def imported_roots(tree: ast.AST) -> set[str]:
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
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        dist = re.split(r"[<>=!~\[;]", line, maxsplit=1)[0].strip()
        key = dist.lower().replace("_", "-")
        modules[dist] = DIST_TO_MODULE.get(key, dist.replace("-", "_"))
    return modules


def local_module_names(paths: tuple[Path, ...]) -> set[str]:
    names: set[str] = {path.stem for path in paths}
    for path in SOURCE.rglob("*"):
        if path.is_dir() and not any(part in SKIP_DIRS for part in path.parts):
            names.add(path.name)
    return names


def main() -> int:
    paths = tuple(iter_python_files(SOURCE, skip_dirs=SKIP_DIRS))
    session = SourceAuditSession(paths)
    counts: Counter[str] = Counter()
    locations: dict[str, set[str]] = defaultdict(set)

    for path in session.paths:
        loaded = session.parse(path)
        if loaded is None:
            continue
        _source, tree = loaded
        roots = imported_roots(tree)
        counts.update(roots)
        relative = str(path.relative_to(ROOT))
        for name in roots:
            locations[name].add(relative)

    local_modules = local_module_names(paths)
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
        files = ", ".join(sorted(locations[name]))
        print(f"- {name}: {files}")

    print(f"\nRésumé: {len(external)} module(s) externe(s), {len(missing)} sans déclaration évidente.")
    if not session.report():
        print("Audit incomplet : inventaire des dépendances non exhaustif.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
