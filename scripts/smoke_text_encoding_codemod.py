#!/usr/bin/env python3
"""Valide le codemod conservateur des ouvertures texte UTF-8."""
from __future__ import annotations

import ast
import importlib.util
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODEMOD = ROOT / "scripts" / "modernize_text_file_encodings.py"


def load_codemod():
    spec = importlib.util.spec_from_file_location("modernize_text_file_encodings", CODEMOD)
    if spec is None or spec.loader is None:
        raise ImportError(f"Impossible de charger {CODEMOD}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    codemod = load_codemod()
    source = '''\
texte = open("exemple accentué.json").read()
with open("sortie.csv", "w") as fichier:
    fichier.write("Élodie;Muñoz")
binaire = open("image.png", "rb").read()
chemin = "dynamique.txt"
dynamique = open(chemin, "r").read()
deja = open("deja.xml", "r", encoding="utf-8").read()
'''

    with tempfile.TemporaryDirectory(prefix="noethys-codemod-") as tmp:
        path = Path(tmp) / "fixture.py"
        path.write_text(source, encoding="utf-8", newline="")

        expected = [1, 2]
        detected = codemod.candidates(path)
        if detected != expected:
            raise RuntimeError(f"Candidats inattendus : {detected}, attendu : {expected}")

        changed = codemod.apply(path)
        if changed != 2:
            raise RuntimeError(f"Nombre de transformations inattendu : {changed}")

        updated = path.read_text(encoding="utf-8")
        ast.parse(updated, filename=str(path))

        if 'open("exemple accentué.json", encoding="utf-8")' not in updated:
            raise RuntimeError("Lecture texte implicite non modernisée")
        if 'open("sortie.csv", "w", encoding="utf-8")' not in updated:
            raise RuntimeError("Écriture texte explicite non modernisée")
        if 'open("image.png", "rb")' not in updated:
            raise RuntimeError("Ouverture binaire modifiée à tort")
        if 'open(chemin, "r")' not in updated:
            raise RuntimeError("Chemin dynamique modifié à tort")
        if updated.count('open("deja.xml", "r", encoding="utf-8")') != 1:
            raise RuntimeError("Encodage existant dupliqué")

        if codemod.candidates(path):
            raise RuntimeError("Le codemod n'est pas idempotent")

    print("Codemod UTF-8 conservateur valide et idempotent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
