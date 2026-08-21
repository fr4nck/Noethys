#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-18 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import calendar
import datetime

import wx

import GestionDB
from Ctrl import CTRL_ActionRepens, CTRL_Saisie_date
from Utils import UTILS_IconesRepens
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


MOIS = [
    _(u"Janvier"), _(u"Février"), _(u"Mars"), _(u"Avril"),
    _(u"Mai"), _(u"Juin"), _(u"Juillet"), _(u"Août"),
    _(u"Septembre"), _(u"Octobre"), _(u"Novembre"), _(u"Décembre"),
]


def _StylePanel(panel):
    Style.appliquer_fenetre(panel, "surface")


def _StyleLabel(label):
    Style.appliquer_texte(label, role="label", role_texte="on_surface", role_fond="surface")


def _StyleSaisie(ctrl, largeur=-1):
    Style.appliquer_saisie(ctrl)
    ctrl.SetMinSize((largeur, Style.cible_action("compact")))


def _AjouteChamp(sizer, label, ctrl, marge=None):
    if marge is None:
        marge = Style.espace(2)
    sizer.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
    sizer.Add(ctrl, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, Style.espace(1))
    sizer.AddSpacer(marge)


def _Action(parent, label, tooltip, icone=None, variante="ghost"):
    return CTRL_ActionRepens.CTRL(
        parent,
        label=label,
        icone=icone,
        variante=variante,
        tooltip=tooltip,
        compact=True,
    )


class Page_Semaines(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        _StylePanel(self)

        self.label_semaine = wx.StaticText(self, -1, _(u"Semaine :"))
        self.ctrl_semaine = wx.SpinCtrl(self, -1, "", min=1, max=53)
        self.label_annee = wx.StaticText(self, -1, _(u"Année :"))
        self.ctrl_annee = wx.SpinCtrl(self, -1, "", min=1977, max=2999)
        self.bouton_aujourdhui = _Action(
            self,
            _(u"Aujourd'hui"),
            _(u"Sélectionnez la semaine en cours"),
            icone="calendar",
        )

        for label in (self.label_semaine, self.label_annee):
            _StyleLabel(label)
        _StyleSaisie(self.ctrl_semaine, Style.px(82))
        _StyleSaisie(self.ctrl_annee, Style.px(92))
        self.ctrl_semaine.SetToolTip(wx.ToolTip(_(u"Sélectionnez une semaine")))
        self.ctrl_annee.SetToolTip(wx.ToolTip(_(u"Sélectionnez une année")))

        self.Bind(wx.EVT_SPINCTRL, self.parent.CallBack, self.ctrl_semaine)
        self.Bind(wx.EVT_SPINCTRL, self.parent.CallBack, self.ctrl_annee)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAujourdhui, self.bouton_aujourdhui)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        _AjouteChamp(sizer, self.label_semaine, self.ctrl_semaine)
        _AjouteChamp(sizer, self.label_annee, self.ctrl_annee)
        sizer.Add(self.bouton_aujourdhui, 0, wx.ALIGN_CENTER_VERTICAL)
        cadre = wx.BoxSizer(wx.VERTICAL)
        cadre.Add(sizer, 0, wx.ALL, Style.espace(3))
        self.SetSizer(cadre)
        self.SelectAujourdhui()

    def SelectAujourdhui(self):
        dateDuJour = datetime.date.today()
        self.ctrl_annee.SetValue(dateDuJour.year)
        self.ctrl_semaine.SetValue(dateDuJour.isocalendar()[1])

    def OnBoutonAujourdhui(self, event=None):
        self.SelectAujourdhui()
        self.parent.CallBack()

    def GetDateDebut(self):
        annee = int(self.ctrl_annee.GetValue())
        num_semaine = int(self.ctrl_semaine.GetValue())
        try:
            return datetime.date.fromisocalendar(annee, num_semaine, 1)
        except ValueError:
            return datetime.datetime.strptime("%d-W%d-1" % (annee, num_semaine), "%Y-W%W-%w").date()

    def GetDateFin(self):
        return self.GetDateDebut() + datetime.timedelta(days=6)


