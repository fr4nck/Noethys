#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Page Repens de la liste des locations."""

import wx

from Ctrl import CTRL_ActionRepens
from Ctrl import CTRL_OutilsListeRepens
from Ol import OL_Locations
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

        self.ctrl_listview = OL_Locations.ListView(
            self,
            id=-1,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES | wx.BORDER_NONE,
        )
        self.ctrl_listview.SetMinSize((50, 50))
        UTILS_ListesRepens.Configurer(self.ctrl_listview)

        self.ctrl_recherche = CTRL_OutilsListeRepens.CTRL(
            self, listview=self.ctrl_listview, texteDefaut=_(u"Rechercher une location…")
        )
        self.check_locations_actives = wx.CheckBox(self, -1, _(u"Locations en cours uniquement"))
        self.check_locations_actives.SetValue(True)
        self.check_locations_actives.SetToolTip(wx.ToolTip(_(u"Masquer les locations terminées")))
        try:
            self.check_locations_actives.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface_variant"))
        except Exception:
            pass

        self.bouton_ajouter = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Ajouter"),
            icone="add",
            variante="primaire",
            tooltip=_(u"Ajouter une location"),
        )
        self.bouton_modifier = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Modifier"),
            icone="edit",
            tooltip=_(u"Modifier la location sélectionnée"),
        )
        self.bouton_supprimer = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Supprimer"),
            icone="delete",
            variante="danger",
            tooltip=_(u"Supprimer la location sélectionnée"),
        )
        self.bouton_configuration = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Colonnes"),
            icone="settings",
            variante="ghost",
            tooltip=_(u"Configurer les colonnes et l'affichage de la liste"),
        )

        self.Bind(wx.EVT_CHECKBOX, self.OnCheckActives, self.check_locations_actives)
        self.Bind(wx.EVT_BUTTON, self.ctrl_listview.Ajouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.ctrl_listview.Modifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.ctrl_listview.Supprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.ctrl_listview.MenuConfigurerListe, self.bouton_configuration)

        marge = max(int(bordure or 0), UTILS_UIMetrics.spacing(2))
        principal = wx.BoxSizer(wx.VERTICAL)

        ligne_recherche = wx.BoxSizer(wx.HORIZONTAL)
        ligne_recherche.Add(self.ctrl_recherche, 1, wx.EXPAND | wx.RIGHT, UTILS_UIMetrics.spacing(2))
        ligne_recherche.Add(self.check_locations_actives, 0, wx.ALIGN_CENTER_VERTICAL)
        principal.Add(ligne_recherche, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, marge)

        commandes = wx.WrapSizer(wx.HORIZONTAL)
        commandes.Add(self.bouton_ajouter, 0, wx.RIGHT | wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        commandes.Add(self.bouton_modifier, 0, wx.RIGHT | wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        commandes.Add(self.bouton_supprimer, 0, wx.RIGHT | wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        commandes.Add(self.bouton_configuration, 0, wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        principal.Add(commandes, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, marge)
        principal.Add(self.ctrl_listview, 1, wx.EXPAND | wx.ALL, marge)
        self.SetSizer(principal)
        self.Layout()

        self.ctrl_listview.afficher_uniquement_actives = self.check_locations_actives.GetValue()

    def OnCheckActives(self, event=None):
        self.ctrl_listview.afficher_uniquement_actives = self.check_locations_actives.GetValue()
        self.ctrl_listview.MAJ()

    def MAJ(self):
        self.OnCheckActives(None)
