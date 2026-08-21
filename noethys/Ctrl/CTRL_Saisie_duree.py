#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-15 Ivan LUCAS
# Licence:          Licence GNU GPL
#-----------------------------------------------------------

import datetime
import wx
import six

from Utils.UTILS_Traduction import _
from Utils import UTILS_Dates
from Utils import UTILS_StyleRepens as Style


if 'phoenix' in wx.PlatformInfo:
    validator = wx.Validator
    IsSilent = wx.Validator.IsSilent
else:
    validator = wx.PyValidator
    IsSilent = wx.Validator_IsSilent


CARACT_AUTORISES = "0123456789-:.hH"


class MyValidator(validator):
    def __init__(self):
        validator.__init__(self)
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        return MyValidator()

    def Validate(self, win):
        tc = self.GetWindow()
        val = tc.GetValue()
        for caractere in val:
            if caractere not in CARACT_AUTORISES:
                return False
        return True

    def OnChar(self, event):
        key = event.GetKeyCode()
        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
            return
        if chr(key) in CARACT_AUTORISES:
            event.Skip()
            return
        if not IsSilent():
            wx.Bell()

    def TransferToWindow(self):
        return True

    def TransfertFromWindow(self):
        return True


class CTRL(wx.TextCtrl):
    """Saisie de durée alignée sur le CSS Repens."""

    def __init__(self, parent, separateur="h", font=None, size=(-1, -1), style=wx.TE_PROCESS_ENTER | wx.TE_CENTER):
        wx.TextCtrl.__init__(self, parent, -1, "", size=size, validator=MyValidator(), style=style)
        self.parent = parent
        self.separateur = separateur
        self._AppliqueStyle(font)
        self.SetToolTip(wx.ToolTip(_(u"Saisissez une durée.\n\nExemples de formats acceptés :\n12h45, 6:32, 12.5, 45h, 1725H30")))
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        self.SetValue(datetime.timedelta(0))
        self.oldValeur = self.GetValue()

    def _AppliqueStyle(self, font=None):
        Style.appliquer_saisie(self)
        if font is not None:
            try:
                self.SetFont(font)
            except Exception:
                pass
        try:
            largeur = max(
                Style.px(84),
                self.GetTextExtent("000h00")[0] + Style.espace(4),
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
            self.SetDuree(self.oldValeur)
        else:
            self.SetDuree(self.GetDuree())
            self.oldValeur = self.GetDuree()
        if event is not None:
            event.Skip()

    def Validation(self):
        try:
            self.GetDuree()
        except Exception:
            message = _(u"La durée que vous avez saisi ne semble pas valide.")
            return False, message
        return True, None

    def GetDuree(self, format=datetime.timedelta):
        valeur = wx.TextCtrl.GetValue(self)
        valeur = valeur.replace(' ', '')
        valeur = valeur.replace('h', ':')
        valeur = valeur.replace('H', ':')
        if valeur == ":":
            valeur = None

        try:
            valeur = float(valeur)
            format = float
        except Exception:
            pass

        if format == datetime.timedelta:
            return UTILS_Dates.HeureStrEnDelta(valeur)
        if format == float:
            return datetime.timedelta(hours=valeur)
        return valeur

    def SetDuree(self, duree=None):
        if type(duree) == float:
            td = datetime.timedelta(hours=duree)
        elif type(duree) in (str, six.text_type):
            td = UTILS_Dates.HeureStrEnDelta(duree)
        elif type(duree) == datetime.timedelta:
            td = duree
        else:
            td = datetime.timedelta(0)
        valeur = UTILS_Dates.DeltaEnStr(td, separateur=self.separateur)
        wx.TextCtrl.SetValue(self, valeur)

    def SetValue(self, value=datetime.timedelta(0)):
        self.SetDuree(value)

    def GetValue(self):
        return self.GetDuree()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(panel)
        self.ctrl = CTRL(panel)
        self.bouton = wx.Button(panel, -1, "TEST")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 0, wx.ALL, Style.espace(2))
        sizer.Add(self.bouton, 0, wx.ALL, Style.espace(2))
        panel.SetSizer(sizer)
        cadre = wx.BoxSizer(wx.VERTICAL)
        cadre.Add(panel, 1, wx.EXPAND)
        self.SetSizer(cadre)
        self.Layout()
        self.CentreOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnBouton, self.bouton)

    def OnBouton(self, event):
        self.ctrl.SetValue(13.5)
        print(self.ctrl.GetValue())


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
