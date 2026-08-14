"""Normalise les anciennes valeurs bytes envoyées aux contrôles texte wxPython.

Le code historique peut encore fournir des bytes encodés à des méthodes wx qui
attendent désormais du texte Unicode. Ce hook décode uniquement les arguments
d'interface ; il ne modifie ni les fichiers ni les données métier.
"""
from __future__ import annotations

import wx


def _to_text(value):
    if not isinstance(value, (bytes, bytearray, memoryview)):
        return value
    raw = bytes(value)
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _patch_method(cls, name):
    original = getattr(cls, name, None)
    if original is None or getattr(original, "__name__", "") == "_wx_text_compat":
        return

    def _wx_text_compat(self, value, *args, **kwargs):
        return original(self, _to_text(value), *args, **kwargs)

    _wx_text_compat.__name__ = "_wx_text_compat"
    setattr(cls, name, _wx_text_compat)


for klass, methods in (
    (wx.TextCtrl, ("SetValue", "ChangeValue", "AppendText", "WriteText")),
    (wx.StaticText, ("SetLabel",)),
    (wx.Button, ("SetLabel",)),
    (wx.CheckBox, ("SetLabel",)),
    (wx.RadioButton, ("SetLabel",)),
):
    for method in methods:
        _patch_method(klass, method)
