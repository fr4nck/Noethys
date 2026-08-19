#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke test d'interface wxPython sans données métier.

Construit une petite fenêtre représentative (sizers, texte, bouton, liste AGW),
force le layout et un cycle d'événements, puis vérifie que les contrôles ont des
dimensions cohérentes. Aucun fichier utilisateur ni base n'est ouvert.
"""
import wx
from wx.lib.agw import ultimatelistctrl as ULC


app = wx.App(False)
print("wx :", wx.version())
print("plateforme :", wx.PlatformInfo)
assert "phoenix" in wx.PlatformInfo

frame = wx.Frame(None, title="Noethys UI smoke", size=(640, 420))
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

listctrl = ULC.UltimateListCtrl(panel, agwStyle=ULC.ULC_REPORT | ULC.ULC_SINGLE_SEL)
listctrl.InsertColumn(0, "Nom", width=220)
listctrl.InsertColumn(1, "Valeur", width=120)
index = listctrl.InsertStringItem(0, "Ligne test")
listctrl.SetStringItem(index, 1, "OK")
root.Add(listctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

panel.SetSizer(root)
frame.Layout()
frame.Show()
wx.Yield()

client = frame.GetClientSize()
assert client.width > 0 and client.height > 0
assert search.GetSize().width > 0
assert button.GetSize().width > 0
assert listctrl.GetSize().width > 0 and listctrl.GetSize().height > 0
assert listctrl.GetItemCount() == 1

frame.Destroy()
wx.Yield()
app.Destroy()
print("smoke layout wx OK")
