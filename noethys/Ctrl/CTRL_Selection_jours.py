#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-18 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import datetime

import wx
import wx.lib.agw.hyperlink as Hyperlink
from dateutil import rrule

import GestionDB
from Ctrl import CTRL_Bouton_image
from Utils import UTILS_Dates, UTILS_Interface, UTILS_UIMetrics
from Utils.UTILS_Traduction import _


def ConvertNumEnDateutil(jours=None):
    listeReference = [rrule.MO, rrule.TU, rrule.WE, rrule.TH, rrule.FR, rrule.SA, rrule.SU]
    if jours is None:
        return []
    if isinstance(jours, list):
        numeros = jours
    else:
        numeros = [int(jour) for jour in str(jours).split(";") if jour != ""]
    return [listeReference[numJour] for numJour in numeros]


def IsVacances(listeVacances=None, date=None):
    if listeVacances is None:
        listeVacances = []
    return any(date_debut <= date <= date_fin for date_debut, date_fin in listeVacances)


def GetDates(jours=None, date_min=None, date_max=None):
    if jours is None:
        jours = {"scolaires": [], "vacances": []}

    DB = GestionDB.DB()
    req = """SELECT date_debut, date_fin
    FROM vacances
    WHERE date_debut<='%s' AND date_fin>='%s'
    ORDER BY date_debut;""" % (date_max, date_min)
    DB.ExecuterReq(req)
    listeDonnees = DB.ResultatReq()
    DB.Close()
    listeVacances = [(UTILS_Dates.DateEngEnDateDD(debut), UTILS_Dates.DateEngEnDateDD(fin)) for debut, fin in listeDonnees]

    listeDates = []
    for periode in ("scolaires", "vacances"):
        liste_jours = ConvertNumEnDateutil(jours.get(periode, []))
        if not liste_jours:
            continue
        dates = rrule.rrule(rrule.WEEKLY, wkst=rrule.MO, byweekday=liste_jours, dtstart=date_min, until=date_max)
        for date in dates:
            date = date.date()
            vacances = IsVacances(listeVacances, date)
            if (periode == "scolaires" and not vacances) or (periode == "vacances" and vacances):
                listeDates.append(date)
    listeDates.sort()
    return listeDates


def _PoliceInterface():
    police = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
    facteur = UTILS_Interface.GetTailleTexte() / 100.0
    police.SetPointSize(max(8, int(round(police.GetPointSize() * facteur))))
    return police


class Hyperlien(Hyperlink.HyperLinkCtrl):
    """Compatibilité pour les écrans tiers qui utilisaient encore ce helper."""

    def __init__(self, parent, id=-1, label="", infobulle="", URL=""):
        Hyperlink.HyperLinkCtrl.__init__(self, parent, id, label, URL=URL)
        self.parent = parent
        self.URL = URL
        self.AutoBrowse(False)
        try:
            couleur = UTILS_Interface.GetCouleurRole("primary")
            self.SetColours(couleur, couleur, couleur)
            self.SetFont(_PoliceInterface())
        except Exception:
            pass
        self.SetUnderlines(False, False, True)
        self.SetBold(False)
        self.EnableRollover(True)
        self.SetToolTip(wx.ToolTip(infobulle))
        self.UpdateLink()
        self.DoPopup(False)
        self.Bind(Hyperlink.EVT_HYPERLINK_LEFT, self.OnLeftLink)

    def OnLeftLink(self, event):
        if self.URL == "tout":
            self.parent.CocherTout()
        elif self.URL == "rien":
            self.parent.CocherRien()
        self.UpdateLink()


