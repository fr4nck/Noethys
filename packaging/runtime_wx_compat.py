"""Compatibilité wxPython/Python 3 pour le runtime Noethys figé.

Ce hook conserve les alias wxPython Classic attendus par Noethys et neutralise
quelques incompatibilités Python 3/Phoenix observées dans le portable Windows.
Il ne touche ni à la base de données ni aux configurations utilisateur.
"""
from __future__ import annotations

import builtins
import sys

import wx


# Alias wxPython Classic encore utilisés par le code historique.
if not hasattr(wx, "EmptyBitmap"):
    wx.EmptyBitmap = lambda width, height, depth=-1: wx.Bitmap(width, height, depth)

if not hasattr(wx, "EmptyIcon"):
    wx.EmptyIcon = wx.Icon

if not hasattr(wx, "EmptyImage"):
    wx.EmptyImage = wx.Image

if not hasattr(wx, "BitmapFromImage"):
    wx.BitmapFromImage = wx.Bitmap

if not hasattr(wx, "NewId"):
    wx.NewId = lambda: int(wx.NewIdRef())


# Sous Python 3, les divisions historiques produisent des float alors que
# wx.Image.Rescale exige des dimensions entières. Centraliser la conversion
# évite de reproduire le même correctif dans chaque ancien écran.
_original_image_rescale = wx.Image.Rescale


def _image_rescale_int(self, width, height, *args, **kwargs):
    width = int(round(width))
    height = int(round(height))
    return _original_image_rescale(self, width, height, *args, **kwargs)


wx.Image.Rescale = _image_rescale_int


# wxPython Classic acceptait sys.maxsize/six.MAXSIZE comme index d'ajout dans
# un ListCtrl. Phoenix exige désormais un identifiant d'item réellement valide.
_original_listctrl_insert_item = wx.ListCtrl.InsertItem


def _listctrl_insert_item(self, item, *args, **kwargs):
    if isinstance(item, int) and item >= sys.maxsize:
        item = self.GetItemCount()
    return _original_listctrl_insert_item(self, item, *args, **kwargs)


wx.ListCtrl.InsertItem = _listctrl_insert_item


# CTRL_Saisie_transport contient des lambdas converties automatiquement sous
# la forme ``lambda parent=self`` au niveau module. En Python 3, ``self``
# n'existe pas à cet endroit et l'import bloque les fiches famille, le
# gestionnaire de consommations, le badgeage et les demandes Connecthys.
# On importe une fois le module avec un défaut inoffensif, puis on remplace
# CreationControles afin que le vrai parent soit toujours fourni explicitement.
_sentinel = object()
_previous_builtin_self = getattr(builtins, "self", _sentinel)
builtins.self = None
try:
    from Ctrl import CTRL_Saisie_transport as _transport
finally:
    if _previous_builtin_self is _sentinel:
        del builtins.self
    else:
        builtins.self = _previous_builtin_self


def _creation_controles_transport(self, rubrique="generalites", label=None):
    if label is None:
        label = _transport._(u"Généralités")

    box = _transport.wx.StaticBox(self, -1, label)
    boxSizer = _transport.wx.StaticBoxSizer(box, _transport.wx.VERTICAL)
    grid_sizer = _transport.wx.FlexGridSizer(rows=18, cols=2, vgap=10, hgap=10)

    for dictControle in _transport.DICT_CONTROLES[rubrique]:
        code = dictControle["code"]
        ctrl_label = _transport.wx.StaticText(self, -1, u"%s :" % dictControle["label"])
        grid_sizer.Add(
            ctrl_label,
            0,
            _transport.wx.ALIGN_RIGHT | _transport.wx.ALIGN_CENTER_VERTICAL,
            0,
        )

        constructeur = dictControle["ctrl"]
        ctrl = constructeur(self)
        ctrl.SetName(code)
        ctrl.rubrique = rubrique
        grid_sizer.Add(ctrl, 0, _transport.wx.EXPAND, 0)
        self.listeControles.append((code, ctrl, ctrl_label))

    grid_sizer.AddGrowableCol(1)
    boxSizer.Add(grid_sizer, 1, _transport.wx.ALL | _transport.wx.EXPAND, 10)
    self.grid_sizer_base.Add(boxSizer, 1, _transport.wx.EXPAND, 0)
    self.listeSizers.append(boxSizer)
    self.listeSizers.append(grid_sizer)


_transport.CTRL.CreationControles = _creation_controles_transport


# Connecthys ajoute un compteur sur son icône de zone de notification. Les
# coordonnées calculées avec /2.0 doivent être entières avec Phoenix.
from Ctrl import CTRL_TaskBarIcon as _taskbar


def _ajoute_texte_image(self, image=None, texte="", alignement="droite-bas", padding=0, taille_police=9):
    largeurImage, hauteurImage = image.GetSize()
    bmp = wx.Bitmap(largeurImage, hauteurImage)
    mdc = wx.MemoryDC(bmp)
    dc = wx.GCDC(mdc)
    mdc.SetBackground(wx.Brush("black"))
    mdc.Clear()

    dc.SetBrush(wx.Brush(wx.RED))
    dc.SetPen(wx.TRANSPARENT_PEN)
    dc.SetFont(wx.Font(taille_police, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
    dc.SetTextForeground(wx.WHITE)
    largeurTexte, hauteurTexte = dc.GetTextExtent(texte)
    mdc.DrawBitmap(image, 0, 0)

    hauteurRond = int(round(hauteurTexte + padding * 2))
    largeurRond = int(round(largeurTexte + padding * 2 + hauteurRond / 2.0))
    if largeurRond < hauteurRond:
        largeurRond = hauteurRond

    xRond = 1 if "gauche" in alignement else largeurImage - largeurRond - 1
    yRond = 1 if "haut" in alignement else hauteurImage - hauteurRond - 1
    xRond = int(round(xRond))
    yRond = int(round(yRond))
    rayon = int(round(hauteurRond / 2.0))
    dc.DrawRoundedRectangle(wx.Rect(xRond, yRond, largeurRond, hauteurRond), rayon)

    xTexte = int(round(xRond + largeurRond / 2.0 - largeurTexte / 2.0))
    yTexte = int(round(yRond + hauteurRond / 2.0 - hauteurTexte / 2.0 - 1))
    dc.DrawText(texte, xTexte, yTexte)

    mdc.SelectObject(wx.NullBitmap)
    bmp.SetMaskColour("black")
    return bmp


_taskbar.CustomTaskBarIcon.AjouteTexteImage = _ajoute_texte_image
