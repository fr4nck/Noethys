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
import GestionDB

from Utils.UTILS_Traduction import _
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics


class CTRL_Choice(wx.Choice):
    """Choix d'un modèle de document avec métriques desktop communes."""

    def __init__(self, parent, categorie=""):
        wx.Choice.__init__(self, parent, -1)
        self.parent = parent
        self.categorie = categorie
        self.defaut = None
        self._AppliqueStyle()
        self.MAJ()

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

    def SetCategorie(self, categorie=""):
        self.categorie = categorie
        self.defaut = None
        self.MAJ()
        self.SetID(self.defaut)

    def MAJ(self):
        selectionActuelle = self.GetID()
        listeItems = self.GetListeDonnees()
        self.Enable(bool(listeItems))
        self.SetItems(listeItems)
        if selectionActuelle is not None:
            self.SetID(selectionActuelle)
        else:
            self.SetID(self.defaut)

    def GetListeDonnees(self):
        listeItems = []
        self.dictDonnees = {}
        DB = GestionDB.DB()
        req = """SELECT IDmodele, nom, largeur, hauteur, observations, defaut
        FROM documents_modeles
        WHERE categorie='%s'
        ORDER BY nom;""" % self.categorie
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        for index, (IDmodele, nom, largeur, hauteur, observations, defaut) in enumerate(listeDonnees):
            listeItems.append(nom)
            self.dictDonnees[index] = {"ID": IDmodele}
            if defaut == 1:
                self.defaut = IDmodele
        return listeItems

    def SetID(self, ID=None):
        for index, values in self.dictDonnees.items():
            if values is not None and values["ID"] == ID:
                self.SetSelection(index)

    def GetID(self):
        index = self.GetSelection()
        if index == -1:
            return None
        return self.dictDonnees[index]["ID"]


def DemandeModele(categorie=""):
    IDmodele = None
    DB = GestionDB.DB()
    req = """SELECT IDmodele, nom, defaut
    FROM documents_modeles
    WHERE categorie='%s'
    ORDER BY nom;""" % categorie
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    listeLabels = []
    indexDefaut = None
    for index, (IDmodele, nom, defaut) in enumerate(listeDonnees):
        listeLabels.append(nom)
        if defaut == 1:
            indexDefaut = index
    dlg = wx.SingleChoiceDialog(None, _(u"Veuillez sélectionner un modèle dans la liste :"), _(u"Sélection d'un modèle"), listeLabels, wx.CHOICEDLG_STYLE)
    if indexDefaut is not None:
        dlg.SetSelection(indexDefaut)
    if dlg.ShowModal() == wx.ID_OK:
        selection = dlg.GetSelection()
        IDmodele = listeDonnees[selection][0]
        dlg.Destroy()
    else:
        dlg.Destroy()
        dlg = wx.MessageDialog(None, _(u"Sans modèle, l'édition est annulée !"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
        dlg.ShowModal()
        dlg.Destroy()
        return None
    return IDmodele


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        self.ctrl = CTRL_Choice(panel, categorie="facture")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 0, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(2))
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
