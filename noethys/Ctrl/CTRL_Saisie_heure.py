#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:          Licence GNU GPL
#-----------------------------------------------------------

import wx
import wx.lib.masked as masked
import datetime

from Utils.UTILS_Traduction import _
from Utils import UTILS_StyleRepens as Style


class Heure(masked.TextCtrl):
    """Saisie d'heure compacte alignée sur le CSS Repens."""

    def __init__(self, parent, heure_max=24, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.TE_CENTRE):
        masked.TextCtrl.__init__(
            self,
            parent,
            id=id,
            value="",
            pos=pos,
            size=size,
            style=style,
            mask="##:##",
            validRegex="[0-2][0-9]:[0-5][0-9]",
        )
        self.parent = parent
        self.heure_max = heure_max
        Style.appliquer_saisie(self)

        try:
            largeur = max(Style.px(68), self.GetTextExtent("00:00")[0] + Style.espace(4))
            self.SetMinSize((largeur, Style.cible_action("compact")))
        except Exception:
            pass

        self.SetToolTip(wx.ToolTip(_(u"Saisissez une heure")))
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

    def StrEnDatetime(self, texteHeure):
        texteHeure = texteHeure[:5]
        posTemp = texteHeure.index(":")
        heuresTemp = int(texteHeure[:posTemp])
        minutesTemp = int(texteHeure[posTemp + 1:])
        return datetime.time(heuresTemp, minutesTemp)

    def Validation(self):
        texteBrut = self.GetPlainValue()
        if len(texteBrut) != 4:
            return False
        try:
            if texteBrut == "":
                return False
            for chiffre in texteBrut:
                if chiffre != " ":
                    if not (0 <= int(chiffre) <= 9):
                        return False
                else:
                    return False
            if not (0 <= int(texteBrut[:2]) <= self.heure_max):
                return False
            if not (0 <= int(texteBrut[-2:]) <= 59):
                return False
            return True
        except Exception:
            return False

    def SetHeure(self, heure):
        if heure is None:
            return
        self.SetValue(heure)

    def GetHeure(self):
        heure = self.GetValue()
        if heure == "  :  ":
            return None
        return heure

    def OnKillFocus(self, event):
        self.Validation()
        event.Skip()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(panel)
        self.ctrl1 = Heure(panel)
        self.ctrl2 = Heure(panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl1, 0, wx.ALL | wx.EXPAND, Style.espace(2))
        sizer.Add(self.ctrl2, 0, wx.ALL | wx.EXPAND, Style.espace(2))
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
