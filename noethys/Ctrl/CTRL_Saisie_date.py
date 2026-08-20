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
import re

import six
import wx
import wx.lib.masked as masked
from dateutil import relativedelta
from dateutil.parser import parse, parserinfo

import Chemins
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Saisie_heure
from Utils import UTILS_Adaptations
from Utils import UTILS_Config
from Utils import UTILS_Dates
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _


ID_AIDE = 5
ID_AUJOURDHUI = 10
ID_HIER = 20
ID_DEMAIN = 30
ID_SEMAINE_ACTUELLE = 100
ID_SEMAINE_PRECEDENTE = 110
ID_SEMAINE_SUIVANTE = 120
ID_MOIS_ACTUEL = 200
ID_MOIS_PRECEDENT = 210
ID_MOIS_SUIVANT = 220
ID_ANNEE_ACTUELLE = 300
ID_ANNEE_PRECEDENTE = 310
ID_ANNEE_SUIVANTE = 320


datePattern = re.compile(
    r"(?P<jour>[\d]{1,2})/(?P<mois>[\d]{1,2})/(?P<annee>[\d]{4})"
)


class myparserinfo(parserinfo):
    JUMP = [" ", ".", ",", ";", "-", "/", "'",
            "at", "on", "and", "ad", "m", "t", "of",
            "st", "nd", "rd", "th"]

    WEEKDAYS = [(_(u"Lun"), _(u"Lundi")),
                (_(u"Mar"), _(u"Mardi")),
                (_(u"Mer"), _(u"Mercredi")),
                (_(u"Jeu"), _(u"Jeudi")),
                (_(u"Ven"), _(u"Vendredi")),
                (_(u"Sam"), _(u"Samedi")),
                (_(u"Dim"), _(u"Dimanche"))]
    MONTHS = [(_(u"Jan"), _(u"Janvier")),
              (_(u"Fév"), _(u"Février")),
              (_(u"Mar"), _(u"Mars")),
              (_(u"Avr"), _(u"Avril")),
              (_(u"Mai"), _(u"Mai")),
              (_(u"Juin"), _(u"Juin")),
              (_(u"Juil"), _(u"Juillet")),
              (_(u"Aoû"), _(u"Août")),
              (_(u"Sept"), _(u"Septembre")),
              (_(u"Oct"), _(u"Octobre")),
              (_(u"Nov"), _(u"Novembre")),
              (_(u"Déc"), _(u"Décembre"))]
    HMS = [("h", "hour", "hours"),
           ("m", "minute", "minutes"),
           ("s", "second", "seconds")]
    AMPM = [("am", "a"),
            ("pm", "p")]
    UTCZONE = ["UTC", "GMT", "Z"]
    PERTAIN = ["of"]
    TZOFFSET = {}

    def __init__(self):
        parserinfo.__init__(self, dayfirst=True, yearfirst=False)


def _MessageErreur(parent, message, titre=_(u"Erreur de date")):
    dlg = wx.MessageDialog(parent, message, titre, wx.OK | wx.ICON_EXCLAMATION)
    dlg.ShowModal()
    dlg.Destroy()


def _BitmapMenu(image):
    taille = UTILS_UIMetrics.icon_size("compact")
    chemin = Chemins.GetStaticIconPath(image, taille=taille)
    bitmap = wx.Bitmap(chemin, wx.BITMAP_TYPE_ANY)
    if bitmap.IsOk() and (bitmap.GetWidth() != taille or bitmap.GetHeight() != taille):
        source = bitmap.ConvertToImage().Scale(taille, taille, wx.IMAGE_QUALITY_HIGH)
        bitmap = wx.Bitmap(source)
    return bitmap


