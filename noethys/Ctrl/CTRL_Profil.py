#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-17 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import ast
import six
import wx

import GestionDB
from Ctrl import CTRL_ActionRepens
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _


class CTRL_Choix_profil(wx.Choice):
    def __init__(self, parent, categorie=""):
        wx.Choice.__init__(self, parent, -1)
        self.parent = parent
        self.categorie = categorie
        self.defaut = None
        try:
            self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
            self.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
            self.SetMinSize((UTILS_UIMetrics.px(110), UTILS_UIMetrics.action_target("compact")))
        except Exception:
            pass
        self.MAJ()
        if len(self.dictDonnees) > 0:
            self.Select(0)

    def MAJ(self):
        selectionActuelle = self.GetID()
        listeItems = self.GetListeDonnees()
        self.Enable(len(listeItems) > 1)
        self.SetItems(listeItems)
        self.SetID(selectionActuelle)

    def GetListeDonnees(self):
        listeItems = [_(u"Aucun profil")]
        self.dictDonnees = {0: None}
        DB = GestionDB.DB()
        req = """SELECT IDprofil, label, defaut
        FROM profils
        WHERE categorie='%s'
        ORDER BY label;""" % self.categorie
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        self.defaut = None
        for index, (IDprofil, label, defaut) in enumerate(listeDonnees, start=1):
            if defaut == 1:
                self.defaut = IDprofil
            listeItems.append(label)
            self.dictDonnees[index] = IDprofil
        return listeItems

    def SetID(self, ID=None):
        for index, IDprofil in self.dictDonnees.items():
            if IDprofil is not None and IDprofil == ID:
                self.SetSelection(index)
                return
        self.SetSelection(0)

    def GetID(self):
        index = self.GetSelection()
        if index == -1:
            return None
        try:
            return self.dictDonnees[index]
        except Exception:
            return None

    def SetOnDefaut(self):
        self.SetID(self.defaut)
        return True


