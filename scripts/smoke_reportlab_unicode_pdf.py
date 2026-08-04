#!/usr/bin/env python3
"""Vérifie la génération PDF ReportLab avec chemin et texte Unicode."""
from __future__ import annotations

import tempfile
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def main() -> int:
    texte = "Élodie Drouillé — José Muñoz — Łukasz — Ægir"
    with tempfile.TemporaryDirectory(prefix="noethys-pdf-é") as tmp:
        pdf_path = Path(tmp) / "aperçu été — test.pdf"
        document = canvas.Canvas(str(pdf_path), pagesize=A4)
        document.setTitle("Noethys — aperçu Unicode")
        document.drawString(72, 800, texte)
        document.save()

        contenu = pdf_path.read_bytes()
        if not contenu.startswith(b"%PDF-"):
            raise AssertionError("Le fichier généré n'est pas un PDF valide")
        if len(contenu) < 500:
            raise AssertionError("Le PDF généré est anormalement vide")

    print("Génération ReportLab Unicode validée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
