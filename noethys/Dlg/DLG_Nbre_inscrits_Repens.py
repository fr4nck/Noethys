#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Présentation Repens du tableau des inscriptions.

Le moteur de données, les exports et les dialogues métier restent dans
``DLG_Nbre_inscrits_2``. Ce module remplace uniquement la structure visuelle :
aucun FlexGridSizer, aucune colonne latérale de BitmapButton 16 px et aucune
couleur historique codée en dur dans le panneau affiché par le cockpit.
"""

import wx

from Dlg import DLG_Nbre_inscrits_2 as legacy
from Ctrl import CTRL_ActionRepens
from Utils import UTILS_HyperTreeRepens
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _


class CTRL(legacy.CTRL):
    """HyperTreeList métier historique avec rendu sémantique Repens."""

    def __init__(self, parent):
        legacy.CTRL.__init__(self, parent)
        UTILS_HyperTreeRepens.Configurer(self, (78, 72, 84, 84, 84, 84))

    def GetCouleurLigne(self, nbre_places_libres=None):
        if nbre_places_libres is None:
            return UTILS_HyperTreeRepens.CouleurEtat("neutral")
        if nbre_places_libres <= 0:
            return UTILS_HyperTreeRepens.CouleurEtat("danger")
        if nbre_places_libres <= self.seuil_alerte:
            return UTILS_HyperTreeRepens.CouleurEtat("warning")
        return UTILS_HyperTreeRepens.CouleurEtat("success")

    def SetItemBackgroundColour(self, item, colour):
        """Traduit localement les fonds de regroupement hérités.

        Il ne s'agit pas d'un monkey-patch wx : seul ce contrôle convertit les
        couleurs historiques qu'émet encore son moteur métier.
        """
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
        self.SetDescriptiveText(_(u"Rechercher une activité ou un groupe…"))
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
    """Panneau compact : recherche, commandes puis données."""

    def __init__(self, parent):
        # Ne pas appeler legacy.Panel.__init__ : il construirait la vieille UI.
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        self.ctrl_inscriptions = CTRL(self)
        self.ctrl_recherche = BarreRecherche(self, self.ctrl_inscriptions)

        self.bouton_attente = CTRL_ActionRepens.CTRL(
            self, label=_(u"Attente"), icone="people", tooltip=_(u"Afficher les inscriptions en attente")
        )
        self.bouton_refus = CTRL_ActionRepens.CTRL(
            self, label=_(u"Refus"), tooltip=_(u"Afficher les inscriptions refusées")
        )
        self.bouton_tarifs = CTRL_ActionRepens.CTRL(
            self, label=_(u"Tarifs"), tooltip=_(u"Consulter les tarifs de l'activité sélectionnée")
        )
        self.bouton_plus = CTRL_ActionRepens.CTRL(
            self, label=_(u"Plus"), icone="more", variante="ghost", tooltip=_(u"Impression, export et paramètres")
        )

        self.Bind(wx.EVT_BUTTON, self.OnBoutonAttente, self.bouton_attente)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonRefus, self.bouton_refus)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonTarifs, self.bouton_tarifs)
        self.Bind(wx.EVT_BUTTON, self.OnPlus, self.bouton_plus)

        marge = UTILS_UIMetrics.spacing(2)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(self.ctrl_recherche, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, marge)

        commandes = wx.WrapSizer(wx.HORIZONTAL)
        commandes.Add(self.bouton_attente, 0, wx.RIGHT | wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        commandes.Add(self.bouton_refus, 0, wx.RIGHT | wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        commandes.Add(self.bouton_tarifs, 0, wx.RIGHT | wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        commandes.Add(self.bouton_plus, 0, wx.BOTTOM, UTILS_UIMetrics.spacing(1))
        principal.Add(commandes, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, marge)
        principal.Add(self.ctrl_inscriptions, 1, wx.EXPAND | wx.ALL, marge)
        self.SetSizer(principal)
        self.Layout()

    def OnPlus(self, event):
        menu = wx.Menu()
        ids = {
            "imprimer": wx.Window.NewControlId(),
            "export": wx.Window.NewControlId(),
            "parametres": wx.Window.NewControlId(),
            "actualiser": wx.Window.NewControlId(),
            "aide": wx.Window.NewControlId(),
        }
        menu.Append(ids["imprimer"], _(u"Imprimer…"))
        menu.Append(ids["export"], _(u"Exporter vers Excel…"))
        menu.AppendSeparator()
        menu.Append(ids["parametres"], _(u"Paramètres d'affichage…"))
        menu.Append(ids["actualiser"], _(u"Actualiser"))
        menu.AppendSeparator()
        menu.Append(ids["aide"], _(u"Aide"))
        self.Bind(wx.EVT_MENU, lambda evt: self.ctrl_inscriptions.Imprimer(), id=ids["imprimer"])
        self.Bind(wx.EVT_MENU, lambda evt: self.ctrl_inscriptions.ExportExcel(), id=ids["export"])
        self.Bind(wx.EVT_MENU, self.OnBoutonParametres, id=ids["parametres"])
        self.Bind(wx.EVT_MENU, self.Actualiser, id=ids["actualiser"])
        self.Bind(wx.EVT_MENU, self.Aide, id=ids["aide"])
        self.PopupMenu(menu)
        menu.Destroy()
