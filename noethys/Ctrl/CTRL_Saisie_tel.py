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

from Utils.UTILS_Traduction import _
from Utils import UTILS_Config
from Utils import UTILS_StyleRepens as Style


class Tel(masked.TextCtrl):
    """Saisie de téléphone compacte alignée sur le CSS Repens."""

    def __init__(self, parent, intitule="", mask="##.##.##.##.##.", size=(-1, -1)):
        self.mask = UTILS_Config.GetParametre("mask_telephone", "##.##.##.##.##.")
        masked.TextCtrl.__init__(self, parent, -1, "", size=size, style=wx.TE_CENTRE, mask=self.mask)
        self.parent = parent
        self._AppliqueStyle()
        self.SetToolTip(wx.ToolTip(_(u"Saisissez un numéro de %s") % intitule))
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

    def _AppliqueStyle(self):
        Style.appliquer_saisie(self)
        try:
            largeur = max(
                Style.px(132),
                self.GetTextExtent("00.00.00.00.00")[0] + Style.espace(4),
            )
            self.SetMinSize((largeur, Style.cible_action("compact")))
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
        if self.mask == "":
            return True, None
        text = self.GetValue()
        if text == "" or text == "  .  .  .  .  .":
            return True, None
        posChiffres = [0, 1, 3, 4, 6, 7, 9, 10, 12, 13]
        for position in posChiffres:
            if text[position].isdigit() is False:
                message = _(u"Le numéro que vous avez saisi ne semble pas valide.")
                return False, message
        return True, None

    def SetNumero(self, numero=""):
        if numero is None:
            return
        try:
            self.SetValue(numero)
        except Exception:
            pass

    def GetNumero(self):
        tel = self.GetValue()
        if tel == "  .  .  .  .  .":
            return None
        return tel


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(panel)
        self.ctrl = Tel(panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 0, wx.ALL, Style.espace(2))
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
