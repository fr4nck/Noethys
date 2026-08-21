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
import GestionDB

from Utils.UTILS_Traduction import _
from Utils import UTILS_StyleRepens as Style
from Ctrl import CTRL_Bouton_image


class CTRL_Choix(wx.Choice):
    def __init__(self, parent, IDcompte_bancaire=None):
        wx.Choice.__init__(self, parent, -1)
        self.parent = parent
        self.IDcompte_bancaire = IDcompte_bancaire
        Style.appliquer_saisie(self)
        self.MAJ()

    def MAJ(self):
        listeItems = self.GetListeDonnees()
        self.Enable(bool(listeItems) and self.IDcompte_bancaire is not None)
        self.SetItems(listeItems)

    def GetListeDonnees(self):
        listeItems = [u""]
        self.dictDonnees = {0: {"ID": None}}
        if self.IDcompte_bancaire is None:
            return listeItems
        DB = GestionDB.DB()
        req = """SELECT IDreleve, nom, date_debut, date_fin
        FROM compta_releves
        WHERE IDcompte_bancaire=%d
        ORDER BY date_debut; """ % self.IDcompte_bancaire
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        for index, (IDreleve, nom, date_debut, date_fin) in enumerate(listeDonnees, start=1):
            self.dictDonnees[index] = {"ID": IDreleve}
            listeItems.append(nom)
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


class CTRL(wx.Panel):
    def __init__(self, parent, IDcompte_bancaire=None, afficherBouton=True):
        wx.Panel.__init__(self, parent, id=-1, name="ctrl_saisie_releve_bancaire", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.afficherBouton = afficherBouton
        Style.appliquer_fenetre(self, "surface")
        self.ctrl_releve = CTRL_Choix(self, IDcompte_bancaire=IDcompte_bancaire)

        self.bouton_releve = None
        if self.afficherBouton is True:
            taille = Style.taille_icone("inline")
            self.bouton_releve = CTRL_Bouton_image.CTRL(
                self,
                texte="",
                iconeFluent="edit",
                tailleImage=(taille, taille),
            )
            self.Bind(wx.EVT_BUTTON, self.OnBoutonReleve, self.bouton_releve)
            self.bouton_releve.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour accéder à la gestion des relevés bancaires")))

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.ctrl_releve, 1, wx.EXPAND)
        if self.bouton_releve is not None:
            sizer.Add(self.bouton_releve, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, Style.espace(1))
        self.SetSizer(sizer)
        self.Layout()

    def OnBoutonReleve(self, event):
        IDreleve = self.ctrl_releve.GetID()
        from Dlg import DLG_Releves_compta
        dlg = DLG_Releves_compta.Dialog(self)
        dlg.ShowModal()
        dlg.Destroy()
        self.ctrl_releve.MAJ()
        self.ctrl_releve.SetID(IDreleve)

    def SetIDcompte_bancaire(self, IDcompte_bancaire=None):
        self.ctrl_releve.IDcompte_bancaire = IDcompte_bancaire

    def SetID(self, ID=0):
        self.ctrl_releve.SetID(ID)

    def GetID(self):
        return self.ctrl_releve.GetID()

    def MAJ(self):
        IDreleve = self.ctrl_releve.GetID()
        self.ctrl_releve.MAJ()
        self.ctrl_releve.SetID(IDreleve)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="panel_test")
        Style.appliquer_fenetre(panel)
        self.ctrl1 = CTRL(panel)
        self.ctrl2 = CTRL(panel, afficherBouton=False)
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
