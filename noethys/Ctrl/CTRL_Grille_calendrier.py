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

from Ctrl import CTRL_Calendrier
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


class CTRL(wx.Panel):
    """Wrapper compact du calendrier commun, sans géométrie locale."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.parent = parent
        Style.appliquer_fenetre(self, "surface")

        bord = Style.espace(1)
        self.ctrl_calendrier = CTRL_Calendrier.CTRL(
            self,
            afficheBoutonAnnuel=False,
            multiSelections=False,
            bordHaut=bord,
            bordBas=bord,
            bordLateral=bord,
        )

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl_calendrier, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetMinSize((Style.px(240), Style.px(190)))
        self.Layout()

        self.ctrl_calendrier.Bind(CTRL_Calendrier.EVT_SELECT_DATES, self.OnDateSelected)

    def OnDateSelected(self, event):
        self.GetParent().SetDate(self.GetDate())

    def GetDate(self):
        selections = self.ctrl_calendrier.GetSelections()
        if len(selections) > 0:
            return selections[0]
        return None

    def SetDate(self, date=None):
        if date is None:
            return
        self.ctrl_calendrier.SelectJours([date])


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(panel, "surface")
        self.ctrl = CTRL(panel)
        contenu = wx.BoxSizer(wx.VERTICAL)
        contenu.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, Style.espace(2))
        panel.SetSizer(contenu)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(panel, 1, wx.EXPAND)
        self.SetSizer(principal)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, _(u"TEST"), size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