class CTRL_Jours(wx.Panel):
    JOURS = (
        ("lundi", _(u"Lun")),
        ("mardi", _(u"Mar")),
        ("mercredi", _(u"Mer")),
        ("jeudi", _(u"Jeu")),
        ("vendredi", _(u"Ven")),
        ("samedi", _(u"Sam")),
        ("dimanche", _(u"Dim")),
    )

    def __init__(self, parent, periode="scolaire"):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.periode = periode
        self.liste_jours = tuple(jour for jour, label in self.JOURS)

        try:
            self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))
        except Exception:
            pass

        jours_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for jour, abrege in self.JOURS:
            controle = wx.CheckBox(self, -1, abrege)
            controle.SetToolTip(wx.ToolTip(jour.capitalize()))
            try:
                controle.SetFont(_PoliceInterface())
                controle.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
            except Exception:
                pass
            setattr(self, "check_%s" % jour, controle)
            jours_sizer.Add(controle, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, UTILS_UIMetrics.spacing(1))

        self.bouton_tout = CTRL_Bouton_image.CTRL(self, texte=_(u"Tout"))
        self.bouton_rien = CTRL_Bouton_image.CTRL(self, texte=_(u"Aucun"))
        self.bouton_tout.SetToolTip(wx.ToolTip(_(u"Tout cocher")))
        self.bouton_rien.SetToolTip(wx.ToolTip(_(u"Tout décocher")))
        self.Bind(wx.EVT_BUTTON, self.OnTout, self.bouton_tout)
        self.Bind(wx.EVT_BUTTON, self.OnRien, self.bouton_rien)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_tout, 0, wx.RIGHT, UTILS_UIMetrics.spacing(1))
        actions.Add(self.bouton_rien, 0)

        principal = wx.BoxSizer(wx.HORIZONTAL)
        principal.Add(jours_sizer, 0, wx.ALIGN_CENTER_VERTICAL)
        principal.Add(actions, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, UTILS_UIMetrics.spacing(2))
        self.SetSizer(principal)
        self.Fit()

    def OnTout(self, event):
        self.CocherTout()

    def OnRien(self, event):
        self.CocherRien()

    def GetJours(self):
        return [index for index, jour in enumerate(self.liste_jours) if getattr(self, "check_%s" % jour).GetValue()]

    def SetJours(self, jours=""):
        if jours is None:
            return
        if isinstance(jours, list):
            listeJours = jours
        else:
            listeJours = [int(jour) for jour in str(jours).split(";") if jour != ""]
        for index, jour in enumerate(self.liste_jours):
            getattr(self, "check_%s" % jour).SetValue(index in listeJours)

    def CocherTout(self):
        self.SetJours([0, 1, 2, 3, 4, 5, 6])

    def CocherRien(self):
        self.SetJours([])


class CTRL(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.label_scolaires = wx.StaticText(self, -1, _(u"Jours scolaires :"))
        self.ctrl_scolaires = CTRL_Jours(self, "scolaire")
        self.label_vacances = wx.StaticText(self, -1, _(u"Jours de vacances :"))
        self.ctrl_vacances = CTRL_Jours(self, "vacances")

        try:
            self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))
            for label in (self.label_scolaires, self.label_vacances):
                label.SetFont(_PoliceInterface())
                label.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        except Exception:
            pass

        ligne_scolaire = wx.BoxSizer(wx.HORIZONTAL)
        ligne_scolaire.Add(self.label_scolaires, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, UTILS_UIMetrics.spacing(2))
        ligne_scolaire.Add(self.ctrl_scolaires, 1, wx.EXPAND)
        ligne_vacances = wx.BoxSizer(wx.HORIZONTAL)
        ligne_vacances.Add(self.label_vacances, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, UTILS_UIMetrics.spacing(2))
        ligne_vacances.Add(self.ctrl_vacances, 1, wx.EXPAND)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(ligne_scolaire, 0, wx.EXPAND | wx.BOTTOM, UTILS_UIMetrics.spacing(2))
        principal.Add(ligne_vacances, 0, wx.EXPAND)
        self.SetSizer(principal)
        self.Fit()

    def GetDonnees(self):
        return {
            "vacances": self.ctrl_vacances.GetJours(),
            "scolaires": self.ctrl_scolaires.GetJours(),
        }

    def SetDonnees(self, donnees=None):
        if not donnees:
            return
        if "vacances" in donnees:
            self.ctrl_vacances.SetJours(donnees["vacances"])
        if "scolaires" in donnees:
            self.ctrl_scolaires.SetJours(donnees["scolaires"])


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        self.ctrl = CTRL(panel)
        bouton_test = wx.Button(panel, -1, u"Test")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 0, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(2))
        sizer.Add(bouton_test, 0, wx.ALL, UTILS_UIMetrics.spacing(2))
        panel.SetSizer(sizer)
        cadre = wx.BoxSizer(wx.VERTICAL)
        cadre.Add(panel, 1, wx.EXPAND)
        self.SetSizer(cadre)
        self.Layout()
        self.CentreOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnBouton, bouton_test)

    def OnBouton(self, event):
        self.ctrl.SetDonnees({"vacances": [0, 1], "scolaires": "5;6"})
        donnees = self.ctrl.GetDonnees()
        print(donnees)
        print(ConvertNumEnDateutil(donnees["vacances"]))
        print(GetDates(jours=donnees, date_min=datetime.date(2018, 1, 1), date_max=datetime.date(2018, 12, 31)))


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(700, 240))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
