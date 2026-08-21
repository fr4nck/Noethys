#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-18 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import wx

import GestionDB
from Ctrl import CTRL_ActionRepens
from Ctrl import CTRL_Grille_periode
from Ctrl import CTRL_Selection_activites
from Utils import UTILS_Dates
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


def GetSQLdates(listePeriodes=[]):
    texteSQL = ""
    for date_debut, date_fin in listePeriodes:
        texteSQL += "(date>='%s' AND date<='%s') OR " % (date_debut, date_fin)
    if len(texteSQL) > 0:
        texteSQL = "(" + texteSQL[:-4] + ")"
    else:
        texteSQL = "date=0"
    return texteSQL


def _AppliquerStyleListe(ctrl):
    """Applique aux listes natives la grammaire commune Repens."""
    Style.appliquer_liste(ctrl)
    ctrl.SetMinSize((-1, Style.hauteur_panneau("secondary")))


class CTRL_Activites(wx.CheckListBox):
    def __init__(self, parent):
        wx.CheckListBox.__init__(self, parent, -1)
        self.parent = parent
        self.data = []
        self.listePeriodes = []
        self.SetToolTip(wx.ToolTip(_(u"Cochez les activités à afficher")))
        self.listeActivites = []
        self.dictActivites = {}
        _AppliquerStyleListe(self)
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheck)

    def SetPeriodes(self, listePeriodes=[]):
        self.listePeriodes = listePeriodes
        self.MAJ()
        self.CocheTout()

    def MAJ(self):
        self.listeActivites, self.dictActivites = self.Importation()
        self.SetListeChoix()

    def Importation(self):
        listeActivites = []
        dictActivites = {}
        if len(self.listePeriodes) == 0:
            return listeActivites, dictActivites

        conditionsPeriodes = GetSQLdates(self.listePeriodes)
        DB = GestionDB.DB()
        req = """SELECT activites.IDactivite, nom, abrege, date_debut, date_fin
        FROM activites
        LEFT JOIN ouvertures ON ouvertures.IDactivite = activites.IDactivite
        WHERE %s
        GROUP BY activites.IDactivite
        ORDER BY date_fin DESC;""" % conditionsPeriodes
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        for IDactivite, nom, abrege, date_debut, date_fin in listeDonnees:
            if date_debut is not None:
                date_debut = UTILS_Dates.DateEngEnDateDD(date_debut)
            if date_fin is not None:
                date_fin = UTILS_Dates.DateEngEnDateDD(date_fin)
            dictTemp = {"nom": nom, "abrege": abrege, "date_debut": date_debut, "date_fin": date_fin, "tarifs": {}}
            dictActivites[IDactivite] = dictTemp
            listeActivites.append((nom, IDactivite))
        listeActivites.sort()
        return listeActivites, dictActivites

    def SetListeChoix(self):
        self.Clear()
        for nom, _IDactivite in self.listeActivites:
            self.Append(nom)

    def GetIDcoches(self):
        listeIDcoches = []
        for index in range(0, len(self.listeActivites)):
            if self.IsChecked(index):
                listeIDcoches.append(self.listeActivites[index][1])
        return listeIDcoches

    def CocheTout(self):
        for index in range(0, len(self.listeActivites)):
            self.Check(index)

    def SetIDcoches(self, listeIDcoches=[]):
        for index in range(0, len(self.listeActivites)):
            ID = self.listeActivites[index][1]
            if ID in listeIDcoches:
                self.Check(index)

    def OnCheck(self, event):
        self.parent.OnCheckActivites()

    def GetListeActivites(self):
        return self.GetIDcoches()

    def GetDictActivites(self):
        return self.dictActivites