class Page_Mois(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        _StylePanel(self)

        self.label_mois = wx.StaticText(self, -1, _(u"Mois :"))
        self.ctrl_mois = wx.Choice(self, -1, choices=MOIS)
        self.spin_mois = wx.SpinButton(self, -1, style=wx.SP_VERTICAL)
        self.spin_mois.SetRange(-1, 1)
        self.label_annee = wx.StaticText(self, -1, _(u"Année :"))
        self.ctrl_annee = wx.SpinCtrl(self, -1, "", min=1977, max=2999)
        self.bouton_aujourdhui = _Action(
            self,
            _(u"Aujourd'hui"),
            _(u"Sélectionnez le mois en cours"),
            icone="calendar",
        )

        for label in (self.label_mois, self.label_annee):
            _StyleLabel(label)
        _StyleSaisie(self.ctrl_mois, Style.px(132))
        _StyleSaisie(self.ctrl_annee, Style.px(92))
        self.spin_mois.SetMinSize((Style.px(28), Style.cible_action("compact")))

        self.ctrl_mois.SetToolTip(wx.ToolTip(_(u"Sélectionnez un mois")))
        self.ctrl_annee.SetToolTip(wx.ToolTip(_(u"Sélectionnez une année")))

        self.Bind(wx.EVT_SPIN, self.OnSpinMois, self.spin_mois)
        self.Bind(wx.EVT_CHOICE, self.parent.CallBack, self.ctrl_mois)
        self.Bind(wx.EVT_SPINCTRL, self.parent.CallBack, self.ctrl_annee)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAujourdhui, self.bouton_aujourdhui)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_mois, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.ctrl_mois, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, Style.espace(1))
        sizer.Add(self.spin_mois, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, Style.espace(1))
        sizer.AddSpacer(Style.espace(2))
        _AjouteChamp(sizer, self.label_annee, self.ctrl_annee)
        sizer.Add(self.bouton_aujourdhui, 0, wx.ALIGN_CENTER_VERTICAL)
        cadre = wx.BoxSizer(wx.VERTICAL)
        cadre.Add(sizer, 0, wx.ALL, Style.espace(3))
        self.SetSizer(cadre)
        self.SelectAujourdhui()

    def SelectAujourdhui(self):
        dateDuJour = datetime.date.today()
        self.ctrl_annee.SetValue(dateDuJour.year)
        self.ctrl_mois.SetSelection(dateDuJour.month - 1)

    def OnBoutonAujourdhui(self, event=None):
        self.SelectAujourdhui()
        self.parent.CallBack()

    def OnSpinMois(self, event):
        direction = event.GetPosition()
        index = self.ctrl_mois.GetSelection() + direction
        if 0 <= index < 12:
            self.ctrl_mois.SetSelection(index)
            self.parent.CallBack()
        self.spin_mois.SetValue(0)

    def GetDateDebut(self):
        return datetime.date(int(self.ctrl_annee.GetValue()), self.ctrl_mois.GetSelection() + 1, 1)

    def GetDateFin(self):
        annee = int(self.ctrl_annee.GetValue())
        mois = self.ctrl_mois.GetSelection() + 1
        return datetime.date(annee, mois, calendar.monthrange(annee, mois)[1])


