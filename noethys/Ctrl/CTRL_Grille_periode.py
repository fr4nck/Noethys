#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import calendar
import datetime

import wx

import GestionDB
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _

if 'phoenix' in wx.PlatformInfo:
    from wx.adv import DatePickerCtrl, DP_DROPDOWN, EVT_DATE_CHANGED
else:
    from wx import DatePickerCtrl, DP_DROPDOWN, EVT_DATE_CHANGED


def _AppliquerStyleControle(ctrl, fond_donnees=True):
    try:
        if fond_donnees:
            ctrl.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
        ctrl.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
    except Exception:
        pass
    try:
        police = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
        facteur = UTILS_Interface.GetTailleTexte() / 100.0
        police.SetPointSize(max(8, int(round(police.GetPointSize() * facteur))))
        ctrl.SetFont(police)
    except Exception:
        pass


def _PreparerPage(panel):
    try:
        panel.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))
    except Exception:
        pass


def _LigneFormulaire(label, ctrl):
    label.SetMinSize((UTILS_UIMetrics.px(68), -1))
    ligne = wx.BoxSizer(wx.HORIZONTAL)
    ligne.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, UTILS_UIMetrics.spacing(2))
    ligne.Add(ctrl, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
    return ligne


class MyDatePickerCtrl(DatePickerCtrl):
    def __init__(self, parent):
        DatePickerCtrl.__init__(self, parent, -1, style=DP_DROPDOWN)
        self.parent = parent
        _AppliquerStyleControle(self)
        self.SetMinSize((UTILS_UIMetrics.px(132), UTILS_UIMetrics.action_target("compact")))
        self.Bind(EVT_DATE_CHANGED, self.OnDateChanged)
        self.Bind(wx.EVT_CHILD_FOCUS, self.OnFocus)

    def OnFocus(self, event):
        event.Skip(False)

    def SetDate(self, dateDD=None):
        if dateDD is None:
            return
        date = wx.DateTime()
        date.Set(dateDD.day, dateDD.month - 1, dateDD.year)
        self.SetValue(date)

    def GetDate(self):
        date = self.GetValue()
        return datetime.date(date.GetYear(), date.GetMonth() + 1, date.GetDay())

    def OnDateChanged(self, event):
        self.GetParent().OnSelection()


class CTRL_Annee(wx.SpinCtrl):
    def __init__(self, parent):
        wx.SpinCtrl.__init__(self, parent, -1, min=1977, max=2999)
        self.parent = parent
        _AppliquerStyleControle(self)
        self.SetMinSize((UTILS_UIMetrics.px(92), UTILS_UIMetrics.action_target("compact")))
        self.SetToolTip(wx.ToolTip(_(u"Sélectionnez une année")))
        self.SetAnnee(datetime.date.today().year)

    def SetAnnee(self, annee=None):
        if annee is not None:
            self.SetValue(annee)

    def GetAnnee(self):
        return self.GetValue()

    def GetDatesSelections(self):
        annee = self.GetAnnee()
        return [(datetime.date(annee, 1, 1), datetime.date(annee, 12, 31))]


class CTRL_ListBox(wx.ListBox):
    def __init__(self, parent):
        wx.ListBox.__init__(self, parent, -1, style=wx.LB_EXTENDED)
        self.parent = parent
        self.SetToolTip(wx.ToolTip(_(u"Sélectionnez une ou plusieurs périodes avec les touches SHIFT ou CTRL")))
        self.listeChoix = []
        _AppliquerStyleControle(self)
        self.SetMinSize((UTILS_UIMetrics.px(150), UTILS_UIMetrics.px(116)))

    def SetListeChoix(self, listeChoix=[], conserveSelections=False):
        self.listeChoix = listeChoix
        listeSelections = self.GetSelections()
        self.Clear()
        self.Set([nomItem for nomItem, _date_debut, _date_fin in listeChoix])
        if conserveSelections:
            for indexSelection in listeSelections:
                if 0 <= indexSelection < self.GetCount():
                    self.Select(indexSelection)

    def GetDatesSelections(self):
        listeDatesSelections = []
        for indexSelection in self.GetSelections():
            date_debut = self.listeChoix[indexSelection][1]
            date_fin = self.listeChoix[indexSelection][2]
            listeDatesSelections.append((date_debut, date_fin))
        return listeDatesSelections

    def SetSelectionIndex(self, indexSelection=None):
        try:
            if indexSelection is None or indexSelection < 0 or indexSelection >= self.GetCount():
                return
            self.Select(indexSelection)
            self.EnsureVisible(indexSelection)
        except Exception:
            pass

    def SetVisibleSelection(self):
        try:
            indexSelection = self.GetSelections()[0]
            self.Select(indexSelection)
            self.EnsureVisible(indexSelection)
        except Exception:
            pass


class Mois(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        _PreparerPage(self)
        self.listeMois = [_(u"Janvier"), _(u"Février"), _(u"Mars"), _(u"Avril"), _(u"Mai"), _(u"Juin"), _(u"Juillet"), _(u"Août"), _(u"Septembre"), _(u"Octobre"), _(u"Novembre"), _(u"Décembre")]

        self.label_annee = wx.StaticText(self, -1, _(u"Année :"))
        self.ctrl_annee = CTRL_Annee(self)
        self.label_mois = wx.StaticText(self, -1, _(u"Mois :"))
        self.ctrl_mois = CTRL_ListBox(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        marge = UTILS_UIMetrics.spacing(2)
        sizer.Add(_LigneFormulaire(self.label_annee, self.ctrl_annee), 0, wx.EXPAND | wx.ALL, marge)
        sizer.Add(self.label_mois, 0, wx.LEFT | wx.RIGHT | wx.TOP, marge)
        sizer.Add(self.ctrl_mois, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, marge)
        self.SetSizer(sizer)

        self.ctrl_annee.Bind(wx.EVT_SPINCTRL, self.OnSelectionAnnee)
        self.ctrl_mois.Bind(wx.EVT_LISTBOX, self.OnSelectionMois)
        self.MAJ()
        self.ctrl_mois.SetSelectionIndex(datetime.date.today().month - 1)

    def OnSelectionAnnee(self, event):
        self.MAJ()
        self.GetGrandParent().OnSelection()

    def OnSelectionMois(self, event):
        self.GetGrandParent().OnSelection()

    def GetDatesSelections(self):
        return self.ctrl_mois.GetDatesSelections()

    def MAJ(self):
        annee = self.ctrl_annee.GetAnnee()
        listeChoix = []
        for index, nomMois in enumerate(self.listeMois):
            mois = index + 1
            nbreJoursMois = calendar.monthrange(annee, mois)[1]
            listeChoix.append((
                nomMois,
                datetime.date(annee, mois, 1),
                datetime.date(annee, mois, nbreJoursMois),
            ))
        self.ctrl_mois.SetListeChoix(listeChoix, conserveSelections=True)

    def SetVisibleSelection(self):
        self.ctrl_mois.SetVisibleSelection()


class Annee(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        _PreparerPage(self)
        self.label_annee = wx.StaticText(self, -1, _(u"Année :"))
        self.ctrl_annee = CTRL_Annee(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(_LigneFormulaire(self.label_annee, self.ctrl_annee), 0, wx.EXPAND | wx.ALL, UTILS_UIMetrics.spacing(2))
        sizer.AddStretchSpacer(1)
        self.SetSizer(sizer)
        self.ctrl_annee.Bind(wx.EVT_SPINCTRL, self.OnSelectionAnnee)

    def OnSelectionAnnee(self, event):
        self.GetGrandParent().OnSelection()

    def GetDatesSelections(self):
        return self.ctrl_annee.GetDatesSelections()


class Vacances(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        _PreparerPage(self)
        self.label_annee = wx.StaticText(self, -1, _(u"Année :"))
        self.ctrl_annee = CTRL_Annee(self)
        self.label_periode = wx.StaticText(self, -1, _(u"Période :"))
        self.ctrl_periode = CTRL_ListBox(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        marge = UTILS_UIMetrics.spacing(2)
        sizer.Add(_LigneFormulaire(self.label_annee, self.ctrl_annee), 0, wx.EXPAND | wx.ALL, marge)
        sizer.Add(self.label_periode, 0, wx.LEFT | wx.RIGHT | wx.TOP, marge)
        sizer.Add(self.ctrl_periode, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, marge)
        self.SetSizer(sizer)

        self.ctrl_annee.Bind(wx.EVT_SPINCTRL, self.OnSelectionAnnee)
        self.ctrl_periode.Bind(wx.EVT_LISTBOX, self.OnSelectionPeriode)
        self.MAJ()

    def OnSelectionAnnee(self, event):
        self.MAJ()
        self.GetGrandParent().OnSelection()

    def OnSelectionPeriode(self, event):
        self.GetGrandParent().OnSelection()

    def GetDatesSelections(self):
        return self.ctrl_periode.GetDatesSelections()

    def MAJ(self):
        annee = self.ctrl_annee.GetAnnee()
        DB = GestionDB.DB()
        req = """SELECT nom, date_debut, date_fin
        FROM vacances
        WHERE annee=%d
        ORDER BY date_debut;""" % annee
        DB.ExecuterReq(req)
        listeVacances = DB.ResultatReq()
        DB.Close()
        listeChoix = []
        for nom, date_debut, date_fin in listeVacances:
            date_debutDD = datetime.date.fromisoformat(date_debut[:10])
            date_finDD = datetime.date.fromisoformat(date_fin[:10])
            listeChoix.append((nom, date_debutDD, date_finDD))
        self.ctrl_periode.SetListeChoix(listeChoix, conserveSelections=False)

    def SetVisibleSelection(self):
        self.ctrl_periode.SetVisibleSelection()


class Dates(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        _PreparerPage(self)
        self.label_date_debut = wx.StaticText(self, -1, _(u"Du :"))
        self.ctrl_date_debut = MyDatePickerCtrl(self)
        self.label_date_fin = wx.StaticText(self, -1, _(u"Au :"))
        self.ctrl_date_fin = MyDatePickerCtrl(self)
        self.ctrl_date_debut.SetToolTip(wx.ToolTip(_(u"Saisissez une date de début")))
        self.ctrl_date_fin.SetToolTip(wx.ToolTip(_(u"Saisissez une date de fin")))

        sizer = wx.BoxSizer(wx.VERTICAL)
        marge = UTILS_UIMetrics.spacing(2)
        sizer.Add(_LigneFormulaire(self.label_date_debut, self.ctrl_date_debut), 0, wx.EXPAND | wx.ALL, marge)
        sizer.Add(_LigneFormulaire(self.label_date_fin, self.ctrl_date_fin), 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, marge)
        sizer.AddStretchSpacer(1)
        self.SetSizer(sizer)

    def GetDates(self):
        return [(self.ctrl_date_debut.GetDate(), self.ctrl_date_fin.GetDate())]

    def OnSelection(self):
        self.GetGrandParent().OnSelection()

    def GetDatesSelections(self):
        return self.GetDates()


class CTRL(wx.Panel):
    """Sélection d'une période pour la grille de saisie des consommations."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.nomParent = self.GetParent().GetName()
        self.evtActif = True
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        self.notebook = wx.Notebook(self, -1, style=wx.BK_TOP)
        _AppliquerStyleControle(self.notebook, fond_donnees=False)
        self.notebook.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        self.page_dates = Dates(self.notebook)
        self.page_annee = Annee(self.notebook)
        self.page_vacances = Vacances(self.notebook)
        self.page_mois = Mois(self.notebook)

        self.notebook.AddPage(self.page_mois, _(u"Mois"))
        self.notebook.AddPage(self.page_vacances, _(u"Vacances"))
        self.notebook.AddPage(self.page_annee, _(u"Année"))
        self.notebook.AddPage(self.page_dates, _(u"Dates"))

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetMinSize((UTILS_UIMetrics.px(260), UTILS_UIMetrics.px(190)))
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def OnSelection(self):
        self.evtActif = False
        if self.nomParent == "grille":
            listeSelections = self.GetDatesSelections()
            self.parent.SetListesPeriodes(listeSelections)
            self.parent.MAJ_grille()
        if self.nomParent == "informations_medicales":
            listeSelections = self.GetDatesSelections()
            self.parent.SetListesPeriodes(listeSelections)
        self.evtActif = True

    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        if old == -1:
            event.Skip()
            return
        if self.nomParent == "grille" and self.evtActif is True:
            indexPage = event.GetSelection()
            page = self.notebook.GetPage(indexPage)
            listeSelections = page.GetDatesSelections()
            self.parent.SetListesPeriodes(listeSelections)
            self.parent.MAJ_grille()
        event.Skip()

    def GetDatesSelections(self):
        indexPage = self.notebook.GetSelection()
        page = self.notebook.GetPage(indexPage)
        return page.GetDatesSelections()

    def SetVisibleSelection(self):
        """Fait défiler la liste active jusqu'à la sélection courante."""
        try:
            indexPage = self.notebook.GetSelection()
            page = self.notebook.GetPage(indexPage)
            if indexPage in (0, 1):
                page.SetVisibleSelection()
        except Exception:
            pass

    def SetDictDonnees(self, dictDonnees={}):
        if dictDonnees is None:
            return
        self.evtActif = False
        numPage = dictDonnees["page"]
        annee = dictDonnees["annee"]
        listeSelections = dictDonnees["listeSelections"]
        dateDebut = dictDonnees["dateDebut"]
        dateFin = dictDonnees["dateFin"]

        self.notebook.SetSelection(numPage)
        page = self.notebook.GetPage(numPage)

        if numPage == 0:
            if annee is not None:
                page.ctrl_annee.SetValue(annee)
                page.MAJ()
            if 'phoenix' in wx.PlatformInfo:
                page.ctrl_mois.SetSelection(-1)
            else:
                page.ctrl_mois.DeselectAll()
            for index in listeSelections:
                page.ctrl_mois.SetSelectionIndex(index)

        if numPage == 1:
            if annee is not None:
                page.ctrl_annee.SetValue(annee)
                page.MAJ()
            if 'phoenix' in wx.PlatformInfo:
                page.ctrl_periode.SetSelection(-1)
            else:
                page.ctrl_periode.DeselectAll()
            for index in listeSelections:
                page.ctrl_periode.SetSelectionIndex(index)

        if numPage == 2 and annee is not None:
            page.ctrl_annee.SetValue(annee)

        if numPage == 3:
            if dateDebut is not None:
                page.ctrl_date_debut.SetDate(dateDebut)
            if dateFin is not None:
                page.ctrl_date_fin.SetDate(dateFin)

        self.evtActif = True

    def GetDictDonnees(self):
        dictDonnees = {}
        numPage = self.notebook.GetSelection()
        page = self.notebook.GetPage(numPage)

        if numPage == 0:
            dictDonnees["page"] = 0
            dictDonnees["listeSelections"] = page.ctrl_mois.GetSelections()
            dictDonnees["annee"] = page.ctrl_annee.GetValue()
            dictDonnees["dateDebut"] = None
            dictDonnees["dateFin"] = None

        if numPage == 1:
            dictDonnees["page"] = 1
            dictDonnees["listeSelections"] = page.ctrl_periode.GetSelections()
            dictDonnees["annee"] = page.ctrl_annee.GetValue()
            dictDonnees["dateDebut"] = None
            dictDonnees["dateFin"] = None

        if numPage == 2:
            dictDonnees["page"] = 2
            dictDonnees["listeSelections"] = []
            dictDonnees["annee"] = page.ctrl_annee.GetValue()
            dictDonnees["dateDebut"] = None
            dictDonnees["dateFin"] = None

        if numPage == 3:
            dictDonnees["page"] = 3
            dictDonnees["listeSelections"] = []
            dictDonnees["annee"] = None
            dictDonnees["dateDebut"] = page.ctrl_date_debut.GetDate()
            dictDonnees["dateFin"] = page.ctrl_date_fin.GetDate()

        dictDonnees["listePeriodes"] = self.GetDatesSelections()
        return dictDonnees


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        self.ctrl = CTRL(panel)
        contenu = wx.BoxSizer(wx.VERTICAL)
        contenu.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(2))
        panel.SetSizer(contenu)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(panel, 1, wx.EXPAND)
        self.SetSizer(principal)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, _(u"TEST"), size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
