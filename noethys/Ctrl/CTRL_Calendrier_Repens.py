#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Calendrier Repens.

Le moteur de sélection/dessin historique reste la source métier. La navigation
qui l'entoure est reconstruite directement : plus de BitmapButton 16 px, de
SpinButton 17x20 ni de FlexGridSizer.
"""

import datetime
import sys

import wx

from Ctrl import CTRL_ActionRepens
from Ctrl import CTRL_Calendrier as legacy
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _


SelectDatesEvent = legacy.SelectDatesEvent
EVT_SELECT_DATES = legacy.EVT_SELECT_DATES


def _rgb(role):
    couleur = UTILS_Interface.GetCouleurRole(role)
    try:
        return (couleur.Red(), couleur.Green(), couleur.Blue())
    except Exception:
        return (255, 255, 255)


class Calendrier(legacy.Calendrier):
    """Moteur historique avec palette sémantique locale."""

    def __init__(self, parent, ID=-1, multiSelections=True, selectionInterdite=False, typeCalendrier="mensuel"):
        legacy.Calendrier.__init__(
            self,
            parent,
            ID,
            multiSelections=multiSelections,
            selectionInterdite=selectionInterdite,
            typeCalendrier=typeCalendrier,
        )
        self.ecartCases = max(UTILS_UIMetrics.px(2), 2)
        self.ecartMois = max(UTILS_UIMetrics.px(8), 8)
        self.AppliquerPalette()
        self.MAJAffichage()

    def AppliquerPalette(self):
        self.couleurFond = _rgb("surface_container_lowest")
        self.couleurNormal = _rgb("surface_container_lowest")
        self.couleurWE = _rgb("surface_container_low")
        self.couleurSelect = _rgb("selection")
        self.couleurSurvol = _rgb("focus")
        self.couleurFontJours = _rgb("on_surface")
        self.couleurVacances = _rgb("surface_container")
        self.couleurFontJoursAvecPresents = _rgb("primary")
        self.couleurFerie = _rgb("surface_container_highest")
        try:
            self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
            self.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        except Exception:
            pass


class CTRL(wx.Panel):
    def __init__(
        self,
        parent,
        ID=-1,
        afficheBoutonAnnuel=True,
        afficheAujourdhui=True,
        multiSelections=True,
        selectionInterdite=False,
        typeCalendrier="mensuel",
        bordHaut=0,
        bordBas=0,
        bordLateral=0,
    ):
        wx.Panel.__init__(self, parent, ID, name="panel_calendrier_repens", style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        self.afficheBoutonAnnuel = afficheBoutonAnnuel
        self.multiSelections = multiSelections
        self.selectionInterdite = selectionInterdite
        self.typeCalendrier = typeCalendrier
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        self.calendrier = Calendrier(
            self,
            -1,
            multiSelections=multiSelections,
            selectionInterdite=selectionInterdite,
            typeCalendrier=typeCalendrier,
        )

        self.listeMois = [
            _(u"Janvier"), _(u"Février"), _(u"Mars"), _(u"Avril"),
            _(u"Mai"), _(u"Juin"), _(u"Juillet"), _(u"Août"),
            _(u"Septembre"), _(u"Octobre"), _(u"Novembre"), _(u"Décembre"),
        ]
        if "linux" in sys.platform:
            self.listeMois = [
                _(u"Janv."), _(u"Fév."), _(u"Mars"), _(u"Avril"),
                _(u"Mai"), _(u"Juin"), _(u"Juil."), _(u"Août"),
                _(u"Sept."), _(u"Oct."), _(u"Nov."), _(u"Déc."),
            ]

        self.bouton_precedent = CTRL_ActionRepens.CTRL(
            self, label=u"‹", variante="ghost", tooltip=_(u"Période précédente")
        )
        self.combo_mois = wx.Choice(self, -1, choices=self.listeMois)
        self.combo_annee = wx.SpinCtrl(self, -1, "")
        self.combo_annee.SetRange(1970, 2099)
        self.bouton_suivant = CTRL_ActionRepens.CTRL(
            self, label=u"›", variante="ghost", tooltip=_(u"Période suivante")
        )
        self.bouton_mode = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Vue annuelle"),
            icone="calendar",
            variante="secondaire",
            tooltip=_(u"Basculer entre calendrier mensuel et annuel"),
        )

        hauteur = UTILS_UIMetrics.action_target("compact")
        self.combo_mois.SetMinSize((UTILS_UIMetrics.px(120), hauteur))
        self.combo_annee.SetMinSize((UTILS_UIMetrics.px(92), hauteur))
        for ctrl in (self.combo_mois, self.combo_annee):
            try:
                ctrl.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
                ctrl.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
            except Exception:
                pass

        date_jour = datetime.date.today()
        self.combo_mois.SetSelection(date_jour.month - 1)
        self.combo_annee.SetValue(date_jour.year)
        self.MAJPeriodeCalendrier()

        if afficheAujourdhui and not self.selectionInterdite:
            self.calendrier.SelectJours([date_jour])

        self.Bind(wx.EVT_BUTTON, self.OnPrecedent, self.bouton_precedent)
        self.Bind(wx.EVT_BUTTON, self.OnSuivant, self.bouton_suivant)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuel, self.bouton_mode)
        self.Bind(wx.EVT_CHOICE, self.OnComboMois, self.combo_mois)
        self.Bind(wx.EVT_SPINCTRL, self.OnComboAnnee, self.combo_annee)
        self.Bind(wx.EVT_TEXT, self.OnComboAnnee, self.combo_annee)

        navigation = wx.BoxSizer(wx.HORIZONTAL)
        navigation.Add(self.bouton_precedent, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, UTILS_UIMetrics.spacing(1))
        navigation.Add(self.combo_mois, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, UTILS_UIMetrics.spacing(1))
        navigation.Add(self.combo_annee, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, UTILS_UIMetrics.spacing(1))
        navigation.Add(self.bouton_suivant, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, UTILS_UIMetrics.spacing(2))
        navigation.Add(self.bouton_mode, 0, wx.ALIGN_CENTER_VERTICAL)

        marge_lateral = max(int(bordLateral or 0), UTILS_UIMetrics.spacing(1))
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(
            navigation,
            0,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
            max(marge_lateral, int(bordHaut or 0)),
        )
        principal.Add(
            self.calendrier,
            1,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM,
            max(marge_lateral, int(bordBas or 0), UTILS_UIMetrics.spacing(1)),
        )
        self.SetSizer(principal)
        self._ActualiseMode()
        self.Layout()

    def _ActualiseMode(self):
        annuel = self.calendrier.GetTypeCalendrier() == "annuel"
        self.combo_mois.Enable(not annuel)
        self.bouton_mode.SetLabel(_(u"Vue mensuelle") if annuel else _(u"Vue annuelle"))
        self.bouton_mode.SetToolTip(
            wx.ToolTip(_(u"Afficher le calendrier mensuel") if annuel else _(u"Afficher le calendrier annuel"))
        )
        if not self.afficheBoutonAnnuel:
            self.bouton_mode.Hide()
        else:
            self.bouton_mode.Show()
        self.Layout()

    def SetMultiSelection(self, etat=False):
        self.multiSelections = etat
        self.calendrier.multiSelections = etat
        selections = self.GetSelections()
        if len(selections) > 1:
            self.SelectJours([min(selections)])

    def GetSelections(self):
        selections = self.calendrier.GetSelections()
        if selections is None:
            return []
        selections = list(selections)
        selections.sort()
        return selections

    def SelectJours(self, listeDates=None):
        self.calendrier.SelectJours(listeDates or [])

    def MAJselectionDates(self, listeDates):
        self.SetSelectionDates(listeDates)
        self.GetGrandParent().GetParent().MAJpanelPlanning()
        self.GetGrandParent().GetParent().panelPersonnes.listCtrlPersonnes.CreateCouleurs()

    def _Decaler(self, delta):
        mois = self.combo_mois.GetSelection() + 1
        annee = int(self.combo_annee.GetValue())
        if self.calendrier.GetTypeCalendrier() == "annuel":
            annee += delta
        else:
            mois += delta
            if mois < 1:
                mois = 12
                annee -= 1
            elif mois > 12:
                mois = 1
                annee += 1
        self.combo_mois.SetSelection(mois - 1)
        self.combo_annee.SetValue(annee)
        self.MAJPeriodeCalendrier()

    def OnPrecedent(self, event):
        self._Decaler(-1)

    def OnSuivant(self, event):
        self._Decaler(1)

    def OnBoutonAnnuel(self, event):
        type_cible = "annuel" if self.calendrier.GetTypeCalendrier() == "mensuel" else "mensuel"
        self.calendrier.SetTypeCalendrier(type_cible)
        self._ActualiseMode()

    def MAJPeriodeCalendrier(self):
        mois = max(1, self.combo_mois.GetSelection() + 1)
        annee = int(self.combo_annee.GetValue())
        self.calendrier.SetMoisAnneeCalendrier(mois, annee)

    def OnComboMois(self, event):
        self.MAJPeriodeCalendrier()

    def OnComboAnnee(self, event):
        self.MAJPeriodeCalendrier()

    def MAJpanel(self):
        self.calendrier.MAJpanel()

    def MAJcontrolesNavigation(self, mois, annee):
        self.combo_mois.SetSelection(mois - 1)
        self.combo_annee.SetValue(annee)
