#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-12 Ivan LUCAS
# Licence:          Licence GNU GPL
#------------------------------------------------------------------------

import wx

import GestionDB
from Ctrl import CTRL_ActionRepens
from Ctrl import CTRL_FenetreRepens
from Ol import OL_Mandats
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


class Dialog(CTRL_FenetreRepens.Dialog):
    """Activation du prélèvement sur le shell commun Repens."""

    def __init__(self, parent, IDfamille=None):
        self.parent = parent
        self.IDfamille = IDfamille

        intro = _(u"Saisissez les coordonnées bancaires du compte de la famille à débiter afin d'activer le prélèvement automatique.")
        titre = _(u"Prélèvement automatique")
        CTRL_FenetreRepens.Dialog.__init__(
            self,
            parent,
            titre=titre,
            intro=intro,
            nomImage="Images/32x32/Prelevement.png",
            taille=(760, 560),
            taille_min=(620, 440),
        )

        self.section_activation = self.AjouterSection(
            _(u"Activation"),
            _(u"Activez ou désactivez le prélèvement pour cette famille."),
            proportion=0,
        )
        parent_activation = self.section_activation.GetContenu()
        self.label_activation = wx.StaticText(parent_activation, -1, _(u"Prélèvement activé"))
        Style.appliquer_texte(
            self.label_activation,
            role="body_emphasis",
            role_texte="on_surface",
            role_fond="surface_container_low",
        )
        self.radio_activation_oui = wx.RadioButton(parent_activation, -1, _(u"Oui"), style=wx.RB_GROUP)
        self.radio_activation_non = wx.RadioButton(parent_activation, -1, _(u"Non"))
        self.radio_activation_non.SetValue(True)
        for ctrl in (self.radio_activation_oui, self.radio_activation_non):
            Style.appliquer_texte(
                ctrl,
                role="body",
                role_texte="on_surface",
                role_fond="surface_container_low",
            )

        ligne_activation = wx.BoxSizer(wx.HORIZONTAL)
        ligne_activation.Add(self.label_activation, 0, wx.ALIGN_CENTER_VERTICAL)
        ligne_activation.AddStretchSpacer(1)
        ligne_activation.Add(self.radio_activation_oui, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, Style.espace(2))
        ligne_activation.Add(self.radio_activation_non, 0, wx.ALIGN_CENTER_VERTICAL)
        self.section_activation.GetSizerContenu().Add(ligne_activation, 0, wx.EXPAND)

        self.section_mandats = self.AjouterSection(
            _(u"Mandats SEPA"),
            _(u"Gérez les mandats associés au compte de la famille."),
            proportion=1,
        )
        parent_mandats = self.section_mandats.GetContenu()

        self.bouton_ajouter = CTRL_ActionRepens.CTRL(
            parent_mandats,
            label=_(u"Ajouter"),
            icone="add",
            variante="primaire",
            tooltip=_(u"Ajouter un mandat"),
        )
        self.bouton_modifier = CTRL_ActionRepens.CTRL(
            parent_mandats,
            label=_(u"Modifier"),
            icone="edit",
            tooltip=_(u"Modifier le mandat sélectionné"),
        )
        self.bouton_supprimer = CTRL_ActionRepens.CTRL(
            parent_mandats,
            label=_(u"Supprimer"),
            icone="delete",
            variante="danger",
            tooltip=_(u"Supprimer le mandat sélectionné"),
        )

        ligne_actions = wx.BoxSizer(wx.HORIZONTAL)
        ligne_actions.AddStretchSpacer(1)
        ligne_actions.Add(self.bouton_ajouter, 0, wx.ALIGN_CENTER_VERTICAL)
        ligne_actions.AddSpacer(Style.espace(1))
        ligne_actions.Add(self.bouton_modifier, 0, wx.ALIGN_CENTER_VERTICAL)
        ligne_actions.AddSpacer(Style.espace(1))
        ligne_actions.Add(self.bouton_supprimer, 0, wx.ALIGN_CENTER_VERTICAL)
        self.section_mandats.GetSizerContenu().Add(ligne_actions, 0, wx.EXPAND | wx.BOTTOM, Style.espace(2))

        self.ctrl_listview = OL_Mandats.ListView(
            parent_mandats,
            id=-1,
            IDfamille=self.IDfamille,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES,
        )
        Style.appliquer_liste(self.ctrl_listview)
        self.ctrl_listview.SetMinSize((Style.px(260), Style.px(180)))
        self.ctrl_listview.MAJ()
        self.section_mandats.GetSizerContenu().Add(self.ctrl_listview, 1, wx.EXPAND)

        self.bouton_aide = self.AjouterAction(
            _(u"Aide"),
            callback=self.OnBoutonAide,
            icone="help",
            alignement="gauche",
            tooltip=_(u"Obtenir de l'aide"),
        )
        self.bouton_rib = self.AjouterAction(
            _(u"Ancien RIB"),
            callback=self.OnBoutonRib,
            icone="edit",
            alignement="gauche",
            tooltip=_(u"Paramétrer un RIB pour les anciens prélèvements nationaux"),
        )
        self.bouton_fermer = self.AjouterAction(
            _(u"Valider et fermer"),
            callback=self.OnBoutonFermer,
            icone="check",
            variante="primaire",
            alignement="droite",
            tooltip=_(u"Enregistrer l'activation et fermer"),
        )

        self.radio_activation_oui.SetToolTip(wx.ToolTip(_(u"Activer le prélèvement")))
        self.radio_activation_non.SetToolTip(wx.ToolTip(_(u"Désactiver le prélèvement")))

        self.bouton_ajouter.Bind(wx.EVT_BUTTON, self.Ajouter)
        self.bouton_modifier.Bind(wx.EVT_BUTTON, self.Modifier)
        self.bouton_supprimer.Bind(wx.EVT_BUTTON, self.Supprimer)
        self.Bind(wx.EVT_CLOSE, self.OnBoutonFermer)

        self.Importation()
        self.Finaliser()

    def OnBoutonAide(self, event):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Rglements1")

    def Ajouter(self, event):
        self.ctrl_listview.Ajouter(None)

    def Modifier(self, event):
        self.ctrl_listview.Modifier(None)

    def Supprimer(self, event):
        self.ctrl_listview.Supprimer(None)

    def Importation(self):
        if self.IDfamille is None:
            return
        DB = GestionDB.DB()
        req = """SELECT IDfamille, prelevement_activation
        FROM familles
        WHERE IDfamille=%d;""" % self.IDfamille
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        if len(listeDonnees) == 0:
            return
        _temp, activation = listeDonnees[0]
        if activation == 1:
            self.radio_activation_oui.SetValue(True)

    def OnBoutonFermer(self, event):
        activation = self.radio_activation_oui.GetValue()

        if activation is True:
            if len(self.ctrl_listview.donnees) == 0:
                dlg = wx.MessageDialog(
                    self,
                    _(u"Vous devez saisir au moins un mandat pour pouvoir activer le prélèvement !"),
                    _(u"Erreur de saisie"),
                    wx.OK | wx.ICON_EXCLAMATION,
                )
                dlg.ShowModal()
                dlg.Destroy()
                return
        else:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous confirmez que vous ne souhaitez pas activer le prélèvement automatique ?"),
                _(u"Confirmation"),
                wx.YES_NO | wx.YES_DEFAULT | wx.CANCEL | wx.ICON_QUESTION,
            )
            reponse = dlg.ShowModal()
            dlg.Destroy()
            if reponse != wx.ID_YES:
                return

        activation = 1 if activation is True else None
        DB = GestionDB.DB()
        DB.ReqMAJ("familles", [("prelevement_activation", activation),], "IDfamille", self.IDfamille)
        DB.Close()
        self.EndModal(wx.ID_OK)

    def OnBoutonRib(self, event):
        from Dlg import DLG_Saisie_rib
        dlg = DLG_Saisie_rib.Dialog(self, IDfamille=self.IDfamille)
        dlg.ShowModal()
        dlg.Destroy()


if __name__ == u"__main__":
    app = wx.App(0)
    dialog_1 = Dialog(None, IDfamille=14)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
