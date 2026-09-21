#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Dialogue de génération d'une convention depuis la fiche Famille.

Réutilise les composants existants (CTRL_Choix_modele.CTRL_Choice pour
le choix du modèle, CTRL_Grille_periode.MyDatePickerCtrl pour les
dates) : aucun nouveau composant visuel n'est créé. Aucune saison ni
type de structure n'est rendu obligatoire ici : c'est une saisie
ponctuelle facultative qui préremplit {CONVENTION_SAISON}, laissée
vide si l'utilisateur ne la renseigne pas.
"""

from __future__ import annotations

import datetime

import wx

from Utils.UTILS_Traduction import _
from Ctrl.CTRL_Choix_modele import CTRL_Choice
from Ctrl.CTRL_Grille_periode import MyDatePickerCtrl


class Dialog(wx.Dialog):
    def __init__(self, parent, date_debut=None, date_fin=None, saison=""):
        wx.Dialog.__init__(self, parent, -1, _(u"Générer une convention"),
                            style=wx.DEFAULT_DIALOG_STYLE)

        label_modele = wx.StaticText(self, -1, _(u"Modèle de convention :"))
        self.ctrl_modele = CTRL_Choice(self, categorie="convention")

        label_periode = wx.StaticText(self, -1, _(u"Période concernée :"))
        self.ctrl_date_debut = MyDatePickerCtrl(self)
        self.ctrl_date_fin = MyDatePickerCtrl(self)
        aujourdhui = datetime.date.today()
        self.ctrl_date_debut.SetDate(date_debut or aujourdhui)
        self.ctrl_date_fin.SetDate(date_fin or aujourdhui)

        label_saison = wx.StaticText(self, -1, _(u"Saison (facultatif, ex. 2026-2027) :"))
        self.ctrl_saison = wx.TextCtrl(self, -1, saison)

        bouton_ok = wx.Button(self, wx.ID_OK, _(u"Générer"))
        bouton_ok.SetDefault()
        bouton_annuler = wx.Button(self, wx.ID_CANCEL, _(u"Annuler"))

        sizer_periode = wx.BoxSizer(wx.HORIZONTAL)
        sizer_periode.Add(self.ctrl_date_debut, 0, wx.RIGHT, 5)
        sizer_periode.Add(wx.StaticText(self, -1, _(u"au")), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
        sizer_periode.Add(self.ctrl_date_fin, 0)

        sizer_boutons = wx.StdDialogButtonSizer()
        sizer_boutons.AddButton(bouton_ok)
        sizer_boutons.AddButton(bouton_annuler)
        sizer_boutons.Realize()

        sizer_general = wx.BoxSizer(wx.VERTICAL)
        for label, ctrl in (
            (label_modele, self.ctrl_modele),
            (label_periode, sizer_periode),
            (label_saison, self.ctrl_saison),
        ):
            sizer_general.Add(label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
            if isinstance(ctrl, wx.Sizer):
                sizer_general.Add(ctrl, 0, wx.ALL, 10)
            else:
                sizer_general.Add(ctrl, 0, wx.ALL | wx.EXPAND, 10)
        sizer_general.Add(sizer_boutons, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        self.SetSizer(sizer_general)
        sizer_general.Fit(self)
        self.CentreOnParent()

    def GetIDmodele(self):
        return self.ctrl_modele.GetID()

    def GetDateDebut(self):
        return self.ctrl_date_debut.GetDate()

    def GetDateFin(self):
        return self.ctrl_date_fin.GetDate()

    def GetSaison(self):
        return self.ctrl_saison.GetValue().strip() or None
