#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Galerie Repens des images de catégories produits."""

import wx

from Dlg import DLG_Categories_produits_images as legacy
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics


class CTRL(legacy.CTRL):
    def __init__(self, parent):
        legacy.CTRL.__init__(self, parent)
        taille = UTILS_UIMetrics.px(108)
        self.taillePhoto = (taille, taille)
        try:
            self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
            self.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        except Exception:
            pass

    def SetDisabledTextColour(self, colour):
        """Neutralise le rouge historique de la galerie pour ce contrôle."""
        try:
            colour = UTILS_Interface.GetCouleurRole("on_surface_variant")
        except Exception:
            pass
        return legacy.CTRL.SetDisabledTextColour(self, colour)


class Panel(wx.Panel):
    def __init__(self, parent, bordure=0):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        self.parent = parent
        self.bordure = bordure
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))
        self.ctrl_image = CTRL(self)

        marge = max(int(bordure or 0), UTILS_UIMetrics.spacing(2))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl_image, 1, wx.EXPAND | wx.ALL, marge)
        self.SetSizer(sizer)
        self.Layout()

    def MAJ(self):
        self.ctrl_image.MAJ()
