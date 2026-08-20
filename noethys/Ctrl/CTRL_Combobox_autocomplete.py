#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-14 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import wx

from Utils.UTILS_Traduction import _
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics


class CTRL(wx.ComboBox):
    """ComboBox avec autocomplétion, alignée sur le design system."""

    def __init__(self, parent):
        wx.ComboBox.__init__(self, parent, wx.ID_ANY)
        self.ignoreEvtText = False
        self._AppliqueStyle()
        self.Bind(wx.EVT_TEXT, self.EvtText)
        self.Bind(wx.EVT_CHAR, self.EvtChar)
        self.Bind(wx.EVT_COMBOBOX, self.EvtCombobox)
        self.Bind(wx.EVT_KILL_FOCUS, self.EvtFillFocus)

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

    def EvtCombobox(self, event):
        self.ignoreEvtText = True
        event.Skip()

    def EvtChar(self, event):
        if event.GetKeyCode() == 8:
            self.ignoreEvtText = True
        event.Skip()

    def EvtText(self, event):
        if self.ignoreEvtText:
            self.ignoreEvtText = False
            return
        currentText = event.GetString()
        found = False
        for index in range(self.GetCount()):
            choice = self.GetString(index)
            if choice.lower().startswith(currentText.lower()):
                self.ignoreEvtText = True
                self.SetValue(choice)
                self.SetInsertionPoint(len(currentText))
                if 'phoenix' in wx.PlatformInfo:
                    self.SetTextSelection(len(currentText), len(choice))
                else:
                    self.SetMark(len(currentText), len(choice))
                found = True
                break
        if not found:
            event.Skip()

    def EvtFillFocus(self, event):
        choice = self.GetValue()
        self.SetStringSelection(choice)
        if self.FindString(choice) == -1:
            self.SetValue("")
        if event is not None:
            event.Skip()

    def GetValeur(self):
        """Permet d'obtenir la valeur en cours de saisie avec wx.EVT_TEXT."""
        choice = self.GetValue()
        for index in range(self.GetCount()):
            if self.GetString(index) == choice:
                return index
        return -1


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="panel_test")
        self.ctrl1 = CTRL(panel)
        self.ctrl1.SetItems([_(u"Bonjour"), _(u"Maison"), _(u"Voiture")])
        self.ctrl2 = CTRL(panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl1, 0, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(2))
        sizer.Add(self.ctrl2, 0, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(2))
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
