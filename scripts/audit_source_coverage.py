#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contrat commun de lecture/parsing pour les audits statiques Noethys.

Un audit ne peut pas conclure à "zéro occurrence" si un fichier Python de son
périmètre n'a pas été lu et parsé. Ce module fournit :

- une lecture respectant l'encodage Python déclaré (PEP 263 / BOM) via
  :func:`tokenize.open` ;
- un comptage explicite ``trouvés == lus == parsés`` ;
- la conservation de chaque erreur de lecture ou de syntaxe ;
- un code de sortie non nul dès qu'un fichier échappe à l'analyse.

Les occurrences détectées par les audits restent des diagnostics. En revanche,
la couverture de l'audit est un contrat bloquant.
"""
from __future__ import annotations

import argparse
import ast
import tokenize
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "build", "dist"}


@dataclass(frozen=True)
class SourceFailure:
    path: Path
    stage: str
    error_type: str
    message: str

    def format(self) -> str:
        return f"{self.path}: {self.stage}: {self.error_type}: {self.message}"


@dataclass
class SourceCoverage:
    found: int = 0
    read: int = 0
    parsed: int = 0
    failures: list[SourceFailure] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return (
            not self.failures
            and self.found == self.read == self.parsed
        )

    def summary(self) -> str:
        status = "OK" if self.complete else "ECHEC"
        return (
            f"Couverture sources: trouvés={self.found}, lus={self.read}, "
            f"parsés={self.parsed} — {status}"
        )


class SourceAuditSession:
    """Charge un ensemble figé de fichiers et mesure leur couverture réelle."""

    def __init__(self, paths: Iterable[Path]):
        self.paths = tuple(sorted(Path(path) for path in paths))
        self.coverage = SourceCoverage(found=len(self.paths))

    def parse(self, path: Path) -> tuple[str, ast.AST] | None:
        path = Path(path)
        try:
            with tokenize.open(path) as stream:
                source = stream.read()
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            self.coverage.failures.append(
                SourceFailure(path, "lecture", type(exc).__name__, str(exc))
            )
            return None

        self.coverage.read += 1

        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            detail = exc.msg
            if exc.lineno is not None:
                detail = f"ligne {exc.lineno}: {detail}"
            self.coverage.failures.append(
                SourceFailure(path, "parsing", type(exc).__name__, detail)
            )
            return None

        self.coverage.parsed += 1
        return source, tree

    def report(self, *, prefix: str = "") -> bool:
        if prefix:
            print(prefix)
        print(self.coverage.summary())
        for failure in self.coverage.failures:
            print(f"ERREUR AUDIT: {failure.format()}")
        return self.coverage.complete


def iter_python_files(root: Path, *, skip_dirs: set[str] | None = None):
    excluded = SKIP_DIRS if skip_dirs is None else set(skip_dirs)
    for path in sorted(Path(root).rglob("*.py")):
        if any(part in excluded for part in path.parts):
            continue
        yield path


def check_tree(root: Path) -> SourceCoverage:
    session = SourceAuditSession(iter_python_files(root))
    for path in session.paths:
        session.parse(path)
    return session.coverage


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Vérifie que tous les fichiers Python d'un périmètre sont lisibles et parsables"
    )
    parser.add_argument("root", nargs="?", default="noethys", type=Path)
    args = parser.parse_args()

    session = SourceAuditSession(iter_python_files(args.root))
    for path in session.paths:
        session.parse(path)

    return 0 if session.report(prefix="Contrat de couverture des audits statiques") else 2


if __name__ == "__main__":
    raise SystemExit(main())