class CTRL(wx.Panel):
    """Sélection d'un profil avec commandes Repens, API historique conservée."""

    def __init__(self, parent, categorie=""):
        wx.Panel.__init__(self, parent, id=-1, name="ctrl_profil", style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        self.parent = parent
        self.categorie = categorie
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_low"))

        self.ctrl_choix_profil = CTRL_Choix_profil(self, categorie=categorie)
        self.bouton_gestion = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Gérer"),
            icone="settings",
            variante="ghost",
            tooltip=_(u"Gérer les profils de configuration"),
        )
        self.bouton_enregistrer = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Enregistrer"),
            icone="check",
            variante="secondaire",
            tooltip=_(u"Enregistrer la configuration dans le profil sélectionné"),
        )

        self.Bind(wx.EVT_CHOICE, self.OnChoixProfil, self.ctrl_choix_profil)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonGestion, self.bouton_gestion)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonEnregistrer, self.bouton_enregistrer)
        self.ctrl_choix_profil.SetToolTip(wx.ToolTip(_(u"Sélectionner un profil de configuration")))

        sizer = wx.WrapSizer(wx.HORIZONTAL)
        sizer.Add(self.ctrl_choix_profil, 1, wx.EXPAND | wx.RIGHT | wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        sizer.Add(self.bouton_gestion, 0, wx.RIGHT | wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        sizer.Add(self.bouton_enregistrer, 0, wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        self.SetSizer(sizer)
        self.Layout()

    def OnBoutonGestion(self, event=None):
        from Dlg import DLG_Profils_parametres
        dlg = DLG_Profils_parametres.Dialog(self, categorie=self.categorie)
        dlg.ShowModal()
        dernierProfilCree = dlg.GetDernierProfilCree()
        dlg.Destroy()
        self.ctrl_choix_profil.MAJ()
        if dernierProfilCree is not None:
            self.ctrl_choix_profil.SetID(dernierProfilCree)

    def OnBoutonEnregistrer(self, event=None):
        self.Recevoir_parametres()

    def GetIDprofil(self):
        return self.ctrl_choix_profil.GetID()

    def SetOnDefaut(self):
        if self.ctrl_choix_profil.SetOnDefaut() is True:
            self.OnChoixProfil()

    def OnChoixProfil(self, event=None):
        IDprofil = self.GetIDprofil()
        dictParametres = None if IDprofil is None else GetParametres(IDprofil=IDprofil)
        self.Envoyer_parametres(dictParametres)

    def Enregistrer(self, dictParametres=None):
        if dictParametres is None:
            dictParametres = {}
        IDprofil = self.GetIDprofil()
        if IDprofil is None:
            IDprofil = self.Proposer_creation_profil()
            if IDprofil in (None, False):
                return False
        SetParametres(categorie="profil_%s" % self.categorie, dictParametres=dictParametres, IDprofil=IDprofil)

    def ViderProfil(self):
        IDprofil = self.GetIDprofil()
        if IDprofil is not None:
            DB = GestionDB.DB()
            DB.ReqDEL("profils_parametres", "IDprofil", IDprofil)
            DB.Close()

    def Proposer_creation_profil(self):
        dlg = wx.MessageDialog(
            self,
            _(u"Vous n'avez sélectionné aucun profil pour enregistrer votre configuration.\n\nSouhaitez-vous créer un nouveau profil maintenant ?"),
            _(u"Créer un profil de configuration"),
            wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL | wx.ICON_QUESTION,
        )
        reponse = dlg.ShowModal()
        dlg.Destroy()
        if reponse != wx.ID_YES:
            return False

        dlg = wx.TextEntryDialog(
            self,
            _(u"Saisissez le nom du nouveau profil de configuration :"),
            _(u"Saisie d'un profil"),
            u"",
        )
        if dlg.ShowModal() == wx.ID_OK:
            label = dlg.GetValue()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return False

        if label == "":
            dlg = wx.MessageDialog(
                self,
                _(u"Le nom que vous avez saisi n'est pas valide."),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_EXCLAMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False

        DB = GestionDB.DB()
        defaut = 1 if len(self.ctrl_choix_profil.dictDonnees) == 1 else 0
        listeDonnees = [("label", label), ("categorie", self.categorie), ("defaut", defaut)]
        IDprofil = DB.ReqInsert("profils", listeDonnees)
        DB.Close()
        self.ctrl_choix_profil.MAJ()
        self.ctrl_choix_profil.SetID(IDprofil)
        return IDprofil

    def Envoyer_parametres(self, dictParametres=None):
        """À surcharger : envoi des paramètres du profil sélectionné."""
        pass

    def Recevoir_parametres(self):
        """À surcharger : récupération des paramètres à enregistrer."""
        pass


def SetParametres(categorie="", dictParametres=None, IDprofil=None):
    if dictParametres is None:
        dictParametres = {}
    DB = GestionDB.DB()
    if DB.echec == 1:
        return False

    req = """SELECT IDparametre, nom, parametre, type_donnee FROM profils_parametres WHERE IDprofil=%d;""" % IDprofil
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    dictDonnees = {}
    for IDparametre, nom, parametre, type_donnee in listeDonnees:
        dictDonnees[nom] = parametre

    listeAjouts = []
    listeModifications = []
    for nom, valeur in dictParametres.items():
        type_donnee = type(valeur)
        if type_donnee in (str, six.text_type):
            type_donnee = "texte"
        else:
            type_donnee = "autre"
            valeur = six.text_type(valeur)

        if nom in dictDonnees:
            if dictDonnees[nom] != valeur:
                listeModifications.append((valeur, type_donnee, nom, IDprofil))
        else:
            listeAjouts.append((nom, valeur, type_donnee, IDprofil))

    if listeModifications:
        DB.Executermany(
            "UPDATE profils_parametres SET parametre=?, type_donnee=? WHERE nom=? and IDprofil=?",
            listeModifications,
            commit=False,
        )
    if listeAjouts:
        DB.Executermany(
            "INSERT INTO profils_parametres (nom, parametre, type_donnee, IDprofil) VALUES (?, ?, ?, ?)",
            listeAjouts,
            commit=False,
        )
    if listeModifications or listeAjouts:
        DB.Commit()
    DB.Close()


def GetParametres(IDprofil=None):
    DB = GestionDB.DB()
    if DB.echec == 1:
        return {}

    req = """SELECT IDparametre, nom, parametre, type_donnee FROM profils_parametres WHERE IDprofil=%d;""" % IDprofil
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()

    dictResultats = {}
    for IDparametre, nom, parametre, type_donnee in listeDonnees:
        if type_donnee != "texte":
            parametre = ast.literal_eval(six.text_type(parametre))
        dictResultats[nom] = parametre
    return dictResultats


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="panel_test")
        self.ctrl = CTRL(panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(2))
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