class Page_Vacances(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        _StylePanel(self)

        self.label_vacances = wx.StaticText(self, -1, _(u"Période :"))
        self.ctrl_vacances = wx.Choice(self, -1, choices=[])
        self.label_annee = wx.StaticText(self, -1, _(u"Année :"))
        self.ctrl_annee = wx.SpinCtrl(self, -1, "", min=1977, max=2999)
        for label in (self.label_vacances, self.label_annee):
            _StyleLabel(label)
        _StyleSaisie(self.ctrl_vacances, Style.px(170))
        _StyleSaisie(self.ctrl_annee, Style.px(92))

        self.ctrl_vacances.SetToolTip(wx.ToolTip(_(u"Sélectionnez une période de vacances")))
        self.ctrl_annee.SetToolTip(wx.ToolTip(_(u"Sélectionnez une année")))
        self.Bind(wx.EVT_CHOICE, self.parent.CallBack, self.ctrl_vacances)
        self.Bind(wx.EVT_SPINCTRL, self.OnChoixAnnee, self.ctrl_annee)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        _AjouteChamp(sizer, self.label_vacances, self.ctrl_vacances)
        _AjouteChamp(sizer, self.label_annee, self.ctrl_annee, 0)
        cadre = wx.BoxSizer(wx.VERTICAL)
        cadre.Add(sizer, 0, wx.ALL, Style.espace(3))
        self.SetSizer(cadre)
        self.SelectAujourdhui()

    def SelectAujourdhui(self):
        self.ctrl_annee.SetValue(datetime.date.today().year)
        self.MAJVacances()

    def OnChoixAnnee(self, event=None):
        self.MAJVacances()
        self.parent.CallBack()

    def MAJVacances(self):
        DB = GestionDB.DB()
        req = """SELECT nom, date_debut, date_fin
        FROM vacances
        WHERE annee=%d
        ORDER BY date_debut;""" % self.ctrl_annee.GetValue()
        DB.ExecuterReq(req)
        listeVacances = DB.ResultatReq()
        DB.Close()

        self.dictVacances = {}
        listeChoix = []
        for index, (nom, date_debut, date_fin) in enumerate(listeVacances):
            debut = datetime.date.fromisoformat(date_debut[:10])
            fin = datetime.date.fromisoformat(date_fin[:10])
            listeChoix.append(nom)
            self.dictVacances[index] = (debut, fin)
        self.ctrl_vacances.Set(listeChoix)
        self.ctrl_vacances.Enable(bool(listeChoix))
        if listeChoix:
            self.ctrl_vacances.Select(0)

    def GetDatesVacances(self):
        index = self.ctrl_vacances.GetSelection()
        return self.dictVacances[index] if index != -1 else (None, None)

    def GetDateDebut(self):
        return self.GetDatesVacances()[0]

    def GetDateFin(self):
        return self.GetDatesVacances()[1]


class Page_Dates(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        _StylePanel(self)

        self.label_periode = wx.StaticText(self, wx.ID_ANY, _(u"Du"))
        self.ctrl_date_debut = CTRL_Saisie_date.Date2(self)
        self.label_au = wx.StaticText(self, wx.ID_ANY, _(u"au"))
        self.ctrl_date_fin = CTRL_Saisie_date.Date2(self)
        self.bouton_appliquer_dates = _Action(
            self,
            _(u"Appliquer"),
            _(u"Cliquez ici pour valider la période saisie"),
            variante="secondaire",
        )
        for label in (self.label_periode, self.label_au):
            _StyleLabel(label)

        self.ctrl_date_debut.SetToolTip(wx.ToolTip(_(u"Saisissez la date de début de la période")))
        self.ctrl_date_fin.SetToolTip(wx.ToolTip(_(u"Saisissez la date de fin de la période")))
        self.Bind(wx.EVT_BUTTON, self.parent.CallBack, self.bouton_appliquer_dates)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.label_periode, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.ctrl_date_debut, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, Style.espace(1))
        sizer.Add(self.label_au, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, Style.espace(2))
        sizer.Add(self.ctrl_date_fin, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, Style.espace(1))
        sizer.Add(self.bouton_appliquer_dates, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, Style.espace(2))
        cadre = wx.BoxSizer(wx.VERTICAL)
        cadre.Add(sizer, 0, wx.ALL, Style.espace(3))
        self.SetSizer(cadre)

        self.ctrl_date_debut.SetDate(datetime.date.today() - datetime.timedelta(days=3))
        self.ctrl_date_fin.SetDate(datetime.date.today() + datetime.timedelta(days=30))

    def OnChoixDate(self):
        self.parent.CallBack()

    def GetDateDebut(self):
        return self.ctrl_date_debut.GetDate()

    def GetDateFin(self):
        return self.ctrl_date_fin.GetDate()


class Page_Jour(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        _StylePanel(self)

        self.ctrl_date = CTRL_Saisie_date.Date2(self)
        self.bouton_appliquer_dates = _Action(
            self,
            _(u"Appliquer"),
            _(u"Cliquez ici pour valider la date saisie"),
            variante="secondaire",
        )
        self.bouton_aujourdhui = _Action(
            self,
            _(u"Aujourd'hui"),
            _(u"Sélectionnez la date du jour"),
            icone="calendar",
        )
        self.ctrl_date.SetToolTip(wx.ToolTip(_(u"Saisissez une date")))
        self.Bind(wx.EVT_BUTTON, self.parent.CallBack, self.bouton_appliquer_dates)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAujourdhui, self.bouton_aujourdhui)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.ctrl_date, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.bouton_appliquer_dates, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, Style.espace(2))
        sizer.Add(self.bouton_aujourdhui, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, Style.espace(1))
        cadre = wx.BoxSizer(wx.VERTICAL)
        cadre.Add(sizer, 0, wx.ALL, Style.espace(3))
        self.SetSizer(cadre)
        self.SelectAujourdhui()

    def SelectAujourdhui(self):
        self.ctrl_date.SetDate(datetime.date.today())

    def OnBoutonAujourdhui(self, event=None):
        self.SelectAujourdhui()
        self.parent.CallBack()

    def OnChoixDate(self):
        self.parent.CallBack()

    def GetDateDebut(self):
        return self.ctrl_date.GetDate()

    def GetDateFin(self):
        return self.ctrl_date.GetDate()


