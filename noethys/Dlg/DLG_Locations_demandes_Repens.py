#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Page Repens des demandes de locations."""

import wx

from Ctrl import CTRL_ActionRepens
from Ctrl import CTRL_OutilsListeRepens
from Ol import OL_Locations_demandes
from Utils import UTILS_Interface
from Utils import UTILS_ListesRepens
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _


class Panel(wx.Panel):
    def __init__(self, parent, bordure=0):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        self.parent = parent
        self.bordure = bordure
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        self.check_attente_avec_possibilites = wx.CheckBox(self, -1, _(u"Avec disponibilités"))
        self.check_attente_sans_possibilites = wx.CheckBox(self, -1, _(u"Sans disponibilités"))
        self.check_attente_refusees = wx.CheckBox(self, -1, _(u"Refusées"))
        self.check_attente_attribuees = wx.CheckBox(self, -1, _(u"Attribuées"))
        self.check_attente_avec_possibilites.SetValue(True)
        self.check_attente_sans_possibilites.SetValue(True)

        for ctrl in (
            self.check_attente_avec_possibilites,
            self.check_attente_sans_possibilites,
            self.check_attente_refusees,
            self.check_attente_attribuees,
        ):
            try:
                ctrl.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface_variant"))
            except Exception:
                pass
            self.Bind(wx.EVT_CHECKBOX, self.OnCheckOptions, ctrl)

        self.check_attente_avec_possibilites.SetToolTip(wx.ToolTip(_(u"Inclure les demandes en attente avec disponibilités")))
        self.check_attente_sans_possibilites.SetToolTip(wx.ToolTip(_(u"Inclure les demandes en attente sans disponibilités")))
        self.check_attente_refusees.SetToolTip(wx.ToolTip(_(u"Inclure les demandes refusées")))
        self.check_attente_attribuees.SetToolTip(wx.ToolTip(_(u"Inclure les demandes déjà attribuées")))

        self.ctrl_listview = OL_Locations_demandes.ListView(
            self,
            id=-1,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES | wx.BORDER_NONE,
        )
        self.ctrl_listview.SetMinSize((50, 50))
        UTILS_ListesRepens.Configurer(self.ctrl_listview)
        self.ctrl_recherche = CTRL_OutilsListeRepens.CTRL(
            self, listview=self.ctrl_listview, texteDefaut=_(u"Rechercher une demande…")
        )

        self.bouton_ajouter = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Ajouter"),
            icone="add",
            variante="primaire",
            tooltip=_(u"Ajouter une demande de location"),
        )
        self.bouton_modifier = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Modifier"),
            icone="edit",
            tooltip=_(u"Modifier la demande sélectionnée"),
        )
        self.bouton_supprimer = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Supprimer"),
            icone="delete",
            variante="danger",
            tooltip=_(u"Supprimer la demande sélectionnée"),
        )
        self.Bind(wx.EVT_BUTTON, self.ctrl_listview.Ajouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.ctrl_listview.Modifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.ctrl_listview.Supprimer, self.bouton_supprimer)

        marge = max(int(bordure or 0), UTILS_UIMetrics.spacing(2))
        principal = wx.BoxSizer(wx.VERTICAL)
        filtres = wx.WrapSizer(wx.HORIZONTAL)
        for ctrl in (
            self.check_attente_avec_possibilites,
            self.check_attente_sans_possibilites,
            self.check_attente_refusees,
            self.check_attente_attribuees,
        ):
            filtres.Add(ctrl, 0, wx.RIGHT | wx.BOTTOM, UTILS_UIMetrics.spacing(2))
        principal.Add(filtres, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, marge)
        principal.Add(self.ctrl_recherche, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, marge)

        commandes = wx.WrapSizer(wx.HORIZONTAL)
        commandes.Add(self.bouton_ajouter, 0, wx.RIGHT | wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        commandes.Add(self.bouton_modifier, 0, wx.RIGHT | wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        commandes.Add(self.bouton_supprimer, 0, wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        principal.Add(commandes, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, marge)
        principal.Add(self.ctrl_listview, 1, wx.EXPAND | wx.ALL, marge)
        self.SetSizer(principal)
        self.Layout()

    def OnCheckOptions(self, event=None):
        liste_options = []
        if self.check_attente_avec_possibilites.GetValue():
            liste_options.append("disponibilite")
        if self.check_attente_sans_possibilites.GetValue():
            liste_options.append("attente")
        if self.check_attente_refusees.GetValue():
            liste_options.append("refusee")
        if self.check_attente_attribuees.GetValue():
            liste_options.append("attribuee")
        self.ctrl_listview.SetOptions(liste_options)
        self.ctrl_listview.MAJ()

    def MAJ(self):
        self.OnCheckOptions(None)