class CTRL_Groupes(wx.CheckListBox):
    def __init__(self, parent):
        wx.CheckListBox.__init__(self, parent, -1)
        self.parent = parent
        self.data = []
        self.date = None
        self.listeActivites = []
        self.SetToolTip(wx.ToolTip(_(u"Cochez les groupes à afficher")))
        self.listeGroupes = []
        self.dictGroupes = {}
        _AppliquerStyleListe(self)

    def SetActivites(self, listeActivites=[]):
        self.listeActivites = listeActivites
        self.MAJ()
        self.CocheTout()

    def MAJ(self):
        self.listeGroupes, self.dictGroupes = self.Importation()
        self.SetListeChoix()

    def Importation(self):
        listeGroupes = []
        dictGroupes = {}
        if len(self.listeActivites) == 0:
            return listeGroupes, dictGroupes
        if len(self.listeActivites) == 1:
            conditionActivites = "(%d)" % self.listeActivites[0]
        else:
            conditionActivites = str(tuple(self.listeActivites))
        DB = GestionDB.DB()
        req = """SELECT IDgroupe, groupes.IDactivite, groupes.nom, activites.nom
        FROM groupes
        LEFT JOIN activites ON activites.IDactivite = groupes.IDactivite
        WHERE groupes.IDactivite IN %s
        ORDER BY groupes.nom;""" % conditionActivites
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        for IDgroupe, IDactivite, nom, nomActivite in listeDonnees:
            dictTemp = {"nom": nom, "IDactivite": IDactivite, "nomActivite": nomActivite}
            dictGroupes[IDgroupe] = dictTemp
            listeGroupes.append((nom, IDgroupe, nomActivite))
        listeGroupes.sort()
        return listeGroupes, dictGroupes

    def SetListeChoix(self):
        self.Clear()
        for nom, _IDgroupe, nomActivite in self.listeGroupes:
            self.Append(u"%s (%s)" % (nom, nomActivite))

    def GetIDcoches(self):
        listeIDcoches = []
        for index in range(0, len(self.listeGroupes)):
            if self.IsChecked(index):
                listeIDcoches.append(self.listeGroupes[index][1])
        return listeIDcoches

    def CocheTout(self):
        for index in range(0, len(self.listeGroupes)):
            self.Check(index)

    def SetIDcoches(self, listeIDcoches=[]):
        for index in range(0, len(self.listeGroupes)):
            ID = self.listeGroupes[index][1]
            if ID in listeIDcoches:
                self.Check(index)

    def GetListeGroupes(self):
        return self.GetIDcoches()

    def GetDictGroupes(self):
        return self.dictGroupes


