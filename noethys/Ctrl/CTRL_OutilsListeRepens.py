#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Recherche et filtres pour les ObjectListView modernisées.

Remplace progressivement ``CTRL_ObjectListView.CTRL_Outils`` dans les écrans
Repens sans modifier le composant historique utilisé ailleurs.
"""

import wx

from Ctrl import CTRL_ActionRepens
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _


class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent, listview, texteDefaut=u"Rechercher…"):
        wx.SearchCtrl.__init__(self, parent, style=wx.TE_PROCESS_ENTER)
        self.listview = listview
        self.SetDescriptiveText(texteDefaut)
        self.ShowSearchButton(True)
        self.ShowCancelButton(False)
        self.SetMinSize((-1, UTILS_UIMetrics.action_target("compact")))
        try:
            self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_low"))
            self.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        except Exception:
            pass

        try:
            self.listview.SetBarreRecherche(self)
        except Exception:
            pass

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.Recherche, self.timer)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
        self.Bind(wx.EVT_TEXT, self.OnTexte)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def OnSearch(self, event=None):
        self.Recherche()

    def OnCancel(self, event=None):
        self.SetValue("")
        self.Recherche()

    def Cancel(self):
        self.OnCancel()

    def OnKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.OnCancel()
            return
        event.Skip()

    def OnTexte(self, event):
        if self.timer.IsRunning():
            self.timer.Stop()
        try:
            nbre = len(self.listview.GetObjects())
        except Exception:
            nbre = 0
        if nbre < 500:
            duree = 30
        elif nbre < 1000:
            duree = 180
        elif nbre < 5000:
            duree = 400
        else:
            duree = 800
        self.timer.Start(duree, oneShot=True)
        event.Skip()

    def Recherche(self, event=None):
        if self.timer.IsRunning():
            self.timer.Stop()
        texte = self.GetValue()
        self.ShowCancelButton(bool(texte))
        try:
            self.listview.Filtrer(texte)
        except TypeError:
            self.listview.Filtrer()


class CTRL(wx.Panel):
    def __init__(self, parent, listview, texteDefaut=u"Rechercher…"):
        wx.Panel.__init__(self, parent, style=wx.BORDER_NONE | wx.TAB_TRAVERSAL)
        self.listview = listview
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        self.barreRecherche = BarreRecherche(self, listview=listview, texteDefaut=texteDefaut)
        self.bouton_filtrer = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Filtrer"),
            icone="settings",
            variante="ghost",
            tooltip=_(u"Gérer les filtres avancés de cette liste"),
        )
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFiltrer, self.bouton_filtrer)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.barreRecherche, 1, wx.EXPAND | wx.RIGHT, UTILS_UIMetrics.spacing(1))
        sizer.Add(self.bouton_filtrer, 0, wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(sizer)
        self.Layout()
        self.MAJFiltre()

    def MAJFiltre(self):
        try:
            nbre = len(self.listview.listeFiltresColonnes)
        except Exception:
            nbre = 0
        label = _(u"Filtrer") if nbre == 0 else _(u"Filtrer (%d)") % nbre
        self.bouton_filtrer.SetLabel(label)
        if nbre:
            self.bouton_filtrer.SetToolTip(wx.ToolTip(_(u"%d filtre(s) avancé(s) actif(s)") % nbre))
        else:
            self.bouton_filtrer.SetToolTip(wx.ToolTip(_(u"Gérer les filtres avancés de cette liste")))

    def OnBoutonFiltrer(self, event=None):
        from Dlg import DLG_Filtres_listes
        dlg = DLG_Filtres_listes.Dialog(self, ctrl_listview=self.listview)
        if dlg.ShowModal() == wx.ID_OK:
            listeFiltres = dlg.GetDonnees()
            self.listview.SetFiltresColonnes(listeFiltres)
            self.listview.Filtrer()
            self.MAJFiltre()
        dlg.Destroy()

    def SetFiltres(self, listeFiltres=None):
        self.listview.SetFiltresColonnes(listeFiltres or [])
        self.listview.Filtrer()
        self.MAJFiltre()
