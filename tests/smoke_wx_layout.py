#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke test d'interface wxPython sans données métier.

Construit une fenêtre représentative (toolbar, formulaire, liste, grille), force
le layout et vérifie que les métriques communes ne tronquent pas leurs
composants. Aucun fichier utilisateur ni base métier n'est ouvert.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "noethys"))

import wx
import wx.grid as gridlib
from wx.lib.agw import ultimatelistctrl as ULC

from Ctrl import CTRL_Accueil
from Dlg import DLG_Echelle_interface
from Utils import UTILS_Aui
from Utils import UTILS_UIMetrics


app = wx.App(False)
print("wx :", wx.version())
print("plateforme :", wx.PlatformInfo)
assert "phoenix" in wx.PlatformInfo

frame = wx.Frame(None, title="Noethys UI smoke", size=(720, 560))
panel = wx.Panel(frame)
root = wx.BoxSizer(wx.VERTICAL)

toolbar = wx.ToolBar(panel, style=wx.TB_FLAT | wx.TB_TEXT | wx.TB_NODIVIDER)
bitmap = wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_TOOLBAR, wx.Size(32, 32))
toolbar.AddTool(wx.ID_ANY, "Action lisible", bitmap, shortHelp="Action de test")
toolbar.Realize()
UTILS_Aui.ConfigurerToolBar(toolbar, taille_base=32, fond_uni=True)
root.Add(toolbar, 0, wx.EXPAND)

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
root.Add(listctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

grid = gridlib.Grid(panel)
grid.CreateGrid(2, 3)
grid.SetRowLabelSize(120)
grid.SetColLabelSize(28)
grid.SetCellValue(0, 0, "Disponible")
grid.SetCellValue(0, 1, "Alerte")
grid.SetCellValue(0, 2, "Complet")
UTILS_Aui.ConfigurerGrille(grid)
root.Add(grid, 1, wx.EXPAND | wx.ALL, 8)

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

hauteur_toolbar = toolbar.GetSize().height
hauteur_min = UTILS_UIMetrics.toolbar_height(avec_libelle=True, icon_px=32)
print("toolbar :", hauteur_toolbar, "minimum design :", hauteur_min)
assert hauteur_toolbar >= hauteur_min
assert hauteur_toolbar > 32

assert grid.GetRowLabelSize() >= 120
assert grid.GetColLabelSize() >= 28
assert grid.GridLinesEnabled()
assert grid.GetDefaultRowSize() >= UTILS_UIMetrics.row_height("table")

frame.Destroy()
wx.Yield()

# Reproduit explicitement le premier paint de l'accueil. Sous wxMSW/Phoenix,
# AutoBufferedPaintDC lève une assertion native si BG_STYLE_PAINT n'a pas été
# posé dans le constructeur du contrôle.
accueil_frame = wx.Frame(None, title="Noethys accueil smoke", size=(520, 260))
accueil = CTRL_Accueil.Panel(accueil_frame)
accueil_frame.Show()
accueil.Refresh()
accueil.Update()
wx.Yield()
assert accueil.GetBackgroundStyle() == wx.BG_STYLE_PAINT
assert accueil.GetSize().width > 0 and accueil.GetSize().height > 0
accueil_frame.Destroy()
wx.Yield()

# Même contrat pour l'aperçu Apparence/échelle. Ce contrôle utilise lui aussi
# AutoBufferedPaintDC et avait la même assertion native sous wxMSW/Phoenix.
echelle_frame = wx.Frame(None, title="Noethys échelle smoke", size=(560, 280))
apercu_echelle = DLG_Echelle_interface.Apercu(echelle_frame)
echelle_frame.Show()
apercu_echelle.Refresh()
apercu_echelle.Update()
wx.Yield()
assert apercu_echelle.GetBackgroundStyle() == wx.BG_STYLE_PAINT
assert apercu_echelle.GetSize().width > 0 and apercu_echelle.GetSize().height > 0
echelle_frame.Destroy()
wx.Yield()

app.Destroy()
print("smoke layout wx OK")
