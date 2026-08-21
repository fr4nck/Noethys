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

from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Calendrier
from Utils import UTILS_Dialogs
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _


class Dialog(wx.Dialog):
    """Sélecteur de date commun, responsive et cohérent avec Repens."""

    def __init__(self, parent):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            name="DLG_Calendrier_simple",
            title=_(u"Sélectionner une date"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        )
        self.parent = parent
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        self.ctrl_calendrier = CTRL_Calendrier.CTRL(
            self,
            afficheAujourdhui=False,
            typeCalendrier="annuel",
            afficheBoutonAnnuel=True,
            multiSelections=False,
        )
        self.ctrl_calendrier.Bind(CTRL_Calendrier.EVT_SELECT_DATES, self.OnDateSelected)

        # Le bouton OK reste disponible pour compatibilité avec d'éventuels
        # appels externes, mais la sélection d'une date valide immédiatement.
        self.bouton_ok = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Valider"),
            iconeFluent="check",
        )
        self.bouton_ok.Hide()
        self.bouton_annuler = CTRL_Bouton_image.CTRL(
            self,
            id=wx.ID_CANCEL,
            texte=_(u"Annuler"),
            iconeFluent="dismiss",
        )
        self.bouton_aide = CTRL_Bouton_image.CTRL(
            self,
            texte=_(u"Aide"),
            iconeFluent="help",
        )
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Obtenir de l'aide sur le calendrier")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Fermer sans sélectionner de date")))

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)

        marge = UTILS_UIMetrics.spacing(3)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(self.ctrl_calendrier, 1, wx.EXPAND | wx.ALL, marge)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_aide, 0)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_ok, 0, wx.LEFT, UTILS_UIMetrics.spacing(1))
        actions.Add(self.bouton_annuler, 0, wx.LEFT, UTILS_UIMetrics.spacing(1))
        principal.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, marge)

        self.SetSizer(principal)
        self.SetMinSize((UTILS_UIMetrics.px(520), UTILS_UIMetrics.px(380)))
        self.SetSize((UTILS_UIMetrics.px(760), UTILS_UIMetrics.px(560)))
        UTILS_Dialogs.AjusteDansEcran(self)
        self.Layout()
        if parent is not None:
            self.CentreOnParent()
        else:
            self.CentreOnScreen()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Calendrier1")

    def OnDateSelected(self, event):
        self.EndModal(wx.ID_OK)

    def GetDate(self):
        selections = self.ctrl_calendrier.GetSelections()
        return selections[0] if selections else None

    def SetDate(self, date=None):
        self.ctrl_calendrier.SelectJours([date])

    def OnBoutonOk(self, event):
        self.EndModal(wx.ID_OK)


if __name__ == u"__main__":
    app = wx.App(0)
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
