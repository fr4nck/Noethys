#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Cockpit Locations en navigation Repens.

Les quatre écrans métier historiques sont conservés, mais le Toolbook 32 px et
son chrome daté disparaissent au profit du même notebook AUI que le reste du
cockpit.
"""

import wx
import wx.lib.agw.aui as aui

from Dlg import DLG_Categories_produits_images
from Dlg import DLG_Produits_liste
from Dlg import DLG_Locations
from Dlg import DLG_Locations_demandes
from Utils import UTILS_Aui
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils import UTILS_Utilisateurs
from Utils.UTILS_Traduction import _


class Panel(wx.Panel):
    def __init__(self, parent, IDfamille=None):
        wx.Panel.__init__(self, parent, id=-1, name="DLG_Tableau_bord_locations_Repens", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDfamille = IDfamille
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        self.notebook = aui.AuiNotebook(
            self,
            agwStyle=aui.AUI_NB_TAB_MOVE | aui.AUI_NB_SCROLL_BUTTONS,
        )
        self.notebook.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
        UTILS_Aui.ConfigurerNotebook(self.notebook)

        bordure = UTILS_UIMetrics.spacing(1)
        self.listePages = [
            ("images", _(u"Images"), DLG_Categories_produits_images.Panel(self.notebook, bordure=bordure)),
            ("produits", _(u"Produits"), DLG_Produits_liste.Panel(self.notebook, bordure=bordure)),
            ("locations", _(u"Locations"), DLG_Locations.Panel(self.notebook, bordure=bordure)),
            ("demandes", _(u"Demandes"), DLG_Locations_demandes.Panel(self.notebook, bordure=bordure)),
        ]
        for code, label, ctrl in self.listePages:
            self.notebook.AddPage(ctrl, label)
        self.notebook.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(self.notebook, 1, wx.EXPAND | wx.ALL, UTILS_UIMetrics.spacing(1))
        self.SetSizer(principal)
        self.Layout()

    def OnPageChanged(self, event):
        index = event.GetSelection()
        self.MAJpage(index)
        event.Skip()

    def MAJpage(self, index=0):
        if index < 0 or index >= len(self.listePages):
            return
        page = self.listePages[index][2]
        if hasattr(page, "MAJ"):
            page.MAJ()

    def IsLectureAutorisee(self):
        return UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel(
            "familles_locations", "consulter", afficheMessage=False
        )

    def MAJ(self):
        index = self.notebook.GetSelection()
        self.MAJpage(index)
        self.Refresh()
