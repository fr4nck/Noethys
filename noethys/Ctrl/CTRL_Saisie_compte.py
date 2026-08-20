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
import GestionDB

from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics


class CTRL(wx.Choice):
    """Sélecteur de compte bancaire cohérent avec les contrôles de saisie."""

    def __init__(self, parent, IDcompte_bancaire=None, size=(-1, -1)):
        wx.Choice.__init__(self, parent, -1, size=size)
        self.parent = parent
        self.IDdefaut = None
        self._AppliqueStyle()
        self.MAJ()
        self.SetID(IDcompte_bancaire)

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

    def MAJ(self):
        listeItems = self.GetListeDonnees()
        self.Enable(bool(listeItems))
        self.SetItems(listeItems)
        self.SetID(self.IDdefaut)

    def GetListeDonnees(self):
        listeItems = []
        self.dictDonnees = {}
        DB = GestionDB.DB()
        req = """SELECT IDcompte, nom, defaut
        FROM comptes_bancaires
        ORDER BY nom; """
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        for index, (IDcompte, nom, defaut) in enumerate(listeDonnees):
            self.dictDonnees[index] = {"ID": IDcompte}
            listeItems.append(nom)
            if defaut == 1:
                self.IDdefaut = IDcompte
        return listeItems

    def SetID(self, ID=0):
        for index, values in self.dictDonnees.items():
            if values["ID"] == ID:
                self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1:
            return None
        return self.dictDonnees[index]["ID"]


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="panel_test")
        self.ctrl1 = CTRL(panel)
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
