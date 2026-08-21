#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Texte sémantique de Repens Design.

Équivalent desktop d'une hiérarchie HTML : un écran choisit ``h1``, ``h2``,
``h3``, ``body`` ou ``caption`` sans fixer lui-même une taille de police.
Le rendu réel vient exclusivement de ``UTILS_StyleRepens``.
"""

import wx

from Utils import UTILS_StyleRepens as Style


ROLES_TEXTE = (
    "h1", "h2", "h3", "h4", "h5", "h6",
    "body", "body_emphasis", "caption", "overline",
)


class CTRL(wx.StaticText):
    def __init__(
        self,
        parent,
        label=u"",
        role="body",
        role_texte="on_surface",
        role_fond=None,
        wrap=True,
    ):
        wx.StaticText.__init__(self, parent, -1, label or u"")
        self.role = role if role in ROLES_TEXTE else "body"
        self.role_texte = role_texte
        self.role_fond = role_fond
        self.wrap_actif = bool(wrap)
        self._reflow_pending = False
        self.AppliquerStyle()
        if self.wrap_actif:
            self.Bind(wx.EVT_SIZE, self.OnSize)
            wx.CallAfter(self.Reflow)

    def AppliquerStyle(self):
        Style.appliquer_texte(
            self,
            role=self.role,
            role_texte=self.role_texte,
            role_fond=self.role_fond,
        )
        self.Refresh()

    def SetRole(self, role):
        if role not in ROLES_TEXTE:
            role = "body"
        self.role = role
        self.AppliquerStyle()
        self.InvalidateBestSize()
        if self.wrap_actif:
            wx.CallAfter(self.Reflow)

    def SetRoleTexte(self, role_texte):
        self.role_texte = role_texte
        self.AppliquerStyle()

    def SetLabel(self, label):
        wx.StaticText.SetLabel(self, label or u"")
        self.InvalidateBestSize()
        if self.wrap_actif:
            wx.CallAfter(self.Reflow)

    def Reflow(self):
        self._reflow_pending = False
        if not self.wrap_actif:
            return
        try:
            largeur = self.GetClientSize().GetWidth()
            if largeur > Style.px(80):
                self.Wrap(max(Style.px(80), largeur))
        except Exception:
            return
        try:
            parent = self.GetParent()
            if parent is not None:
                parent.Layout()
        except Exception:
            pass

    def OnSize(self, event):
        event.Skip()
        if self._reflow_pending:
            return
        self._reflow_pending = True
        wx.CallAfter(self.Reflow)


class H1(CTRL):
    def __init__(self, parent, label=u"", **kwargs):
        kwargs["role"] = "h1"
        CTRL.__init__(self, parent, label=label, **kwargs)


class H2(CTRL):
    def __init__(self, parent, label=u"", **kwargs):
        kwargs["role"] = "h2"
        CTRL.__init__(self, parent, label=label, **kwargs)


class H3(CTRL):
    def __init__(self, parent, label=u"", **kwargs):
        kwargs["role"] = "h3"
        CTRL.__init__(self, parent, label=label, **kwargs)
