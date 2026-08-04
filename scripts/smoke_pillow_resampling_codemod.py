#!/usr/bin/env python3
"""Vérifie la sûreté et l'idempotence du codemod Pillow."""
from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "scripts" / "modernize_pillow_resampling.py"

spec = importlib.util.spec_from_file_location("modernize_pillow_resampling", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Impossible de charger le codemod Pillow")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

SOURCE = '''from PIL import Image

filters = (
    Image.NEAREST,
    Image.BILINEAR,
    Image.BICUBIC,
    Image.LANCZOS,
    Image.ANTIALIAS,
    Image.Resampling.LANCZOS,
)
image.resize((10, 10))
'''

EXPECTED = (
    "Image.Resampling.NEAREST",
    "Image.Resampling.BILINEAR",
    "Image.Resampling.BICUBIC",
    "Image.Resampling.LANCZOS",
)


def main() -> int:
    updated, changed = module.modernize_source(SOURCE)
    if changed != 5:
        raise AssertionError(f"Nombre de remplacements inattendu : {changed}")
    for token in EXPECTED:
        if token not in updated:
            raise AssertionError(f"Remplacement manquant : {token}")
    if "Image.ANTIALIAS" in updated:
        raise AssertionError("Image.ANTIALIAS est encore présent")
    if "image.resize((10, 10))" not in updated:
        raise AssertionError("Un resize sans filtre a été modifié")
    ast.parse(updated)

    second, second_changed = module.modernize_source(updated)
    if second_changed != 0 or second != updated:
        raise AssertionError("Le codemod Pillow n'est pas idempotent")

    print("Codemod Pillow : OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
