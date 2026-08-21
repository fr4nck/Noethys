#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Surface commune de Repens Design.

Ce contrôle n'est pas une carte mobile : c'est une couche de fond desktop pour
regrouper une information ou une commande dans une interface métier. Son
apparence est entièrement fournie par ``UTILS_StyleRepens``.

Les anciens appels peuvent encore fournir ``rayon`` et ``padding`` en valeurs
numériques. Les nouveaux composants doivent les omettre afin de consommer les
métriques sémantiques du socle Repens.
"""

import wx

from Utils import UTILS_StyleRepens as Style


class CTRL(wx.Panel):
    def __init__(
        self,
        parent,
        role_fond="surface_container_low",
        role_contour="outline_variant",
        rayon=None,
        padding=None,
    ):
        wx.Panel.__init__(self, parent, style=wx.BORDER_NONE | wx.TAB_TRAVERSAL)
        self.role_fond = role_fond
        self.role_contour = role_contour
        # Compatibilité avec les écrans historiques encore non migrés. Les
        # valeurs None signifient : utiliser les métriques communes Repens.
        self.rayon_legacy = rayon
        self.padding_legacy = padding
        self.SetFont(Style.police("body"))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda event: None)

    def GetCouleurFond(self):
        return Style.couleur(self.role_fond)

    def GetCouleurContour(self):
        return Style.couleur(self.role_contour)

    def GetPadding(self):
        if self.padding_legacy is not None:
            return Style.px(self.padding_legacy)
        return Style.espace(2)

    def GetRayon(self):
        if self.rayon_legacy is not None:
            return Style.px(self.rayon_legacy)
        return Style.rayon("surface")

    def _GetCouleurExterieure(self):
        try:
            couleur = self.GetParent().GetBackgroundColour()
            if couleur.IsOk():
                return couleur
        except Exception:
            pass
        return Style.couleur("surface")

    def SetRoles(self, role_fond=None, role_contour=None):
        if role_fond:
            self.role_fond = role_fond
        if role_contour:
            self.role_contour = role_contour
        self.Refresh()

    def OnPaint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBackground(wx.Brush(self._GetCouleurExterieure()))
        dc.Clear()
        rect = self.GetClientRect()
        if rect.width <= 1 or rect.height <= 1:
            return
        dc.SetBrush(wx.Brush(self.GetCouleurFond()))
        dc.SetPen(wx.Pen(self.GetCouleurContour(), max(1, Style.px(1))))
        dc.DrawRoundedRectangle(
            rect.x,
            rect.y,
            max(1, rect.width - 1),
            max(1, rect.height - 1),
            self.GetRayon(),
        )
