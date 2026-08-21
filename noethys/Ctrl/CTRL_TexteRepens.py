#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Texte sémantique de Repens Design.

Équivalent desktop d'une hiérarchie HTML enrichie : un écran choisit un rôle
(Display, H1..H6, Lead, BodyLarge, Body, BodySmall, Label, Caption, Micro ou
DataLarge) sans fixer lui-même une taille de police. Le rendu réel vient
exclusivement de ``UTILS_StyleRepens``.
"""

import wx

from Utils import UTILS_StyleRepens as Style


ROLES_TEXTE = (
    "display",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "lead",
    "body_large", "body", "body_small", "body_emphasis",
    "label", "caption", "micro", "overline",
    "data_large",
)


def _role(role):
    role = Style.normaliser_role_typographie(role)
    return role if role in ROLES_TEXTE or role in ("title", "section") else "body"


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
        self.role = _role(role)
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
        self.role = _role(role)
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


class _RoleTexte(CTRL):
    ROLE = "body"

    def __init__(self, parent, label=u"", **kwargs):
        kwargs["role"] = self.ROLE
        CTRL.__init__(self, parent, label=label, **kwargs)


class Display(_RoleTexte):
    ROLE = "display"


class H1(_RoleTexte):
    ROLE = "h1"


class H2(_RoleTexte):
    ROLE = "h2"


class H3(_RoleTexte):
    ROLE = "h3"


class H4(_RoleTexte):
    ROLE = "h4"


class H5(_RoleTexte):
    ROLE = "h5"


class H6(_RoleTexte):
    ROLE = "h6"


class Lead(_RoleTexte):
    ROLE = "lead"


class BodyLarge(_RoleTexte):
    ROLE = "body_large"


class Body(_RoleTexte):
    ROLE = "body"


class BodySmall(_RoleTexte):
    ROLE = "body_small"


class Label(_RoleTexte):
    ROLE = "label"


class Caption(_RoleTexte):
    ROLE = "caption"


class Micro(_RoleTexte):
    ROLE = "micro"


class DataLarge(_RoleTexte):
    ROLE = "data_large"
