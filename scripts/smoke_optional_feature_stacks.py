#!/usr/bin/env python3
"""Vérifie les piles fonctionnelles chargées tardivement par Noethys.

Le test n'ouvre ni interface ni base. Il importe seulement les sous-modules
utilisés pour les impressions, graphiques, échanges réseau et XML afin de
bloquer avant PyInstaller si une pile critique est incomplète.
"""
from __future__ import annotations

import importlib
import sys

STACKS = {
    "PDF / impression": (
        "reportlab.pdfgen.canvas",
        "reportlab.platypus",
        "reportlab.lib.pagesizes",
        "reportlab.pdfbase.ttfonts",
    ),
    "Graphiques": (
        "matplotlib",
        "matplotlib.figure",
        "matplotlib.backends.backend_agg",
    ),
    "Chiffrement": (
        "Crypto.Hash.SHA256",
        "Crypto.Cipher.AES",
        "Crypto.Random",
    ),
    "SSH / SFTP": (
        "paramiko",
        "paramiko.client",
        "paramiko.sftp_client",
    ),
    "XML / HTML": (
        "lxml.etree",
        "lxml.html",
    ),
    "Réseau asynchrone": (
        "twisted.internet",
        "twisted.web.client",
    ),
}


def main() -> int:
    failures = 0
    for label, modules in STACKS.items():
        print(f"\n{label}")
        for module_name in modules:
            try:
                importlib.import_module(module_name)
            except Exception as err:
                failures += 1
                print(f"- {module_name}: {type(err).__name__}: {err}")
            else:
                print(f"- {module_name}: ok")

    if failures:
        print(f"\n{failures} sous-module(s) fonctionnel(s) indisponible(s).", file=sys.stderr)
        return 1
    print("\nToutes les piles fonctionnelles critiques sont importables.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
