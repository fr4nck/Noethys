#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Page Repens de consultation des produits."""

import wx

from Ctrl import CTRL_ActionRepens
from Ctrl import CTRL_OutilsListeRepens
from Ol import OL_Produits
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

        self.ctrl_listview = OL_Produits.ListView(
            self,
            id=-1,
            on_double_click="consultation",
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES | wx.BORDER_NONE,
        )
        self.ctrl_listview.SetMinSize((50, 50))
        UTILS_ListesRepens.Configurer(self.ctrl_listview)
        self.ctrl_recherche = CTRL_OutilsListeRepens.CTRL(
            self, listview=self.ctrl_listview, texteDefaut=_(u"Rechercher un produit…")
        )
        self.bouton_consulter = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Consulter"),
            icone="edit",
            variante="primaire",
            tooltip=_(u"Ouvrir la fiche du produit sélectionné"),
        )
        self.Bind(wx.EVT_BUTTON, self.ctrl_listview.Consulter, self.bouton_consulter)

        marge = max(int(bordure or 0), UTILS_UIMetrics.spacing(2))
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(self.ctrl_recherche, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, marge)
        commandes = wx.WrapSizer(wx.HORIZONTAL)
        commandes.Add(self.bouton_consulter, 0, wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        principal.Add(commandes, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, marge)
        principal.Add(self.ctrl_listview, 1, wx.EXPAND | wx.ALL, marge)
        self.SetSizer(principal)
        self.Layout()

    def MAJ(self):
        self.ctrl_listview.MAJ()
