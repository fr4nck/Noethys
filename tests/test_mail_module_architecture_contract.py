#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path


def test_mail_module_stays_optional_by_design():
    root = Path(__file__).resolve().parents[1]
    texte = (root / "docs" / "MAIL_MODULE_ARCHITECTURE.md").read_text(encoding="utf-8")

    assert "désactivé par défaut" in texte
    assert "pas de connexion réseau" in texte
    assert "Réception IMAP" in texte
    assert "familles" in texte and "collectivités/mairies" in texte
