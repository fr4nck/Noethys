#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke test d'interface wxPython sans données métier.

Construit des composants et dialogues représentatifs, force leur affichage et
leur layout, puis vérifie qu'ils contiennent réellement des contrôles visibles
et dimensionnés. Aucun fichier utilisateur ni base métier n'est modifié.
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
from Dlg import DLG_Inscription
from Utils import UTILS_Aui
from Utils import UTILS_UIMetrics


def _descendants(window):
    resultat = []
    pile = list(window.GetChildren())
    while pile:
        enfant = pile.pop()
        resultat.append(enfant)
        pile.extend(enfant.GetChildren())
    return resultat


def _book_types():
    """Types standards wx dérivés de BookCtrl disponibles sur la plateforme."""
    noms = ("Notebook", "Treebook", "Listbook", "Choicebook", "Toolbook")
    return tuple(getattr(wx, nom) for nom in noms if hasattr(wx, nom))


def _assert_books_populated(descendants):
    """Parcourt réellement toutes les pages des Notebook/Treebook standards."""
    types = _book_types()
    if not types:
        return

    for book in (ctrl for ctrl in descendants if isinstance(ctrl, types)):
        page_count = book.GetPageCount()
        assert page_count > 0, f"book vide: {book.__class__.__name__}"
        selection_initiale = book.GetSelection()

        for index in range(page_count):
            book.SetSelection(index)
            book.Layout()
            page = book.GetPage(index)
            page.Layout()
            wx.Yield()

            taille = page.GetSize()
            assert taille.width > 0 and taille.height > 0, (
                f"page non dimensionnée: {book.__class__.__name__}[{index}] {taille}"
            )

            contenu = _descendants(page)
            assert contenu, f"page sans contenu: {book.__class__.__name__}[{index}]"
            assert any(
                ctrl.IsShown() and ctrl.GetSize().width > 0 and ctrl.GetSize().height > 0
                for ctrl in contenu
            ), f"page sans contrôle visible: {book.__class__.__name__}[{index}]"

        if 0 <= selection_initiale < page_count:
            book.SetSelection(selection_initiale)
            wx.Yield()


def _assert_window_populated(window, min_descendants=1):
    """Vérifie qu'une fenêtre affichée n'est ni vide ni non dimensionnée."""
    window.Layout()
    window.Show()
    wx.Yield()

    client = window.GetClientSize()
    assert client.width > 0 and client.height > 0, (
        f"fenêtre sans taille utile: {window.__class__.__name__} {client}"
    )

    descendants = _descendants(window)
    assert len(descendants) >= min_descendants, (
        f"contenu incomplet: {window.__class__.__name__} "
        f"({len(descendants)} descendants, minimum {min_descendants})"
    )

    visibles = []
    for ctrl in descendants:
        taille = ctrl.GetSize()
        if ctrl.IsShown() and taille.width > 0 and taille.height > 0:
            visibles.append(ctrl)
    assert visibles, f"aucun contrôle visible et dimensionné dans {window.__class__.__name__}"

    _assert_books_populated(descendants)
    return descendants


app = wx.App(False)
print("wx :", wx.version())
print("plateforme :", wx.PlatformInfo)
assert "phoenix" in wx.PlatformInfo

# Les imports historiques doivent pointer vers leur implémentation réelle quand
# aucune spécialisation n'est structurellement nécessaire. Les corrections de
# layout des préférences vivent désormais dans DLG_Preferences lui-même.
from Dlg import DLG_Impression_conso
from Dlg import DLG_Preferences
assert DLG_Impression_conso.__name__ == "Dlg.DLG_Impression_conso_differe"
assert DLG_Preferences.__name__ == "Dlg.DLG_Preferences"

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

# Préférences : ce test construit réellement le dialogue métier. Un simple
# import ou un constructeur qui retourne sans contenu ne suffit pas.
preferences_parent = wx.Frame(None, title="Noethys préférences parent", size=(1000, 800))
preferences_parent.Show()
wx.Yield()
preferences = DLG_Preferences.Dialog(preferences_parent)
_desc = _assert_window_populated(preferences, min_descendants=30)
assert isinstance(preferences.contenu, wx.ScrolledWindow)
for nom_ctrl in (
    "ctrl_interface",
    "ctrl_interface_mysql",
    "ctrl_dates",
    "ctrl_telephones",
    "ctrl_codesPostaux",
    "ctrl_adresses",
    "ctrl_propose_maj",
    "ctrl_rapport_bugs",
    "ctrl_derniers_fichiers",
    "ctrl_monnaie",
    "ctrl_autodeconnect",
    "ctrl_comptes_internet",
    "ctrl_email",
):
    ctrl = getattr(preferences, nom_ctrl)
    assert ctrl.GetParent() is preferences.contenu, f"parent wx inattendu pour {nom_ctrl}"
    taille = ctrl.GetSize()
    assert taille.width > 0 and taille.height > 0, f"contrôle non dimensionné: {nom_ctrl}"
assert preferences.bouton_ok.IsShown()
assert preferences.bouton_annuler.IsShown()
preferences.Destroy()
preferences_parent.Destroy()
wx.Yield()

# Inscription : construit le vrai dialogue et parcourt ses deux pages. Le seul
# accès DB neutralisé est le chargement du questionnaire ; la structure wx et
# le câblage parent visuel / contrôleur métier restent ceux de production.
inscription_parent = wx.Frame(None, title="Noethys inscription parent", size=(1000, 800))
inscription_parent.Show()
wx.Yield()
_questionnaire_maj = DLG_Inscription.CTRL_Questionnaire.CTRL.MAJ
inscription = None
try:
    DLG_Inscription.CTRL_Questionnaire.CTRL.MAJ = lambda self, *args, **kwargs: None
    inscription = DLG_Inscription.Dialog(
        inscription_parent,
        mode="saisie",
        IDindividu=None,
        cp="00000",
        ville="CI",
    )
    _desc = _assert_window_populated(inscription, min_descendants=20)
    page_activite = inscription.GetPageActivite()
    assert page_activite.controller is inscription
    assert page_activite.ctrl_activite.controller is page_activite
    assert page_activite.ctrl_groupes.controller is page_activite
    assert page_activite.ctrl_categories.controller is page_activite
finally:
    DLG_Inscription.CTRL_Questionnaire.CTRL.MAJ = _questionnaire_maj
    if inscription is not None:
        inscription.Destroy()
    inscription_parent.Destroy()
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