#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-17 Ivan LUCAS
# Licence:          Licence GNU GPL
#-----------------------------------------------------------

import wx
import GestionDB

from Utils.UTILS_Traduction import _
from Utils import UTILS_StyleRepens as Style
from Ctrl import CTRL_ActionRepens


class CTRL(wx.CheckListBox):
    """Liste à cocher alignée sur le CSS Repens."""

    def __init__(self, parent):
        wx.CheckListBox.__init__(self, parent, -1)
        self.parent = parent
        self.listeDonnees = []
        self.dictDonnees = {}
        Style.appliquer_liste(self)
        self.SetMinSize((Style.px(180), Style.px(92)))

    def SetDonnees(self, listeDonnees=None, trier=False, cocher=False):
        if listeDonnees is None:
            listeDonnees = []
        self.listeDonnees = listeDonnees
        listeLabels = []
        for dictTemp in listeDonnees:
            listeLabels.append((dictTemp["label"], dictTemp))

        if trier is True:
            listeLabels.sort()

        self.dictDonnees = {}
        self.Clear()
        for index, (label, dictTemp) in enumerate(listeLabels):
            self.Append(label)
            if cocher is True:
                self.Check(index)
            self.dictDonnees[index] = dictTemp

    def GetIDcoches(self):
        listeIDcoches = []
        for index, dictItem in self.dictDonnees.items():
            if self.IsChecked(index):
                listeIDcoches.append(dictItem["ID"])
        return listeIDcoches

    def CocherTout(self):
        for index in self.dictDonnees:
            self.Check(index)

    def CocherRien(self):
        for index in self.dictDonnees:
            self.Check(index, False)

    def SetIDcoches(self, listeIDcoches=None):
        if listeIDcoches is None:
            listeIDcoches = []
        for index, dictItem in self.dictDonnees.items():
            self.Check(index, dictItem["ID"] in listeIDcoches)

    def GetLabelsCoches(self):
        listeLabels = []
        listeID = self.GetIDcoches()
        for dictItem in self.dictDonnees.values():
            if dictItem["ID"] in listeID:
                listeLabels.append(dictItem["label"])
        return ", ".join(listeLabels)


class Panel(wx.Panel):
    """Checklist et commandes compactes, sans colonne latérale de boutons."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        self.parent = parent
        Style.appliquer_fenetre(self, "surface")

        self.ctrl_liste = CTRL(self)
        self.bouton_cocher_tout = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Tout cocher"),
            variante="ghost",
            tooltip=_(u"Cocher tous les éléments"),
        )
        self.bouton_cocher_rien = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Tout décocher"),
            variante="ghost",
            tooltip=_(u"Décocher tous les éléments"),
        )

        self.__do_layout()
        self.Bind(wx.EVT_BUTTON, self.OnBoutonCocherTout, self.bouton_cocher_tout)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonCocherRien, self.bouton_cocher_rien)

        listeFonctions = ["SetDonnees", "GetIDcoches", "CocherTout", "CocherRien", "SetIDcoches", "GetLabelsCoches"]
        for nomFonction in listeFonctions:
            setattr(self, nomFonction, getattr(self.ctrl_liste, nomFonction))

    def __do_layout(self):
        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_cocher_tout, 0, wx.RIGHT, Style.espace(1))
        actions.Add(self.bouton_cocher_rien, 0)
        actions.AddStretchSpacer(1)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(actions, 0, wx.EXPAND | wx.BOTTOM, Style.espace(1))
        principal.Add(self.ctrl_liste, 1, wx.EXPAND)
        self.SetSizer(principal)
        self.Layout()

    def OnBoutonCocherTout(self, event=None):
        self.ctrl_liste.CocherTout()

    def OnBoutonCocherRien(self, event=None):
        self.ctrl_liste.CocherRien()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        Style.appliquer_fenetre(panel)
        self.ctrl = Panel(panel)
        boutonTest = wx.Button(panel, -1, _(u"Test"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, Style.espace(2))
        sizer.Add(boutonTest, 0, wx.ALL, Style.espace(2))
        panel.SetSizer(sizer)
        cadre = wx.BoxSizer(wx.VERTICAL)
        cadre.Add(panel, 1, wx.EXPAND)
        self.SetSizer(cadre)
        self.SetSize((900, 500))
        self.Layout()
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnBoutonTest, boutonTest)
        self.MAJ()
        self.ctrl.CocherTout()

    def MAJ(self, IDactivite=1):
        DB = GestionDB.DB()
        req = """SELECT IDgroupe, IDactivite, nom
        FROM groupes
        WHERE IDactivite=%d
        ORDER BY ordre;""" % IDactivite
        DB.ExecuterReq(req)
        listeGroupes = DB.ResultatReq()
        DB.Close()

        listeDonnees = []
        for IDgroupe, IDactivite, nom in listeGroupes:
            listeDonnees.append({"ID": IDgroupe, "label": nom, "IDactivite": IDactivite})
        self.ctrl.SetDonnees(listeDonnees)

    def OnBoutonTest(self, event):
        print(self.ctrl.GetLabelsCoches())


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
