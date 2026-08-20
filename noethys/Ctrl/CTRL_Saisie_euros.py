#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import wx

from Utils.UTILS_Traduction import _
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics


class CTRL(wx.TextCtrl):
    """Saisie monétaire alignée sur les métriques du design system."""

    def __init__(self, parent, font=None, size=(-1, -1), style=wx.TE_RIGHT):
        wx.TextCtrl.__init__(self, parent, -1, u"0.00", size=size, style=style)
        self.parent = parent
        self._AppliqueStyle(font)
        self.SetToolTip(wx.ToolTip(_(u"Saisissez un montant")))
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

    def _AppliqueStyle(self, font=None):
        try:
            if font is None:
                font = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
                facteur = UTILS_Interface.GetTailleTexte() / 100.0
                font.SetPointSize(max(8, int(round(font.GetPointSize() * facteur))))
            self.SetFont(font)
        except Exception:
            pass

        try:
            largeur = max(
                UTILS_UIMetrics.px(88),
                self.GetTextExtent("0000.00")[0] + UTILS_UIMetrics.spacing(4),
            )
            self.SetMinSize((largeur, UTILS_UIMetrics.action_target("compact")))
            self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
            self.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        except Exception:
            pass

    def OnKillFocus(self, event):
        valide, messageErreur = self.Validation()
        if valide is False:
            dlg = wx.MessageDialog(self, messageErreur, _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
        else:
            montant = float(self.GetValue())
            self.SetValue(u"%.2f" % montant)
        if event is not None:
            event.Skip()

    def Validation(self):
        montantStr = self.GetValue()
        try:
            float(montantStr)
        except Exception:
            message = _(u"Le montant que vous avez saisi n'est pas valide.")
            return False, message
        return True, None

    def SetMontant(self, montant=0.0):
        if montant is None:
            montant = 0.0
        self.SetValue(u"%.2f" % montant)

    def GetMontant(self):
        validation, erreur = self.Validation()
        if validation is True:
            return float(self.GetValue())
        return None


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        self.ctrl = CTRL(panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 0, wx.ALL, UTILS_UIMetrics.spacing(2))
        panel.SetSizer(sizer)
        cadre = wx.BoxSizer(wx.VERTICAL)
        cadre.Add(panel, 1, wx.EXPAND)
        self.SetSizer(cadre)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
