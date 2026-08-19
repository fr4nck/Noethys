#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke test GTK3/wxPython sous DISPLAY virtuel.

Le test construit une petite hiérarchie représentative de Noethys : frame,
panel, sizers, contrôles texte, bouton et liste. Il force un layout et un cycle
d'événements sans afficher d'interface à l'utilisateur ni ouvrir de base.
"""
import wx
from wx.lib.agw import ultimatelistctrl as ULC


app = wx.App(False)
print("wx :", wx.version())
print("plateforme :", wx.PlatformInfo)

assert "phoenix" in wx.PlatformInfo, "wxPython Phoenix attendu"
assert any(token in wx.PlatformInfo for token in ("wxGTK", "__WXGTK__")), "backend GTK attendu"

frame = wx.Frame(None, title="Noethys GTK3 smoke", size=(640, 420))
panel = wx.Panel(frame)

root = wx.BoxSizer(wx.VERTICAL)
header = wx.BoxSizer(wx.HORIZONTAL)
label = wx.StaticText(panel, label="Recherche")
search = wx.TextCtrl(panel, value="test")
button = wx.Button(panel, label="Actualiser")
header.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
header.Add(search, 1, wx.EXPAND | wx.RIGHT, 6)
header.Add(button, 0)
root.Add(header, 0, wx.EXPAND | wx.ALL, 8)

listctrl = ULC.UltimateListCtrl(
    panel,
    agwStyle=ULC.ULC_REPORT | ULC.ULC_SINGLE_SEL,
)
listctrl.InsertColumn(0, "Nom", width=220)
listctrl.InsertColumn(1, "Valeur", width=120)
idx = listctrl.InsertStringItem(0, "Ligne test")
listctrl.SetStringItem(idx, 1, "OK")
root.Add(listctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

panel.SetSizer(root)
frame.Layout()
frame.Show()
wx.Yield()

client = frame.GetClientSize()
assert client.width > 0 and client.height > 0
assert search.GetSize().width > 0
assert listctrl.GetSize().width > 0 and listctrl.GetSize().height > 0
assert listctrl.GetItemCount() == 1

frame.Destroy()
wx.Yield()
app.Destroy()
print("smoke GTK3 OK")