class CTRL(wx.Panel):
    """Sélection dense des inscrits ou présents, sans grille de layout figée."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        Style.appliquer_fenetre(self, "surface")

        self.staticbox_mode_staticbox = wx.StaticBox(self, -1, _(u"Mode de sélection"))
        self.radio_inscrits = wx.RadioButton(self, -1, _(u"Inscrits"), style=wx.RB_GROUP)
        self.radio_presents = wx.RadioButton(self, -1, _(u"Présents sur une période"))

        self.staticbox_date_staticbox = wx.StaticBox(self, -1, _(u"Période"))
        self.ctrl_calendrier = CTRL_Grille_periode.CTRL(self)
        self.ctrl_calendrier.SetMinSize((Style.px(280), Style.px(180)))

        self.staticbox_activites_staticbox = wx.StaticBox(self, -1, _(u"Activités"))
        self.ctrl_activites_presents = CTRL_Activites(self)
        self.ctrl_activites_inscrits = CTRL_Selection_activites.CTRL(self)
        self.ctrl_activites_presents.SetMinSize((Style.px(280), Style.hauteur_panneau("secondary")))
        self.ctrl_activites_inscrits.SetMinSize((Style.px(280), Style.hauteur_panneau("secondary")))

        self.staticbox_groupes_staticbox = wx.StaticBox(self, -1, _(u"Groupes"))
        self.ctrl_groupes = CTRL_Groupes(self)
        self.ctrl_groupes.SetMinSize((Style.px(280), Style.hauteur_panneau("secondary")))

        for box in (
            self.staticbox_mode_staticbox,
            self.staticbox_date_staticbox,
            self.staticbox_activites_staticbox,
            self.staticbox_groupes_staticbox,
        ):
            Style.appliquer_texte(box, role="label", role_texte="on_surface_variant", role_fond="surface")
        for radio in (self.radio_inscrits, self.radio_presents):
            Style.appliquer_texte(radio, role="body", role_texte="on_surface", role_fond="surface")

        self.radio_inscrits.SetToolTip(wx.ToolTip(_(u"Sélectionnez le mode de sélection des individus")))
        self.radio_presents.SetToolTip(wx.ToolTip(_(u"Sélectionnez le mode de sélection des individus")))

        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioMode, self.radio_inscrits)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioMode, self.radio_presents)

        self.__do_layout()

        self.ctrl_calendrier.SetVisibleSelection()
        self.SetListesPeriodes(self.ctrl_calendrier.GetDatesSelections())
        self.OnRadioMode()

    def __do_layout(self):
        marge = Style.espace(3)
        espace = Style.espace(3)
        interieur = Style.espace(2)

        mode = wx.StaticBoxSizer(self.staticbox_mode_staticbox, wx.VERTICAL)
        modes = wx.BoxSizer(wx.HORIZONTAL)
        modes.Add(self.radio_inscrits, 0, wx.ALIGN_CENTER_VERTICAL)
        modes.AddSpacer(espace)
        modes.Add(self.radio_presents, 0, wx.ALIGN_CENTER_VERTICAL)
        mode.Add(modes, 0, wx.ALL | wx.EXPAND, interieur)

        periode = wx.StaticBoxSizer(self.staticbox_date_staticbox, wx.VERTICAL)
        periode.Add(self.ctrl_calendrier, 1, wx.ALL | wx.EXPAND, interieur)

        gauche = wx.BoxSizer(wx.VERTICAL)
        gauche.Add(mode, 0, wx.EXPAND)
        gauche.AddSpacer(espace)
        gauche.Add(periode, 1, wx.EXPAND)

        activites = wx.StaticBoxSizer(self.staticbox_activites_staticbox, wx.VERTICAL)
        activites.Add(self.ctrl_activites_presents, 1, wx.ALL | wx.EXPAND, interieur)
        activites.Add(self.ctrl_activites_inscrits, 1, wx.ALL | wx.EXPAND, interieur)

        groupes = wx.StaticBoxSizer(self.staticbox_groupes_staticbox, wx.VERTICAL)
        groupes.Add(self.ctrl_groupes, 1, wx.ALL | wx.EXPAND, interieur)

        droite = wx.BoxSizer(wx.VERTICAL)
        droite.Add(activites, 1, wx.EXPAND)
        droite.AddSpacer(espace)
        droite.Add(groupes, 1, wx.EXPAND)

        colonnes = wx.BoxSizer(wx.HORIZONTAL)
        colonnes.Add(gauche, 0, wx.EXPAND)
        colonnes.AddSpacer(espace)
        colonnes.Add(droite, 1, wx.EXPAND)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(colonnes, 1, wx.ALL | wx.EXPAND, marge)
        self.SetSizer(principal)
        self.grid_sizer_base = principal
        self.SetMinSize((Style.px(680), Style.px(440)))
        self.Layout()

    def OnRadioMode(self, event=None):
        mode_inscrits = self.radio_inscrits.GetValue()
        self.ctrl_activites_inscrits.Show(mode_inscrits)
        self.ctrl_activites_presents.Show(not mode_inscrits)
        self.staticbox_date_staticbox.Enable(not mode_inscrits)
        self.ctrl_calendrier.Enable(not mode_inscrits)
        self.Layout()
        try:
            self.GetParent().Layout()
        except Exception:
            pass
        self.OnCheckActivites()

    def OnCheckActivites(self):
        if self.radio_inscrits.GetValue() is True:
            listeSelections = self.ctrl_activites_inscrits.GetActivites()
            self.SetGroupes(listeSelections)
        if self.radio_presents.GetValue() is True:
            listeSelections = self.ctrl_activites_presents.GetIDcoches()
            self.SetGroupes(listeSelections)

    def SetListesPeriodes(self, listePeriodes=[]):
        self.ctrl_activites_presents.SetPeriodes(listePeriodes)
        self.SetGroupes(self.ctrl_activites_presents.GetListeActivites())

    def SetGroupes(self, listeActivites=[]):
        self.ctrl_groupes.SetActivites(listeActivites)

    def SetModePresents(self, etat=True):
        self.radio_presents.SetValue(etat)
        self.OnRadioMode()

    def GetParametres(self):
        dictParametres = {}
        dictParametres["liste_periodes"] = self.ctrl_calendrier.GetDatesSelections()
        dictParametres["impression_infos_med_mode_presents"] = self.radio_presents.GetValue()

        if self.radio_inscrits.GetValue() is True:
            dictParametres["mode"] = "inscrits"
            dictParametres["liste_activites"] = self.ctrl_activites_inscrits.GetActivites()
            dictParametres["dict_activites"] = self.ctrl_activites_inscrits.GetDictActivites()

        if self.radio_presents.GetValue() is True:
            dictParametres["mode"] = "presents"
            dictParametres["liste_activites"] = self.ctrl_activites_presents.GetListeActivites()
            dictParametres["dict_activites"] = self.ctrl_activites_presents.GetDictActivites()

        dictParametres["liste_groupes"] = self.ctrl_groupes.GetListeGroupes()
        dictParametres["dict_groupes"] = self.ctrl_groupes.GetDictGroupes()
        return dictParametres

    def SetParametres(self, dictParametres={}):
        pass


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(panel, "surface")
        self.ctrl = CTRL(panel)
        bouton_test = CTRL_ActionRepens.CTRL(panel, label=u"Test", variante="secondaire")
        contenu = wx.BoxSizer(wx.VERTICAL)
        contenu.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, Style.espace(2))
        contenu.Add(bouton_test, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, Style.espace(2))
        panel.SetSizer(contenu)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(panel, 1, wx.EXPAND)
        self.SetSizer(principal)
        self.SetMinSize((Style.px(700), Style.px(520)))
        self.Layout()
        self.CentreOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnBouton, bouton_test)

    def OnBouton(self, event):
        print("ok")


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 600))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
