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


class Mail(wx.TextCtrl):
    """Saisie d'adresse mail compatible thème, DPI et grosse police."""

    def __init__(self, parent, size=(-1, -1)):
        wx.TextCtrl.__init__(self, parent, -1, "", size=size)
        self.parent = parent
        self._AppliqueStyle()
        self.SetToolTip(wx.ToolTip(_(u"Saisissez une adresse mail")))
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

    def _AppliqueStyle(self):
        try:
            police = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
            facteur = UTILS_Interface.GetTailleTexte() / 100.0
            police.SetPointSize(max(8, int(round(police.GetPointSize() * facteur))))
            self.SetFont(police)
        except Exception:
            pass

        try:
            self.SetMinSize((-1, UTILS_UIMetrics.action_target("compact")))
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
        if event is not None:
            event.Skip()

    def Validation(self):
        text = self.GetValue()
        if text != "":
            posAt = text.find("@")
            if posAt == -1:
                message = _(u"L'adresse Email que vous avez saisie n'est pas valide !")
                return False, message
            posPoint = text.rfind(".")
            if posPoint < posAt:
                message = _(u"L'adresse Email que vous avez saisie n'est pas valide !")
                return False, message
        return True, None

    def SetMail(self, mail=""):
        if mail is None:
            return
        self.SetValue(mail)

    def GetMail(self):
        mail = self.GetValue()
        if mail == "":
            return None
        return mail.strip()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        self.ctrl = Mail(panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 0, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(2))
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
