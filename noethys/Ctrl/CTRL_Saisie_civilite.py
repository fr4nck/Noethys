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

from Utils.UTILS_Traduction import _
from Utils import UTILS_StyleRepens as Style
from Data import DATA_Civilites as Civilites


LISTE_CIVILITES = Civilites.LISTE_CIVILITES


class Civilite(wx.Choice):
    """Choix de civilité/genre aligné sur le CSS Repens."""

    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1, choices=self.GetListeCivilites())
        self.parent = parent
        Style.appliquer_saisie(self)
        self.SetToolTip(wx.ToolTip(_(u"Sélectionnez ici la civilité de l'individu s'il s'agit\nd'un adulte ou le genre s'il s'agit d'un enfant")))

    def GetListeCivilites(self):
        self.dictCivilites = {}
        listeCivilites = []
        index = 0
        for rubrique, civilites in LISTE_CIVILITES:
            listeCivilites.append(u"--- %s ---" % rubrique)
            self.dictCivilites[index] = {
                "ID": None,
                "type": "rubrique",
                "rubrique": rubrique,
                "civilite": None,
                "abrege": None,
                "photo": None,
                "sexe": None,
            }
            index += 1
            for ID, civiliteLong, civiliteAbrege, photo, sexe in civilites:
                listeCivilites.append(civiliteLong)
                self.dictCivilites[index] = {
                    "ID": ID,
                    "type": "civilite",
                    "rubrique": rubrique,
                    "civilite": civiliteLong,
                    "abrege": civiliteAbrege,
                    "photo": photo,
                    "sexe": sexe,
                }
                index += 1
        return listeCivilites

    def GetIndex(self):
        return self.GetSelection()

    def SetID(self, ID=0):
        for index, values in self.dictCivilites.items():
            if values["ID"] == ID:
                self.SetSelection(index)

    def _GetValeur(self, cle):
        index = self.GetIndex()
        if index == -1:
            return None
        return self.dictCivilites[index][cle]

    def GetID(self):
        return self._GetValeur("ID")

    def GetType(self):
        return self._GetValeur("type")

    def GetRubrique(self):
        return self._GetValeur("rubrique")

    def GetCivilite(self):
        return self._GetValeur("civilite")

    def GetAbrege(self):
        return self._GetValeur("abrege")

    def GetPhoto(self):
        return self._GetValeur("photo")

    def GetSexe(self):
        return self._GetValeur("sexe")


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(panel)
        self.ctrl = Civilite(panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 0, wx.ALL | wx.EXPAND, Style.espace(2))
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
