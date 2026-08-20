#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
from pathlib import Path


def _read(path):
    root = Path(__file__).resolve().parents[1]
    texte = (root / path).read_text(encoding="utf-8")
    ast.parse(texte)
    return texte


def test_mail_module_is_disabled_by_default():
    texte = _read("noethys/Utils/UTILS_Modules.py")
    assert '"messagerie"' in texte
    assert '"defaut": False' in texte
    assert '"module_messagerie_actif"' in texte


def test_mail_panel_uses_splitters_not_fixed_multisplitter():
    texte = _read("noethys/Ctrl/CTRL_Messagerie.py")
    assert "wx.SplitterWindow" in texte
    assert "MultiSplitterWindow" not in texte
    assert ".Float()" not in texte
    assert "SetSashGravity" in texte


def test_mail_panel_does_not_connect_on_import():
    texte = _read("noethys/Ctrl/CTRL_Messagerie.py")
    assert "imaplib" not in texte
    assert "smtplib" not in texte
    assert "urlopen" not in texte
