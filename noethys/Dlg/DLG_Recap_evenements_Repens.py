#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Présentation Repens du récapitulatif des événements."""

import wx

from Dlg import DLG_Recap_evenements as legacy
from Ctrl import CTRL_ActionRepens
from Utils import UTILS_HyperTreeRepens
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _


class CTRL(legacy.CTRL):
    def __init__(self, parent):
        legacy.CTRL.__init__(self, parent)
        UTILS_HyperTreeRepens.Configurer(self, (72, 82, 82, 84))

    def GetCouleurLigne(self, nbre_places_libres=None):
        if nbre_places_libres is None:
            return UTILS_HyperTreeRepens.CouleurEtat("neutral")
        if nbre_places_libres <= 0:
            return UTILS_HyperTreeRepens.CouleurEtat("danger")
        return UTILS_HyperTreeRepens.CouleurEtat("success")

    def SetItemBackgroundColour(self, item, colour):
        try:
            rgb = (colour.Red(), colour.Green(), colour.Blue())
            if rgb == (221, 221, 221):
                colour = UTILS_HyperTreeRepens.CouleurEtat("group")
            elif rgb == legacy.COULEUR_DISPONIBLE:
                colour = UTILS_HyperTreeRepens.CouleurEtat("success")
            elif rgb == legacy.COULEUR_ALERTE:
                colour = UTILS_HyperTreeRepens.CouleurEtat("warning")
            elif rgb == legacy.COULEUR_COMPLET:
                colour = UTILS_HyperTreeRepens.CouleurEtat("danger")
        except Exception:
            pass
        return legacy.CTRL.SetItemBackgroundColour(self, item, colour)


class BarreRecherche(wx.SearchCtrl):
    def __init__(self, parent, ctrl):
        wx.SearchCtrl.__init__(self, parent, style=wx.TE_PROCESS_ENTER)
        self.ctrl = ctrl
        self.SetDescriptiveText(_(u"Rechercher un événement…"))
        self.ShowSearchButton(True)
        self.ShowCancelButton(False)
        self.SetMinSize((-1, UTILS_UIMetrics.action_target("compact")))
        try:
            self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_low"))
            self.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        except Exception:
            pass
        self.Bind(wx.EVT_TEXT, self.OnRecherche)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnAnnuler)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def OnRecherche(self, event):
        filtre = self.GetValue()
        self.ShowCancelButton(bool(filtre))
        self.ctrl.SetFiltre(filtre)
        event.Skip()

    def OnAnnuler(self, event):
        self.SetValue("")
        self.ctrl.SetFiltre("")

    def OnKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.OnAnnuler(event)
            return
        event.Skip()


class Panel(legacy.Panel):
    def __init__(self, parent):
        # Construction directe : aucune vieille colonne de BitmapButton n'est créée.
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        self.ctrl_evenements = CTRL(self)
        self.ctrl_recherche = BarreRecherche(self, self.ctrl_evenements)
        self.bouton_parametres = CTRL_ActionRepens.CTRL(
            self, label=_(u"Paramètres"), icone="settings", tooltip=_(u"Modifier les paramètres d'affichage")
        )
        self.bouton_plus = CTRL_ActionRepens.CTRL(
            self, label=_(u"Plus"), icone="more", variante="ghost", tooltip=_(u"Impression, export et actualisation")
        )

        self.Bind(wx.EVT_BUTTON, self.OnBoutonParametres, self.bouton_parametres)
        self.Bind(wx.EVT_BUTTON, self.OnPlus, self.bouton_plus)

        marge = UTILS_UIMetrics.spacing(2)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(self.ctrl_recherche, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, marge)
        commandes = wx.WrapSizer(wx.HORIZONTAL)
        commandes.Add(self.bouton_parametres, 0, wx.RIGHT | wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        commandes.Add(self.bouton_plus, 0, wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        principal.Add(commandes, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, marge)
        principal.Add(self.ctrl_evenements, 1, wx.EXPAND | wx.ALL, marge)
        self.SetSizer(principal)
        self.Layout()

    def _GetDashboard(self):
        parent = self
        for _ in range(6):
            if parent is None:
                break
            if hasattr(parent, "ctrl_remplissage"):
                return parent
            try:
                parent = parent.GetParent()
            except Exception:
                break
        return None

    def MAJ(self):
        dashboard = self._GetDashboard()
        if dashboard is not None:
            self.SetDictDonnees(dashboard.ctrl_remplissage.dictDonnees)
        else:
            self.ctrl_evenements.MAJ()

    def OnBoutonParametres(self, event):
        dashboard = self._GetDashboard()
        if dashboard is None:
            return
        from Dlg import DLG_Parametres_remplissage
        dictDonnees = dashboard.ctrl_remplissage.dictDonnees
        dlg = DLG_Parametres_remplissage.Dialog(
            None,
            dictDonnees,
            afficheAbregeGroupes=False,
            afficheLargeurColonneUnite=False,
            afficheTotaux=False,
        )
        if dlg.ShowModal() == wx.ID_OK:
            newDictDonnees = dlg.GetDictDonnees()
            for key, valeur in newDictDonnees.items():
                dictDonnees[key] = valeur
            dashboard.ctrl_remplissage.SetDictDonnees(dictDonnees)
            self.MAJ()
        dlg.Destroy()

    def SetDictDonnees(self, dictDonnees=None):
        if not dictDonnees:
            return
        self.ctrl_evenements.listeActivites = dictDonnees.get("listeActivites", [])
        self.ctrl_evenements.listePeriodes = dictDonnees.get("listePeriodes", [])
        self.ctrl_evenements.MAJ()

    def OnPlus(self, event):
        menu = wx.Menu()
        id_imprimer = wx.Window.NewControlId()
        id_export = wx.Window.NewControlId()
        id_actualiser = wx.Window.NewControlId()
        id_aide = wx.Window.NewControlId()
        menu.Append(id_imprimer, _(u"Imprimer…"))
        menu.Append(id_export, _(u"Exporter vers Excel…"))
        menu.AppendSeparator()
        menu.Append(id_actualiser, _(u"Actualiser"))
        menu.AppendSeparator()
        menu.Append(id_aide, _(u"Aide"))
        self.Bind(wx.EVT_MENU, lambda evt: self.ctrl_evenements.Imprimer(), id=id_imprimer)
        self.Bind(wx.EVT_MENU, lambda evt: self.ctrl_evenements.ExportExcel(), id=id_export)
        self.Bind(wx.EVT_MENU, self.Actualiser, id=id_actualiser)
        self.Bind(wx.EVT_MENU, self.Aide, id=id_aide)
        self.PopupMenu(menu)
        menu.Destroy()
