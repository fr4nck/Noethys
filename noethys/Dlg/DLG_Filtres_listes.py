#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import ast
import wx

from Ctrl import CTRL_ActionRepens
from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Profil
from Ol import OL_Filtres_listes
from Utils import UTILS_Dialogs
from Utils import UTILS_Interface
from Utils import UTILS_ListesRepens
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _


class CTRL_profil_perso(CTRL_Profil.CTRL):
    def __init__(self, parent, categorie="", dlg=None):
        CTRL_Profil.CTRL.__init__(self, parent, categorie=categorie)
        self.dlg = dlg

    def Envoyer_parametres(self, dictParametres=None):
        listeFiltres = []
        if dictParametres is not None:
            for index, dictFiltreStr in dictParametres.items():
                listeFiltres.append(ast.literal_eval(dictFiltreStr))
        self.dlg.SetDonnees(listeFiltres)

    def Recevoir_parametres(self):
        listeFiltres = self.dlg.GetDonnees()
        dictParametres = {}
        for index, dictFiltre in enumerate(listeFiltres):
            dictParametres["filtre%d" % index] = str(dictFiltre)
        self.ViderProfil()
        self.Enregistrer(dictParametres)


class Dialog(wx.Dialog):
    def __init__(self, parent, ctrl_listview=None):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            title=_(u"Filtrer"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX,
        )
        self.parent = parent
        self.ctrl_listview = ctrl_listview
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        intro = _(
            u"Ajoutez une ou plusieurs règles de filtre. Le profil de configuration permet de mémoriser et réutiliser vos jeux de filtres."
        )
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(
            self,
            titre=_(u"Filtrer"),
            texte=intro,
            hauteurHtml=30,
            nomImage="Images/32x32/Filtre.png",
        )

        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.splitter.SetMinimumPaneSize(UTILS_UIMetrics.px(150))

        self.panel_liste = wx.Panel(self.splitter, style=wx.BORDER_NONE | wx.TAB_TRAVERSAL)
        self.panel_liste.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))
        self.ctrl_filtres = OL_Filtres_listes.ListView(
            self.panel_liste,
            ctrl_listview=ctrl_listview,
            id=-1,
            name="OL_filtres",
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES | wx.BORDER_NONE,
        )
        UTILS_ListesRepens.Configurer(self.ctrl_filtres)
        self.ctrl_filtres.MAJ()

        self.bouton_ajouter = CTRL_ActionRepens.CTRL(
            self.panel_liste, label=_(u"Ajouter"), icone="add", variante="primaire", tooltip=_(u"Ajouter une règle de filtre")
        )
        self.bouton_modifier = CTRL_ActionRepens.CTRL(
            self.panel_liste, label=_(u"Modifier"), icone="edit", tooltip=_(u"Modifier la règle sélectionnée")
        )
        self.bouton_supprimer = CTRL_ActionRepens.CTRL(
            self.panel_liste, label=_(u"Supprimer"), icone="delete", variante="danger", tooltip=_(u"Supprimer la règle sélectionnée")
        )
        self.bouton_tout_supprimer = CTRL_ActionRepens.CTRL(
            self.panel_liste, label=_(u"Tout effacer"), icone="delete", variante="ghost", tooltip=_(u"Supprimer toutes les règles")
        )

        commandes = wx.WrapSizer(wx.HORIZONTAL)
        for bouton in (
            self.bouton_ajouter,
            self.bouton_modifier,
            self.bouton_supprimer,
            self.bouton_tout_supprimer,
        ):
            commandes.Add(bouton, 0, wx.RIGHT | wx.BOTTOM, UTILS_UIMetrics.spacing(1))

        sizer_liste = wx.BoxSizer(wx.VERTICAL)
        sizer_liste.Add(commandes, 0, wx.EXPAND | wx.BOTTOM, UTILS_UIMetrics.spacing(2))
        sizer_liste.Add(self.ctrl_filtres, 1, wx.EXPAND)
        self.panel_liste.SetSizer(sizer_liste)

        nom_liste = self.ctrl_listview.GetNomModule() if self.ctrl_listview is not None else ""
        self.ctrl_profil = CTRL_profil_perso(
            self.splitter,
            categorie="filtres_%s" % nom_liste,
            dlg=self,
        )
        try:
            self.ctrl_profil.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_low"))
        except Exception:
            pass
        self.splitter.SplitVertically(
            self.panel_liste,
            self.ctrl_profil,
            sashPosition=UTILS_UIMetrics.px(500),
        )
        self.splitter.SetSashGravity(0.76)

        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_(u"Aide"), iconeFluent="help")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_(u"Valider"), iconeFluent="check")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_(u"Annuler"), iconeFluent="dismiss")

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAjouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonModifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonToutSupprimer, self.bouton_tout_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)

        marge = UTILS_UIMetrics.spacing(3)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(self.ctrl_bandeau, 0, wx.EXPAND)
        principal.Add(self.splitter, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, marge)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_aide, 0)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_ok, 0, wx.LEFT, UTILS_UIMetrics.spacing(1))
        actions.Add(self.bouton_annuler, 0, wx.LEFT, UTILS_UIMetrics.spacing(1))
        principal.Add(actions, 0, wx.EXPAND | wx.ALL, marge)
        self.SetSizer(principal)

        self.SetMinSize((UTILS_UIMetrics.px(560), UTILS_UIMetrics.px(380)))
        self.SetSize((UTILS_UIMetrics.px(820), UTILS_UIMetrics.px(520)))
        UTILS_Dialogs.AjusteDansEcran(self)
        self.Layout()
        if parent is not None:
            self.CentreOnParent()
        else:
            self.CentreOnScreen()

    def OnBoutonAjouter(self, event):
        self.ctrl_filtres.Ajouter(None)

    def OnBoutonModifier(self, event):
        self.ctrl_filtres.Modifier(None)

    def OnBoutonSupprimer(self, event):
        self.ctrl_filtres.Supprimer(None)

    def OnBoutonToutSupprimer(self, event):
        self.ctrl_filtres.SupprimerTout()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Filtrer")

    def OnBoutonOk(self, event):
        self.EndModal(wx.ID_OK)

    def SetDonnees(self, listeFiltres=None):
        self.ctrl_filtres.SetDonnees(listeFiltres or [])

    def GetDonnees(self):
        return self.ctrl_filtres.GetDonnees()


if __name__ == '__main__':
    app = wx.App(0)
    dlg = Dialog(None)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
