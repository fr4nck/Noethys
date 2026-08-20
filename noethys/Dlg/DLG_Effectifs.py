#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import wx.lib.agw.aui as aui

from Utils.UTILS_Traduction import _
from Utils import UTILS_Aui
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Dlg import DLG_Remplissage
from Dlg import DLG_Recap_evenements
from Dlg import DLG_Nbre_inscrits_2 as DLG_Nbre_inscrits
from Dlg import DLG_Tableau_bord_locations


class CTRL(wx.Panel):
    """Cockpit fréquentation de l'accueil Noethys.

    La logique des quatre vues reste inchangée. Le conteneur fournit seulement
    la hiérarchie visuelle Repens Design et laisse le notebook absorber tout
    l'espace disponible.
    """

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_low"))

        self.ctrl_titre = wx.StaticText(self, label=_(u"Fréquentation & activités"))
        self.ctrl_sous_titre = wx.StaticText(
            self,
            label=_(u"Capacités, consommations, inscriptions et événements"),
        )
        self.ctrl_titre.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        self.ctrl_sous_titre.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface_variant"))

        police = self.ctrl_titre.GetFont()
        police.SetWeight(wx.FONTWEIGHT_BOLD)
        police.SetPointSize(max(police.GetPointSize() + 2, 11))
        self.ctrl_titre.SetFont(police)

        self.notebook = aui.AuiNotebook(
            self,
            agwStyle=(
                aui.AUI_NB_BOTTOM
                | aui.AUI_NB_TAB_EXTERNAL_MOVE
                | aui.AUI_NB_TAB_SPLIT
                | aui.AUI_NB_TAB_MOVE
            ),
        )
        self.notebook.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))

        self.ctrl_remplissage = DLG_Remplissage.Panel(self.notebook)
        self.notebook.AddPage(self.ctrl_remplissage, _(u"Consommations"))
        try:
            self.notebook.SetPageTooltip(0, _(u"État des consommations et des capacités."))
        except Exception:
            pass

        self.ctrl_nbre_inscrits = DLG_Nbre_inscrits.Panel(self.notebook)
        self.notebook.AddPage(self.ctrl_nbre_inscrits, _(u"Inscriptions"))
        try:
            self.notebook.SetPageTooltip(1, _(u"État des inscriptions."))
        except Exception:
            pass

        self.ctrl_evenements = DLG_Recap_evenements.Panel(self.notebook)
        self.notebook.AddPage(self.ctrl_evenements, _(u"Événements"))
        try:
            self.notebook.SetPageTooltip(2, _(u"État des événements."))
        except Exception:
            pass

        self.ctrl_locations = DLG_Tableau_bord_locations.Panel(self.notebook)
        self.notebook.AddPage(self.ctrl_locations, _(u"Locations"))
        try:
            self.notebook.SetPageTooltip(3, _(u"État des locations."))
        except Exception:
            pass

        UTILS_Aui.ConfigurerNotebook(self.notebook)
        self.notebook.Bind(aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
        self.__do_layout()

    def __do_layout(self):
        marge = UTILS_UIMetrics.spacing(2)
        principal = wx.BoxSizer(wx.VERTICAL)

        entete = wx.BoxSizer(wx.VERTICAL)
        entete.Add(self.ctrl_titre, 0, wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        entete.Add(self.ctrl_sous_titre, 0)
        principal.Add(entete, 0, wx.EXPAND | wx.ALL, marge)
        principal.Add(self.notebook, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, marge)

        self.SetSizer(principal)
        self.Layout()

    def OnPageChanged(self, event):
        self.MAJ()
        event.Skip()

    def MAJ(self):
        page = self.GetPageActive()
        if page == 0:
            self.ctrl_remplissage.MAJ()
        elif page == 1:
            self.ctrl_nbre_inscrits.MAJ()
        elif page == 2:
            self.ctrl_evenements.MAJ()
        elif page == 3:
            self.ctrl_locations.MAJ()

    def SetPageActive(self, index=0):
        try:
            self.notebook.SetSelection(index)
        except Exception:
            pass

    def GetPageActive(self):
        return self.notebook.GetSelection()

    def SavePerspective(self):
        try:
            return self.notebook.SavePerspective()
        except Exception:
            return ""

    def LoadPerspective(self, perspective):
        try:
            return self.notebook.LoadPerspective(perspective)
        except Exception:
            return False

    def SetDictDonnees(self, dictDonnees=None):
        if dictDonnees is None:
            dictDonnees = {}
        self.ctrl_remplissage.SetDictDonnees(dictDonnees)

    def OuvrirListeAttente(self):
        self.ctrl_remplissage.OuvrirListeAttente()

    def OuvrirListeRefus(self):
        self.ctrl_remplissage.OuvrirListeRefus()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = CTRL(panel)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.EXPAND)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(900, 560))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
