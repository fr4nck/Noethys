#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Surface arrondie commune de Repens Design.

Ce contrôle n'est pas une carte mobile : c'est une couche de fond desktop pour
regrouper une information ou une commande dans le cockpit. Les enfants restent
des contrôles wx standards ; seul le fond/contour est dessiné ici.
"""

import wx

from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics


class CTRL(wx.Panel):
    def __init__(
        self,
        parent,
        role_fond="surface_container_low",
        role_contour="outline_variant",
        rayon=9,
        padding=8,
    ):
        wx.Panel.__init__(self, parent, style=wx.BORDER_NONE | wx.TAB_TRAVERSAL)
        self.role_fond = role_fond
        self.role_contour = role_contour
        self.rayon_base = rayon
        self.padding_base = padding
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda event: None)

    def GetCouleurFond(self):
        return UTILS_Interface.GetCouleurRole(self.role_fond)

    def GetCouleurContour(self):
        return UTILS_Interface.GetCouleurRole(self.role_contour)

    def GetPadding(self):
        return UTILS_UIMetrics.px(self.padding_base)

    def _GetCouleurExterieure(self):
        try:
            couleur = self.GetParent().GetBackgroundColour()
            if couleur.IsOk():
                return couleur
        except Exception:
            pass
        return UTILS_Interface.GetCouleurRole("surface")

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
        dc.SetPen(wx.Pen(self.GetCouleurContour(), max(1, UTILS_UIMetrics.px(1))))
        dc.DrawRoundedRectangle(
            rect.x,
            rect.y,
            max(1, rect.width - 1),
            max(1, rect.height - 1),
            UTILS_UIMetrics.px(self.rayon_base),
        )