class Date(masked.TextCtrl):
    """Contrôle de date compact, DPI-aware et compatible avec le thème."""

    def __init__(self, parent, date_min="01/01/1900", date_max="01/01/2999",
                 size=(-1, -1), pos=wx.DefaultPosition):
        self.mask_date = UTILS_Config.GetParametre("mask_date", "##/##/####")
        masked.TextCtrl.__init__(
            self,
            parent,
            -1,
            "",
            style=wx.TE_CENTRE | wx.TE_PROCESS_ENTER,
            size=size,
            pos=pos,
            mask=self.mask_date,
        )
        self.parent = parent
        self.date_min = date_min
        self.date_max = date_max
        self.dateDD = None
        self.lienCtrlAge = False
        self._AppliqueStyle()

        self.Bind(wx.EVT_TEXT_ENTER, self.OnKillFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnContextMenu)
        if self.mask_date == "":
            self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)

    def _AppliqueStyle(self):
        try:
            police = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
            facteur = UTILS_Interface.GetTailleTexte() / 100.0
            police.SetPointSize(max(8, int(round(police.GetPointSize() * facteur))))
            self.SetFont(police)
        except Exception:
            pass

        try:
            largeur = max(
                UTILS_UIMetrics.px(108),
                self.GetTextExtent("00/00/0000")[0] + UTILS_UIMetrics.spacing(4),
            )
            self.SetMinSize((largeur, UTILS_UIMetrics.action_target("compact")))
            self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
            self.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        except Exception:
            pass

    def OnDoubleClick(self, event):
        pass

    def SetDate(self, date):
        """Importe une date string ou datetime."""
        if date is None or date == "":
            return
        try:
            if type(date) == datetime.date:
                dateDD = date
            if type(date) in (str, six.text_type):
                if date[2] == "/":
                    dateDD = datetime.datetime.strptime(date[:10], '%d/%m/%Y').date()
                else:
                    dateDD = datetime.date.fromisoformat(date[:10])
            self.SetValue(self.DateEngFr(str(dateDD)))
        except Exception:
            pass

    def GetDate(self, FR=False):
        """Récupère une date au format datetime ou français."""
        dateFR = self.GetValue()
        if dateFR == "  /  /    " or dateFR == "":
            return None
        validation = ValideDate(dateFR, self.date_min, self.date_max, avecMessages=False, mask=self.mask_date)
        if validation is False:
            return None
        dateDD = datetime.datetime.strptime(dateFR[:10], '%d/%m/%Y').date()
        dateFR = self.DateEngFr(str(dateDD))
        if FR is True:
            return dateFR
        return dateDD

    def DateEngFr(self, textDate):
        return str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])

    def DateFrEng(self, textDate):
        return str(textDate[6:10]) + "/" + str(textDate[3:5]) + "/" + str(textDate[:2])

    def OnKillFocus(self, event):
        self.MaJ_DateNaiss()
        self.FonctionValiderDate()
        try:
            self.parent.OnChoixDate()
        except Exception:
            pass
        if event is not None:
            event.Skip()

    def MaJ_DateNaiss(self):
        if self.GetValue() == "  /  /    ":
            if self.lienCtrlAge is True:
                self.parent.ctrl_age.SetValue("")
            return

    def FonctionValiderDate(self):
        if self.GetValue() != "" and self.mask_date == "":
            try:
                date = parse(self.GetValue(), myparserinfo())
                self.SetDate(datetime.date(year=date.year, month=date.month, day=date.day))
            except Exception:
                pass
        return ValideDate(self.GetValue(), self.date_min, self.date_max, mask=self.mask_date)

    def Validation(self):
        return self.FonctionValiderDate()

    def GetAge(self):
        bday = self.GetDate()
        datedujour = datetime.date.today()
        return (datedujour.year - bday.year) - int((datedujour.month, datedujour.day) < (bday.month, bday.day))

    def GetPanelParent(self):
        if self.parent.GetName() == "panel_date2":
            return self.parent.parent
        return self.parent

    def OnContextMenu(self, event):
        menuPop = UTILS_Adaptations.Menu()

        for identifiant, label, image in (
            (ID_AUJOURDHUI, _(u"Aujourd'hui"), "Images/16x16/Date_actuelle.png"),
            (ID_HIER, _(u"Hier"), "Images/16x16/Date_precedente.png"),
            (ID_DEMAIN, _(u"Demain"), "Images/16x16/Date_suivante.png"),
        ):
            item = wx.MenuItem(menuPop, identifiant, label)
            item.SetBitmap(_BitmapMenu(image))
            menuPop.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.OnActionMenu, id=identifiant)

        menuPop.AppendSeparator()

        listeFonctions = [
            (ID_SEMAINE_ACTUELLE, _(u"Semaine actuelle")),
            (ID_SEMAINE_PRECEDENTE, _(u"Semaine précédente")),
            (ID_SEMAINE_SUIVANTE, _(u"Semaine suivante")),
            (None, None),
            (ID_MOIS_ACTUEL, _(u"Mois actuel")),
            (ID_MOIS_PRECEDENT, _(u"Mois précédent")),
            (ID_MOIS_SUIVANT, _(u"Mois suivant")),
            (None, None),
            (ID_ANNEE_ACTUELLE, _(u"Année actuelle")),
            (ID_ANNEE_PRECEDENTE, _(u"Année précédente")),
            (ID_ANNEE_SUIVANTE, _(u"Année suivante")),
        ]
        for identifiant, label in listeFonctions:
            if identifiant is None:
                menuPop.AppendSeparator()
            else:
                sousMenu = UTILS_Adaptations.Menu()
                sousMenu.AppendItem(wx.MenuItem(sousMenu, identifiant + 1, _(u"Date de début")))
                self.Bind(wx.EVT_MENU, self.OnActionMenu, id=identifiant + 1)
                sousMenu.AppendItem(wx.MenuItem(sousMenu, identifiant + 2, _(u"Date de fin")))
                self.Bind(wx.EVT_MENU, self.OnActionMenu, id=identifiant + 2)
                menuPop.AppendMenu(identifiant, label, sousMenu)

        menuPop.AppendSeparator()
        item = wx.MenuItem(menuPop, ID_AIDE, _(u"Aide"))
        item.SetBitmap(_BitmapMenu("Images/16x16/Aide.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.OnActionMenu, id=ID_AIDE)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def OnActionMenu(self, event=None):
        identifiant = event.GetId()
        dateJour = datetime.date.today()

        if identifiant == ID_AUJOURDHUI:
            self.SetDate(dateJour)
        if identifiant == ID_HIER:
            self.SetDate(dateJour - datetime.timedelta(days=1))
        if identifiant == ID_DEMAIN:
            self.SetDate(dateJour + datetime.timedelta(days=1))

        if identifiant == ID_SEMAINE_ACTUELLE + 1:
            date = dateJour + relativedelta.relativedelta(weekday=relativedelta.MO(-1))
            self.SetDate(date)
        if identifiant == ID_SEMAINE_ACTUELLE + 2:
            date = dateJour + relativedelta.relativedelta(weekday=relativedelta.MO(-1))
            self.SetDate(date + datetime.timedelta(days=6))

        if identifiant == ID_SEMAINE_PRECEDENTE + 1:
            date = dateJour + relativedelta.relativedelta(weekday=relativedelta.SU(-1))
            self.SetDate(date - datetime.timedelta(days=6))
        if identifiant == ID_SEMAINE_PRECEDENTE + 2:
            date = dateJour + relativedelta.relativedelta(weekday=relativedelta.SU(-1))
            self.SetDate(date)

        if identifiant == ID_SEMAINE_SUIVANTE + 1:
            date = dateJour + relativedelta.relativedelta(weekday=relativedelta.MO(+1))
            self.SetDate(date)
        if identifiant == ID_SEMAINE_SUIVANTE + 2:
            date = dateJour + relativedelta.relativedelta(weekday=relativedelta.MO(+1))
            self.SetDate(date + datetime.timedelta(days=6))

        if identifiant == ID_MOIS_ACTUELLE + 1 if False else False:
            pass
        if identifiant == ID_MOIS_ACTUEL + 1:
            self.SetDate(datetime.date(dateJour.year, dateJour.month, 1))
        if identifiant == ID_MOIS_ACTUEL + 2:
            mois = calendar.monthrange(dateJour.year, dateJour.month)
            self.SetDate(datetime.date(dateJour.year, dateJour.month, mois[1]))

        if identifiant == ID_MOIS_PRECEDENT + 1:
            date = dateJour + relativedelta.relativedelta(months=-1)
            self.SetDate(datetime.date(date.year, date.month, 1))
        if identifiant == ID_MOIS_PRECEDENT + 2:
            date = dateJour + relativedelta.relativedelta(months=-1)
            mois = calendar.monthrange(date.year, date.month)
            self.SetDate(datetime.date(date.year, date.month, mois[1]))

        if identifiant == ID_MOIS_SUIVANT + 1:
            date = dateJour + relativedelta.relativedelta(months=+1)
            self.SetDate(datetime.date(date.year, date.month, 1))
        if identifiant == ID_MOIS_SUIVANT + 2:
            date = dateJour + relativedelta.relativedelta(months=+1)
            mois = calendar.monthrange(date.year, date.month)
            self.SetDate(datetime.date(date.year, date.month, mois[1]))

        if identifiant == ID_ANNEE_ACTUELLE + 1 if False else False:
            pass
        if identifiant == ID_ANNEE_ACTUELLE + 1:
            self.SetDate(datetime.date(dateJour.year, 1, 1))
        if identifiant == ID_ANNEE_ACTUELLE + 2:
            self.SetDate(datetime.date(dateJour.year, 12, 31))

        if identifiant == ID_ANNEE_PRECEDENTE + 1:
            date = dateJour + relativedelta.relativedelta(years=-1)
            self.SetDate(datetime.date(date.year, 1, 1))
        if identifiant == ID_ANNEE_PRECEDENTE + 2:
            date = dateJour + relativedelta.relativedelta(years=-1)
            self.SetDate(datetime.date(date.year, 12, 31))

        if identifiant == ID_ANNEE_SUIVANTE + 1:
            date = dateJour + relativedelta.relativedelta(years=+1)
            self.SetDate(datetime.date(date.year, 1, 1))
        if identifiant == ID_ANNEE_SUIVANTE + 2:
            date = dateJour + relativedelta.relativedelta(years=+1)
            self.SetDate(datetime.date(date.year, 12, 31))

        if identifiant == ID_AIDE:
            from Utils import UTILS_Aide
            UTILS_Aide.Aide("Slectionnerunedate")


def ValideDate(texte, date_min="01/01/1900", date_max="01/01/2999", avecMessages=True, mask=""):
    """Vérificateur de validité de date."""
    if texte == "  /  /    " or texte == "":
        return True

    listeErreurs = []
    date = datePattern.match(texte)
    if date:
        jour = int(date.group("jour"))
        if jour == 0 or jour > 31:
            listeErreurs.append(_(u"le jour"))
        mois = int(date.group("mois"))
        if mois == 0 or mois > 12:
            listeErreurs.append(_(u"le mois"))
        annee = int(date.group("annee"))
        if annee < 1900 or annee > 2999:
            listeErreurs.append(_(u"l'année"))

        if listeErreurs:
            if avecMessages is True:
                nbErreurs = len(listeErreurs)
                if nbErreurs == 1:
                    message = _(u"Une incohérence a été détectée dans ") + listeErreurs[0]
                else:
                    message = _(u"Des incohérences ont été détectées dans ") + listeErreurs[0]
                    if nbErreurs == 2:
                        message += " et " + listeErreurs[1]
                    elif nbErreurs == 3:
                        message += ", " + listeErreurs[1] + " et " + listeErreurs[2]
                message += _(u" de la date que vous venez de saisir. Veuillez la vérifier.")
                _MessageErreur(None, message)
            return False

        date_min_num = int(str(date_min[6:10]) + str(date_min[3:5]) + str(date_min[:2]))
        date_max_num = int(str(date_max[6:10]) + str(date_max[3:5]) + str(date_max[:2]))
        date_sel = int(str(annee) + ('0' if mois < 10 else '') + str(mois) +
                       ('0' if jour < 10 else '') + str(jour))

        if date_sel < date_min_num:
            if avecMessages is True:
                _MessageErreur(None, _(u"La date que vous venez de saisir semble trop ancienne. Veuillez la vérifier."))
            return False
        if date_sel > date_max_num:
            if avecMessages is True:
                _MessageErreur(None, _(u"La date que vous venez de saisir semble trop élevée. Veuillez la vérifier."))
            return False

        try:
            datetime.date(year=annee, month=mois, day=jour)
        except Exception:
            pass
        else:
            return True

    if avecMessages is True:
        _MessageErreur(None, _(u"La date que vous venez de saisir ne semble pas valide !"))
    return False


class Date2(wx.Panel):
    """Contrôle Date avec bouton calendrier et heure optionnelle."""

    def __init__(self, parent, date_min="01/01/1910", date_max="01/01/2030",
                 activeCallback=True, size=(-1, -1), heure=False, pos=wx.DefaultPosition):
        wx.Panel.__init__(self, parent, id=-1, name="panel_date2", size=size, pos=pos, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.activeCallback = activeCallback
        self.heure = heure

        self.ctrl_date = Date(self, date_min, date_max)
        self.bouton_calendrier = CTRL_Bouton_image.CTRL(
            self,
            texte="",
            iconeFluent="calendar",
            tailleImage=(UTILS_UIMetrics.icon_size("inline"), UTILS_UIMetrics.icon_size("inline")),
        )
        self.Bind(wx.EVT_BUTTON, self.OnBoutonCalendrier, self.bouton_calendrier)
        self.bouton_calendrier.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour sélectionner la date dans le calendrier")))

        self.ctrl_heure = None
        if heure is True:
            self.ctrl_heure = CTRL_Saisie_heure.Heure(self)

        try:
            self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))
        except Exception:
            pass

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.ctrl_date, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.bouton_calendrier, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, UTILS_UIMetrics.spacing(1))
        if self.ctrl_heure is not None:
            sizer.Add(self.ctrl_heure, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, UTILS_UIMetrics.spacing(1))
        self.SetSizer(sizer)
        self.Fit()
        self.Layout()

    def SetToolTipString(self, texte=""):
        self.ctrl_date.SetToolTip(wx.ToolTip(texte))

    def SetToolTip(self, tip=None):
        self.ctrl_date.SetToolTip(tip)

    def OnBoutonCalendrier(self, event):
        from Dlg import DLG_calendrier_simple
        dlg = DLG_calendrier_simple.Dialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            date = dlg.GetDate()
            self.ctrl_date.SetDate(date)
            self.OnChoixDate()
        dlg.Destroy()

    def OnChoixDate(self):
        if self.activeCallback is True:
            try:
                self.parent.OnChoixDate()
            except Exception:
                pass

    def SetDate(self, date):
        if type(date) == datetime.datetime or (type(date) in (str, six.text_type) and ":" in date):
            date_dt = UTILS_Dates.DateEngEnDateDDT(date)
            self.ctrl_date.SetDate(datetime.datetime.strftime(date_dt, "%Y-%m-%d"))
            if self.heure is True:
                self.ctrl_heure.SetHeure(datetime.datetime.strftime(date_dt, "%H:%M"))
        else:
            self.ctrl_date.SetDate(date)

    def GetDate(self, FR=False):
        if self.heure is False:
            return self.ctrl_date.GetDate(FR=FR)
        date = self.ctrl_date.GetDate()
        heure = self.ctrl_heure.GetHeure()
        if date is None or heure is None or heure == "  :  ":
            return None
        return datetime.datetime(
            year=date.year,
            month=date.month,
            day=date.day,
            hour=int(heure[:2]),
            minute=int(heure[3:]),
        )

    def FonctionValiderDate(self):
        return self.Validation()

    def Validation(self):
        if self.heure is False:
            return self.ctrl_date.FonctionValiderDate()

        date_valide = self.ctrl_date.FonctionValiderDate()
        if date_valide is False:
            return False

        heure = self.ctrl_heure.GetHeure()
        if heure is None or self.ctrl_heure.Validation() is False:
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement saisir une heure valide !"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_heure.SetFocus()
            return False
        return True

    def GetAge(self):
        return self.ctrl_date.GetAge()

    def SetInsertionPoint(self, position=0):
        self.ctrl_date.SetInsertionPoint(position)

    def SetFocus(self):
        self.ctrl_date.SetFocus()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="panel_test")
        self.ctrl1 = Date2(panel, heure=True)
        self.ctrl2 = Date2(panel)
        self.bouton1 = wx.Button(panel, -1, u"Tester la validité du ctrl 1")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl1, 0, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(2))
        sizer.Add(self.ctrl2, 0, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(2))
        sizer.Add(self.bouton1, 0, wx.ALL, UTILS_UIMetrics.spacing(2))
        panel.SetSizer(sizer)
        cadre = wx.BoxSizer(wx.VERTICAL)
        cadre.Add(panel, 1, wx.EXPAND)
        self.SetSizer(cadre)
        self.Layout()
        self.CentreOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnBouton1, self.bouton1)

    def OnBouton1(self, event):
        print(self.ctrl1.Validation())


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
