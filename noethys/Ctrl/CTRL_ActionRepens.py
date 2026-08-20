#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Commande desktop Repens Design.

Contrôle volontairement léger pour les endroits où le bouton natif wx ne peut
pas exprimer la grammaire visuelle du cockpit (coins arrondis, état sémantique,
icône + libellé). Il conserve les usages desktop : focus clavier, Entrée/Espace,
hover, pressed et émission d'un ``wx.EVT_BUTTON`` standard.
"""

import wx

from Utils import UTILS_IconesRepens
from Utils import UTILS_Interface
from Utils import UTILS_Responsive
from Utils import UTILS_UIMetrics


class CTRL(wx.Control):
    def __init__(
        self,
        parent,
        id=wx.ID_ANY,
        label=u"",
        icone=None,
        variante="secondaire",
        tooltip=None,
        compact=True,
    ):
        style = wx.BORDER_NONE | wx.WANTS_CHARS | wx.TAB_TRAVERSAL
        wx.Control.__init__(self, parent, id=id, style=style)
        self.label = label or u""
        self.icone = icone
        self.variante = variante if variante in ("secondaire", "primaire", "danger", "ghost") else "secondaire"
        self.compact = bool(compact)
        self._hover = False
        self._pressed = False

        if tooltip:
            self.SetToolTip(wx.ToolTip(tooltip))
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetMinSize(self.DoGetBestSize())

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self.Bind(wx.EVT_SET_FOCUS, self.OnFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnFocus)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda event: None)

    def SetLabel(self, label):
        self.label = label or u""
        self.InvalidateBestSize()
        self.SetMinSize(self.DoGetBestSize())
        self.Refresh()

    def GetLabel(self):
        return self.label

    def SetIcone(self, icone):
        self.icone = icone
        self.InvalidateBestSize()
        self.Refresh()

    def _GetBitmap(self):
        if not self.icone:
            return None
        taille = UTILS_Responsive.GetTailleIcone(18 if self.compact else 20)
        role = "on_primary" if self.variante == "primaire" else "on_surface"
        if self.variante == "danger":
            role = "danger_text"
        try:
            bitmap = UTILS_IconesRepens.GetBitmap(self.icone, taille=taille, role=role)
            if bitmap is not None and bitmap.IsOk():
                return bitmap
        except Exception:
            pass
        return None

    def _GetCouleurs(self):
        if not self.IsEnabled():
            return (
                UTILS_Interface.GetCouleurRole("disabled"),
                UTILS_Interface.GetCouleurRole("disabled_text"),
                UTILS_Interface.GetCouleurRole("outline_variant"),
            )

        if self.variante == "primaire":
            fond = UTILS_Interface.GetCouleurRole("primary")
            texte = UTILS_Interface.GetCouleurRole("on_primary")
            contour = UTILS_Interface.GetCouleurRole("primary")
        elif self.variante == "danger":
            fond = UTILS_Interface.GetCouleurRole("danger")
            texte = UTILS_Interface.GetCouleurRole("danger_text")
            contour = UTILS_Interface.GetCouleurRole("danger_text")
        elif self.variante == "ghost":
            fond = UTILS_Interface.GetCouleurRole("surface_container_low")
            texte = UTILS_Interface.GetCouleurRole("on_surface")
            contour = UTILS_Interface.GetCouleurRole("surface_container_low")
        else:
            fond = UTILS_Interface.GetCouleurRole("surface_container_high")
            texte = UTILS_Interface.GetCouleurRole("on_surface")
            contour = UTILS_Interface.GetCouleurRole("outline_variant")

        if self._pressed:
            fond = UTILS_Interface.GetCouleurRole("selection")
            texte = UTILS_Interface.GetCouleurRole("selection_text")
            contour = UTILS_Interface.GetCouleurRole("primary")
        elif self._hover:
            if self.variante == "primaire":
                fond = UTILS_Interface.GetCouleurRole("primary_container")
                texte = UTILS_Interface.GetCouleurRole("on_primary_container")
            elif self.variante != "danger":
                fond = UTILS_Interface.GetCouleurRole("surface_container_highest")

        if self.HasFocus():
            contour = UTILS_Interface.GetCouleurRole("focus")
        return fond, texte, contour

    def _CouleurParent(self):
        try:
            parent = self.GetParent()
            couleur = parent.GetBackgroundColour()
            if couleur.IsOk():
                return couleur
        except Exception:
            pass
        return UTILS_Interface.GetCouleurRole("surface")

    def DoGetBestSize(self):
        hauteur = UTILS_UIMetrics.action_target("compact" if self.compact else "standard")
        padding_x = UTILS_UIMetrics.spacing(2 if self.compact else 3)
        largeur = padding_x * 2

        bitmap = self._GetBitmap()
        if bitmap is not None:
            largeur += bitmap.GetWidth()
        if self.label:
            dc = wx.ClientDC(self)
            dc.SetFont(self.GetFont())
            largeur_texte, _ = dc.GetTextExtent(self.label)
            if bitmap is not None:
                largeur += UTILS_UIMetrics.spacing(1)
            largeur += largeur_texte
        if not self.label:
            largeur = max(largeur, hauteur)
        return wx.Size(max(hauteur, largeur), hauteur)

    def OnPaint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBackground(wx.Brush(self._CouleurParent()))
        dc.Clear()
        rect = self.GetClientRect()
        fond, texte, contour = self._GetCouleurs()
        rayon = UTILS_UIMetrics.px(7)

        dc.SetBrush(wx.Brush(fond))
        dc.SetPen(wx.Pen(contour, max(1, UTILS_UIMetrics.px(1))))
        dc.DrawRoundedRectangle(rect.x, rect.y, max(1, rect.width - 1), max(1, rect.height - 1), rayon)

        bitmap = self._GetBitmap()
        dc.SetFont(self.GetFont())
        dc.SetTextForeground(texte)
        dc.SetBackgroundMode(wx.TRANSPARENT)

        largeur_texte, hauteur_texte = dc.GetTextExtent(self.label) if self.label else (0, 0)
        largeur_bitmap = bitmap.GetWidth() if bitmap is not None else 0
        hauteur_bitmap = bitmap.GetHeight() if bitmap is not None else 0
        espace = UTILS_UIMetrics.spacing(1) if bitmap is not None and self.label else 0
        largeur_contenu = largeur_bitmap + espace + largeur_texte
        x = rect.x + max(0, int((rect.width - largeur_contenu) / 2))

        if bitmap is not None:
            y = rect.y + max(0, int((rect.height - hauteur_bitmap) / 2))
            dc.DrawBitmap(bitmap, x, y, True)
            x += largeur_bitmap + espace
        if self.label:
            y = rect.y + max(0, int((rect.height - hauteur_texte) / 2))
            dc.DrawText(self.label, x, y)

    def _EnvoyerClick(self):
        if not self.IsEnabled():
            return
        type_evt = getattr(wx.EVT_BUTTON, "typeId", getattr(wx, "wxEVT_BUTTON", 0))
        evenement = wx.CommandEvent(type_evt, self.GetId())
        evenement.SetEventObject(self)
        wx.PostEvent(self, evenement)

    def OnEnter(self, event):
        self._hover = True
        self.Refresh()

    def OnLeave(self, event):
        self._hover = False
        if not self.HasCapture():
            self._pressed = False
        self.Refresh()

    def OnLeftDown(self, event):
        if not self.IsEnabled():
            return
        self.SetFocus()
        self._pressed = True
        if not self.HasCapture():
            self.CaptureMouse()
        self.Refresh()

    def OnLeftUp(self, event):
        if not self.IsEnabled():
            return
        dedans = self.GetClientRect().Contains(event.GetPosition())
        if self.HasCapture():
            self.ReleaseMouse()
        etait_presse = self._pressed
        self._pressed = False
        self.Refresh()
        if dedans and etait_presse:
            self._EnvoyerClick()

    def OnKeyDown(self, event):
        if event.GetKeyCode() in (wx.WXK_SPACE, wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            self._pressed = True
            self.Refresh()
            return
        event.Skip()

    def OnKeyUp(self, event):
        if event.GetKeyCode() in (wx.WXK_SPACE, wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
            etait_presse = self._pressed
            self._pressed = False
            self.Refresh()
            if etait_presse:
                self._EnvoyerClick()
            return
        event.Skip()

    def OnFocus(self, event):
        self.Refresh()
        event.Skip()
