"""Compatibilité wxPython/Python 3 pour le runtime Noethys figé.

Ce hook conserve les alias wxPython Classic attendus par Noethys et neutralise
quelques incompatibilités Python 3/Phoenix observées dans le portable Windows.
Il ne charge volontairement aucun module applicatif Noethys au démarrage : les
correctifs spécifiques sont appliqués au moment de leur import normal.
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
# wx.Image.Rescale exige des dimensions entières.
_original_image_rescale = wx.Image.Rescale


def _image_rescale_int(self, width, height, *args, **kwargs):
    return _original_image_rescale(
        self, int(round(width)), int(round(height)), *args, **kwargs
    )


wx.Image.Rescale = _image_rescale_int


# wxPython Classic acceptait sys.maxsize/six.MAXSIZE comme index d'ajout dans
# un ListCtrl. Phoenix exige un index d'insertion valide.
_original_listctrl_insert_item = wx.ListCtrl.InsertItem


def _listctrl_insert_item(self, item, *args, **kwargs):
    if isinstance(item, int) and item >= sys.maxsize:
        item = self.GetItemCount()
    return _original_listctrl_insert_item(self, item, *args, **kwargs)


wx.ListCtrl.InsertItem = _listctrl_insert_item


def _patch_transport(module):
    """Corrige les factories ``lambda parent=self`` converties depuis Python 2."""

    def creation_controles(self, rubrique="generalites", label=None):
        if label is None:
            label = module._(u"Généralités")

        box = module.wx.StaticBox(self, -1, label)
        box_sizer = module.wx.StaticBoxSizer(box, module.wx.VERTICAL)
        grid_sizer = module.wx.FlexGridSizer(rows=18, cols=2, vgap=10, hgap=10)

        for dict_controle in module.DICT_CONTROLES[rubrique]:
            code = dict_controle["code"]
            ctrl_label = module.wx.StaticText(
                self, -1, u"%s :" % dict_controle["label"]
            )
            grid_sizer.Add(
                ctrl_label,
                0,
                module.wx.ALIGN_RIGHT | module.wx.ALIGN_CENTER_VERTICAL,
                0,
            )

            constructeur = dict_controle["ctrl"]
            ctrl = constructeur(self)
            ctrl.SetName(code)
            ctrl.rubrique = rubrique
            grid_sizer.Add(ctrl, 0, module.wx.EXPAND, 0)
            self.listeControles.append((code, ctrl, ctrl_label))

        grid_sizer.AddGrowableCol(1)
        box_sizer.Add(grid_sizer, 1, module.wx.ALL | module.wx.EXPAND, 10)
        self.grid_sizer_base.Add(box_sizer, 1, module.wx.EXPAND, 0)
        self.listeSizers.append(box_sizer)
        self.listeSizers.append(grid_sizer)

    module.CTRL.CreationControles = creation_controles


def _patch_taskbar(module):
    """Force en entiers les coordonnées du compteur Connecthys."""

    def ajoute_texte_image(
        self,
        image=None,
        texte="",
        alignement="droite-bas",
        padding=0,
        taille_police=9,
    ):
        largeur_image, hauteur_image = image.GetSize()
        bmp = wx.Bitmap(largeur_image, hauteur_image)
        mdc = wx.MemoryDC(bmp)
        dc = wx.GCDC(mdc)
        mdc.SetBackground(wx.Brush("black"))
        mdc.Clear()

        dc.SetBrush(wx.Brush(wx.RED))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetFont(wx.Font(taille_police, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        dc.SetTextForeground(wx.WHITE)
        largeur_texte, hauteur_texte = dc.GetTextExtent(texte)
        mdc.DrawBitmap(image, 0, 0)

        hauteur_rond = int(round(hauteur_texte + padding * 2))
        largeur_rond = int(
            round(largeur_texte + padding * 2 + hauteur_rond / 2.0)
        )
        if largeur_rond < hauteur_rond:
            largeur_rond = hauteur_rond

        x_rond = 1 if "gauche" in alignement else largeur_image - largeur_rond - 1
        y_rond = 1 if "haut" in alignement else hauteur_image - hauteur_rond - 1
        x_rond = int(round(x_rond))
        y_rond = int(round(y_rond))
        rayon = int(round(hauteur_rond / 2.0))
        dc.DrawRoundedRectangle(
            wx.Rect(x_rond, y_rond, largeur_rond, hauteur_rond), rayon
        )

        x_texte = int(round(x_rond + largeur_rond / 2.0 - largeur_texte / 2.0))
        y_texte = int(
            round(y_rond + hauteur_rond / 2.0 - hauteur_texte / 2.0 - 1)
        )
        dc.DrawText(texte, x_texte, y_texte)

        mdc.SelectObject(wx.NullBitmap)
        bmp.SetMaskColour("black")
        return bmp

    module.CustomTaskBarIcon.AjouteTexteImage = ajoute_texte_image


_TARGETS = {
    "Ctrl.CTRL_Saisie_transport": _patch_transport,
    "Ctrl.CTRL_TaskBarIcon": _patch_taskbar,
}


class _DeferredPatchLoader:
    def __init__(self, fullname, loader, patcher):
        self.fullname = fullname
        self.loader = loader
        self.patcher = patcher

    def create_module(self, spec):
        create_module = getattr(self.loader, "create_module", None)
        if create_module is None:
            return None
        return create_module(spec)

    def exec_module(self, module):
        sentinel = object()
        previous_self = sentinel
        if self.fullname == "Ctrl.CTRL_Saisie_transport":
            previous_self = getattr(builtins, "self", sentinel)
            builtins.self = None

        try:
            self.loader.exec_module(module)
        finally:
            if self.fullname == "Ctrl.CTRL_Saisie_transport":
                if previous_self is sentinel:
                    try:
                        del builtins.self
                    except AttributeError:
                        pass
                else:
                    builtins.self = previous_self

        self.patcher(module)

    def __getattr__(self, name):
        return getattr(self.loader, name)


class _DeferredPatchFinder:
    def find_spec(self, fullname, path=None, target=None):
        patcher = _TARGETS.get(fullname)
        if patcher is None:
            return None

        # Demande le spec aux finders déjà installés (dont celui de PyInstaller)
        # sans rappeler ce finder et provoquer une récursion.
        for finder in tuple(sys.meta_path):
            if finder is self:
                continue
            find_spec = getattr(finder, "find_spec", None)
            if find_spec is None:
                continue
            spec = find_spec(fullname, path, target)
            if spec is not None and spec.loader is not None:
                spec.loader = _DeferredPatchLoader(fullname, spec.loader, patcher)
                return spec
        return None


sys.meta_path.insert(0, _DeferredPatchFinder())