class CTRL(wx.Notebook):
    def __init__(self, parent, callback=None):
        wx.Notebook.__init__(self, parent, id=-1, style=wx.BK_DEFAULT)
        self.parent = parent
        self.callback = callback
        self.dictPages = {}
        self.callback_actif = True
        Style.appliquer_fenetre(self, "surface")

        self.listePages = [
            {"code": "mois", "ctrl": Page_Mois(self), "label": _(u"Mois"), "icone": "calendar_month"},
            {"code": "semaine", "ctrl": Page_Semaines(self), "label": _(u"Semaine"), "icone": "calendar_week"},
            {"code": "vacances", "ctrl": Page_Vacances(self), "label": _(u"Vacances"), "icone": "calendar"},
            {"code": "periode", "ctrl": Page_Dates(self), "label": _(u"Période"), "icone": "calendar"},
            {"code": "date", "ctrl": Page_Jour(self), "label": _(u"Jour"), "icone": "calendar_day"},
        ]

        taille_icone = Style.taille_icone("inline")
        il = wx.ImageList(taille_icone, taille_icone)
        self.dictImages = {}
        for page in self.listePages:
            bitmap = UTILS_IconesRepens.GetBitmap(
                page["icone"],
                taille=taille_icone,
                role="on_surface_variant",
            )
            self.dictImages[page["code"]] = il.Add(bitmap)
        self.AssignImageList(il)

        for index, page in enumerate(self.listePages):
            self.AddPage(page["ctrl"], page["label"])
            self.SetPageImage(index, self.dictImages[page["code"]])
            self.dictPages[page["code"]] = page["ctrl"]
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def CallBack(self, event=None):
        if self.callback is not None and self.callback_actif:
            self.callback()

    def GetPageActive(self):
        return self.listePages[self.GetSelection()]["ctrl"]

    def GetPageAvecCode(self, codePage=""):
        return self.dictPages[codePage]

    def AffichePage(self, codePage=""):
        for index, page in enumerate(self.listePages):
            if page["code"] == codePage:
                self.SetSelection(index)
                return

    def OnPageChanged(self, event):
        self.CallBack()
        if event is not None:
            event.Skip()

    def GetDateDebut(self):
        return self.GetPageActive().GetDateDebut()

    def GetDateFin(self):
        return self.GetPageActive().GetDateFin()

    def SetModePeriode(self, code=""):
        self.callback_actif = False
        self.AffichePage(code)
        self.callback_actif = True

    def GetModePeriode(self):
        return self.listePages[self.GetSelection()]["code"]


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(panel, "surface")
        self.ctrl = CTRL(panel)
        bouton_test = CTRL_ActionRepens.CTRL(panel, label=u"Test", variante="secondaire")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, Style.espace(2))
        sizer.Add(bouton_test, 0, wx.ALL, Style.espace(2))
        panel.SetSizer(sizer)
        cadre = wx.BoxSizer(wx.VERTICAL)
        cadre.Add(panel, 1, wx.EXPAND)
        self.SetSizer(cadre)
        self.SetMinSize((Style.px(520), Style.px(280)))
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(900, 420))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
