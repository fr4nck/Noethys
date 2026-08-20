#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Licence :        GNU GPL
#------------------------------------------------------------------------
"""Structure UI du futur client mail intégré.

Ce fichier ne réalise volontairement aucune connexion IMAP à l'import. Le
module principal ne devra l'importer que si ``UTILS_Modules.EstActif('messagerie')``
est vrai.
"""

import wx

from Utils.UTILS_Traduction import _
from Utils import UTILS_Interface


class Panel(wx.Panel):
    """Client mail desktop dense : dossiers, liste, aperçu."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name="messagerie", style=wx.TAB_TRAVERSAL)

        self.splitter_principal = wx.SplitterWindow(
            self,
            style=wx.SP_LIVE_UPDATE | wx.SP_3D,
        )
        self.splitter_contenu = wx.SplitterWindow(
            self.splitter_principal,
            style=wx.SP_LIVE_UPDATE | wx.SP_3D,
        )

        self.panel_dossiers = wx.Panel(self.splitter_principal)
        self.panel_liste = wx.Panel(self.splitter_contenu)
        self.panel_apercu = wx.Panel(self.splitter_contenu)

        self.ctrl_dossiers = wx.ListBox(
            self.panel_dossiers,
            choices=[
                _(u"Réception"),
                _(u"À traiter"),
                _(u"Envoyés"),
                _(u"Brouillons"),
                _(u"Archives"),
                _(u"Corbeille"),
            ],
        )
        self.ctrl_dossiers.SetSelection(0)

        self.ctrl_messages = wx.ListCtrl(
            self.panel_liste,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES,
        )
        self.ctrl_messages.AppendColumn(_(u"Correspondant"), width=180)
        self.ctrl_messages.AppendColumn(_(u"Objet"), width=320)
        self.ctrl_messages.AppendColumn(_(u"Date"), width=120)

        self.ctrl_entete = wx.StaticText(
            self.panel_apercu,
            label=_(u"Sélectionnez un message pour afficher son contenu."),
        )
        self.ctrl_apercu = wx.TextCtrl(
            self.panel_apercu,
            value="",
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_NONE,
        )

        self._AppliqueApparence()
        self._ConstruitLayout()

    def _AppliqueApparence(self):
        fond = UTILS_Interface.GetCouleurRole("surface")
        fond_donnees = UTILS_Interface.GetCouleurRole("surface_container_lowest")
        texte = UTILS_Interface.GetCouleurRole("on_surface")

        self.SetBackgroundColour(fond)
        for panel in (self.panel_dossiers, self.panel_liste, self.panel_apercu):
            panel.SetBackgroundColour(fond)
        for ctrl in (self.ctrl_dossiers, self.ctrl_messages, self.ctrl_apercu):
            ctrl.SetBackgroundColour(fond_donnees)
            ctrl.SetForegroundColour(texte)
        self.ctrl_entete.SetForegroundColour(texte)
        self.ctrl_entete.SetBackgroundColour(fond)

    def _ConstruitLayout(self):
        sizer_dossiers = wx.BoxSizer(wx.VERTICAL)
        sizer_dossiers.Add(self.ctrl_dossiers, 1, wx.EXPAND | wx.ALL, 6)
        self.panel_dossiers.SetSizer(sizer_dossiers)

        sizer_liste = wx.BoxSizer(wx.VERTICAL)
        sizer_liste.Add(self.ctrl_messages, 1, wx.EXPAND)
        self.panel_liste.SetSizer(sizer_liste)

        sizer_apercu = wx.BoxSizer(wx.VERTICAL)
        sizer_apercu.Add(self.ctrl_entete, 0, wx.EXPAND | wx.ALL, 8)
        sizer_apercu.Add(self.ctrl_apercu, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        self.panel_apercu.SetSizer(sizer_apercu)

        self.splitter_contenu.SetMinimumPaneSize(180)
        self.splitter_contenu.SplitVertically(self.panel_liste, self.panel_apercu)
        self.splitter_contenu.SetSashGravity(0.52)

        self.splitter_principal.SetMinimumPaneSize(130)
        self.splitter_principal.SplitVertically(self.panel_dossiers, self.splitter_contenu)
        self.splitter_principal.SetSashGravity(0.18)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.splitter_principal, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()

        # Proportions initiales, ajustées à la vraie largeur au premier layout.
        wx.CallAfter(self._PositionneSplitters)

    def _PositionneSplitters(self):
        largeur = max(1, self.GetClientSize().GetWidth())
        self.splitter_principal.SetSashPosition(max(150, int(largeur * 0.17)))
        largeur_contenu = max(1, self.splitter_contenu.GetClientSize().GetWidth())
        self.splitter_contenu.SetSashPosition(max(300, int(largeur_contenu * 0.50)))

    def Initialisation(self):
        """Point d'entrée futur pour démarrer la synchronisation IMAP lazy."""
        return True

    def Arret(self):
        """Point d'arrêt futur du worker/timer de relève."""
        return True


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        self.ctrl = Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetSize((1200, 720))
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame = MyFrame(None, -1, _(u"Messagerie Noethys"))
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
