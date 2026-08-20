#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

from Utils import UTILS_Adaptations
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _
import wx
from Ol import OL_Messages


ID_AJOUTER = wx.Window.NewControlId()
ID_MODIFIER = wx.Window.NewControlId()
ID_SUPPRIMER = wx.Window.NewControlId()


class Panel(wx.Panel):
    """Messages de l'accueil : dense, lisible et sans quadrillage agressif."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_low"))

        self.ctrl_titre = wx.StaticText(self, label=_(u"Messages & alertes"))
        self.ctrl_sous_titre = wx.StaticText(
            self,
            label=_(u"Rappels et informations à traiter"),
        )
        self.ctrl_compteur = wx.StaticText(self, label="")

        police = self.ctrl_titre.GetFont()
        police.SetWeight(wx.FONTWEIGHT_BOLD)
        police.SetPointSize(max(police.GetPointSize() + 2, 11))
        self.ctrl_titre.SetFont(police)
        self.ctrl_titre.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        self.ctrl_sous_titre.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface_variant"))
        self.ctrl_compteur.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface_variant"))

        self.barre_actions = UTILS_Adaptations.ToolBar(
            self,
            style=wx.TB_FLAT | wx.TB_TEXT | wx.TB_NODIVIDER,
        )
        self.barre_actions.SetToolBitmapSize(wx.Size(24, 24))
        self.barre_actions.AddFluentTool(
            ID_AJOUTER,
            _(u"Ajouter"),
            "add",
            _(u"Saisir un message"),
            role="primary",
        )
        self.barre_actions.AddFluentTool(
            ID_MODIFIER,
            _(u"Modifier"),
            "edit",
            _(u"Modifier le message sélectionné"),
        )
        self.barre_actions.AddFluentTool(
            ID_SUPPRIMER,
            _(u"Supprimer"),
            "delete",
            _(u"Supprimer le message sélectionné"),
            role="danger",
        )
        self.barre_actions.Realize()

        # Les règles horizontales natives deviennent presque blanches sous
        # Windows en thème sombre. La hiérarchie se fait par les surfaces et la
        # sélection, pas par un quadrillage de tableur.
        self.ctrl_messages = OL_Messages.ListView(
            self,
            -1,
            style=wx.LC_NO_HEADER | wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.NO_BORDER,
        )
        self.ctrl_messages.SetBackgroundColour(
            UTILS_Interface.GetCouleurRole("surface_container_lowest")
        )
        self.ctrl_messages.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))

        self.__do_layout()

        self.Bind(wx.EVT_TOOL, self.OnAjouterMessage, id=ID_AJOUTER)
        self.Bind(wx.EVT_TOOL, self.OnModifierMessage, id=ID_MODIFIER)
        self.Bind(wx.EVT_TOOL, self.OnSupprimerMessage, id=ID_SUPPRIMER)

    def __do_layout(self):
        marge = UTILS_UIMetrics.spacing(2)
        sizer = wx.BoxSizer(wx.VERTICAL)

        entete = wx.BoxSizer(wx.HORIZONTAL)
        textes = wx.BoxSizer(wx.VERTICAL)
        textes.Add(self.ctrl_titre, 0, wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        textes.Add(self.ctrl_sous_titre, 0)
        entete.Add(textes, 1, wx.ALIGN_CENTER_VERTICAL)
        entete.Add(self.ctrl_compteur, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, marge)
        sizer.Add(entete, 0, wx.EXPAND | wx.ALL, marge)

        sizer.Add(self.barre_actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, marge)
        sizer.Add(
            self.ctrl_messages,
            1,
            wx.EXPAND | wx.ALL,
            marge,
        )
        self.SetSizer(sizer)
        self.Layout()

    def MAJ(self):
        self.ctrl_messages.MAJ()
        try:
            nbre = len(self.ctrl_messages.donnees)
            self.ctrl_compteur.SetLabel(_(u"%d en cours") % nbre if nbre else _(u"Aucun"))
        except Exception:
            self.ctrl_compteur.SetLabel("")
        self.Layout()

    def OnAjouterMessage(self, event):
        self.ctrl_messages.Ajouter(None)

    def OnModifierMessage(self, event):
        self.ctrl_messages.Modifier(None)

    def OnSupprimerMessage(self, event):
        self.ctrl_messages.Supprimer(None)

    def GetMessages(self):
        return self.ctrl_messages.donnees


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = Panel(panel)
        self.ctrl.MAJ()
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.EXPAND)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
