#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Badge d'état compact de Repens Design.

Destiné aux statuts courts au sein d'une interface dense : validité, alerte,
information, succès. Le contrôle ne connaît aucune couleur concrète et consomme
exclusivement le « CSS Noethys » ``UTILS_StyleRepens``.
"""

import wx

from Utils import UTILS_StyleRepens as Style


ROLES = {
    "neutre": ("surface_container_high", "on_surface"),
    "succes": ("success", "success_text"),
    "attention": ("warning", "warning_text"),
    "danger": ("danger", "danger_text"),
    "info": ("info", "info_text"),
}


class CTRL(wx.Control):
    def __init__(self, parent, label=u"", role="neutre"):
        wx.Control.__init__(
            self,
            parent,
            -1,
            style=wx.BORDER_NONE | wx.TAB_TRAVERSAL,
        )
        self.label = label or u""
        self.role = role if role in ROLES else "neutre"
        self.SetFont(Style.police("caption"))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetMinSize(self.DoGetBestSize())
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda event: None)

    def SetEtat(self, label=None, role=None):
        if label is not None:
            self.label = label
        if role is not None and role in ROLES:
            self.role = role
        self.InvalidateBestSize()
        self.SetMinSize(self.DoGetBestSize())
        self.Refresh()

    def SetLabel(self, label):
        self.SetEtat(label=label)

    def GetLabel(self):
        return self.label

    def _CouleurParent(self):
        try:
            couleur = self.GetParent().GetBackgroundColour()
            if couleur.IsOk():
                return couleur
        except Exception:
            pass
        return Style.couleur("surface")

    def DoGetBestSize(self):
        dc = wx.ClientDC(self)
        dc.SetFont(self.GetFont())
        largeur, hauteur_texte = dc.GetTextExtent(self.label or u" ")
        padding_x = Style.espace(2)
        hauteur = max(Style.px(24), hauteur_texte + Style.espace(2))
        return wx.Size(max(hauteur, largeur + padding_x * 2), hauteur)

    def OnPaint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBackground(wx.Brush(self._CouleurParent()))
        dc.Clear()
        rect = self.GetClientRect()
        if rect.width <= 1 or rect.height <= 1:
            return

        role_fond, role_texte = ROLES[self.role]
        dc.SetBrush(wx.Brush(Style.couleur(role_fond)))
        dc.SetPen(wx.Pen(Style.couleur(role_fond), max(1, Style.px(1))))
        dc.DrawRoundedRectangle(
            rect.x,
            rect.y,
            max(1, rect.width - 1),
            max(1, rect.height - 1),
            max(1, int(rect.height / 2)),
        )

        dc.SetFont(self.GetFont())
        dc.SetTextForeground(Style.couleur(role_texte))
        dc.SetBackgroundMode(wx.TRANSPARENT)
        largeur, hauteur = dc.GetTextExtent(self.label)
        dc.DrawText(
            self.label,
            rect.x + max(0, int((rect.width - largeur) / 2)),
            rect.y + max(0, int((rect.height - hauteur) / 2)),
        )
