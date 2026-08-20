#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Licence :        GNU GPL
#------------------------------------------------------------------------

import wx

from Utils.UTILS_Traduction import _
from Utils import UTILS_Config


VALEURS_ECHELLE = (80, 90, 100, 110, 125, 150, 175, 200)
CLE_CONFIG = "interface_echelle_pct"


def NormaliseEchelle(valeur, defaut=100):
    try:
        valeur = int(valeur)
    except (TypeError, ValueError):
        valeur = defaut
    return min(VALEURS_ECHELLE, key=lambda item: abs(item - valeur))


def GetEchelle():
    return NormaliseEchelle(UTILS_Config.GetParametre(CLE_CONFIG, 100))


def SetEchelle(valeur):
    valeur = NormaliseEchelle(valeur)
    UTILS_Config.SetParametre(CLE_CONFIG, valeur)
    return valeur


class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, title=_(u"Échelle de l'interface"), style=wx.DEFAULT_DIALOG_STYLE)

        self.label = wx.StaticText(self, -1, _(u"Agrandissement de l'interface :"))
        self.choix = wx.Choice(self, -1, choices=[u"%d %%" % valeur for valeur in VALEURS_ECHELLE])
        valeur_actuelle = GetEchelle()
        self.choix.SetSelection(VALEURS_ECHELLE.index(valeur_actuelle))

        self.info = wx.StaticText(
            self,
            -1,
            _(u"Le nouveau pourcentage sera appliqué au prochain démarrage de Noethys."),
        )

        self.bouton_ok = wx.Button(self, wx.ID_OK, _(u"Valider"))
        self.bouton_annuler = wx.Button(self, wx.ID_CANCEL, _(u"Annuler"))

        grille = wx.FlexGridSizer(rows=1, cols=2, vgap=8, hgap=8)
        grille.Add(self.label, 0, wx.ALIGN_CENTER_VERTICAL)
        grille.Add(self.choix, 0, wx.EXPAND)
        grille.AddGrowableCol(1)

        boutons = wx.StdDialogButtonSizer()
        boutons.AddButton(self.bouton_ok)
        boutons.AddButton(self.bouton_annuler)
        boutons.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(grille, 0, wx.ALL | wx.EXPAND, 12)
        sizer.Add(self.info, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 12)
        sizer.Add(boutons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT, 12)
        self.SetSizerAndFit(sizer)
        self.SetMinSize((440, -1))
        self.CenterOnParent()

    def GetValeur(self):
        return VALEURS_ECHELLE[self.choix.GetSelection()]


def Ouvrir(parent):
    dlg = Dialog(parent)
    resultat = dlg.ShowModal()
    valeur = None
    if resultat == wx.ID_OK:
        valeur = SetEchelle(dlg.GetValeur())
    dlg.Destroy()
    return valeur
