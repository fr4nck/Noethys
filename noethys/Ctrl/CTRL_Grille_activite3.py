#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import datetime

import wx
import wx.lib.agw.hypertreelist as HTL
from wx.lib.agw.customtreectrl import EVT_TREE_ITEM_CHECKED

import GestionDB
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


def DateComplete(dateDD):
    """Transforme une date DD en date complète : Ex : lundi 15 janvier 2008."""
    listeJours = (
        _(u"Lundi"), _(u"Mardi"), _(u"Mercredi"), _(u"Jeudi"),
        _(u"Vendredi"), _(u"Samedi"), _(u"Dimanche"),
    )
    listeMois = (
        _(u"janvier"), _(u"février"), _(u"mars"), _(u"avril"), _(u"mai"),
        _(u"juin"), _(u"juillet"), _(u"août"), _(u"septembre"),
        _(u"octobre"), _(u"novembre"), _(u"décembre"),
    )
    return u"{0} {1} {2} {3}".format(
        listeJours[dateDD.weekday()], str(dateDD.day),
        listeMois[dateDD.month - 1], str(dateDD.year),
    )


def DateEngEnDateDD(dateEng):
    return datetime.date.fromisoformat(dateEng[:10])


class CTRL_archive(wx.CheckListBox):
    """Ancien sélecteur plat conservé pour compatibilité."""

    def __init__(self, parent):
        wx.CheckListBox.__init__(self, parent, -1)
        self.parent = parent
        self.data = []
        self.date = None
        self.SetToolTip(wx.ToolTip(_(u"Cochez les activités à afficher")))
        self.listeActivites = []
        self.dictActivites = {}
        Style.appliquer_liste(self)
        self.SetMinSize((Style.px(220), Style.px(160)))
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheck)

    def SetDate(self, date=None):
        self.date = date
        self.MAJ()
        self.CocheTout()

    def MAJ(self):
        self.listeActivites, self.dictActivites = self.Importation()
        self.SetListeChoix()

    def Importation(self):
        listeActivites = []
        dictActivites = {}
        if self.date is None:
            return listeActivites, dictActivites
        DB = GestionDB.DB()
        req = """SELECT activites.IDactivite, nom, abrege, date_debut, date_fin
        FROM activites
        LEFT JOIN ouvertures ON ouvertures.IDactivite = activites.IDactivite
        WHERE ouvertures.date='%s'
        GROUP BY activites.IDactivite
        ORDER BY nom;""" % str(self.date)
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        for IDactivite, nom, abrege, date_debut, date_fin in listeDonnees:
            if date_debut is not None:
                date_debut = DateEngEnDateDD(date_debut)
            if date_fin is not None:
                date_fin = DateEngEnDateDD(date_fin)
            dictActivites[IDactivite] = {
                "nom": nom,
                "abrege": abrege,
                "date_debut": date_debut,
                "date_fin": date_fin,
                "tarifs": {},
            }
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
            if self.listeActivites[index][1] in listeIDcoches:
                self.Check(index)

    def OnCheck(self, event):
        listeSelections = self.GetIDcoches()
        try:
            self.parent.SetActivites(listeSelections)
        except Exception:
            print(listeSelections)

    def GetListeActivites(self):
        return self.GetIDcoches()


class CTRL(HTL.HyperTreeList):
    """Sélection des activités et groupes affichés dans les grilles métier."""

    def __init__(self, parent):
        HTL.HyperTreeList.__init__(self, parent, -1)
        self.parent = parent
        self.date = datetime.date(2014, 1, 10)
        self.liste_activites = []
        self.MAJenCours = False
        self.cocherParDefaut = True
        self.cochesActives = {}
        self.cochesActivitesActives = set()
        self._resize_pending = False

        Style.appliquer_liste(self)
        try:
            Style.appliquer_liste(self.GetMainWindow())
        except Exception:
            pass

        self.SetAGWWindowStyleFlag(
            HTL.TR_NO_HEADER | wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS |
            wx.TR_HAS_VARIABLE_ROW_HEIGHT | wx.TR_FULL_ROW_HIGHLIGHT
        )
        self.EnableSelectionVista(True)
        self.SetToolTip(wx.ToolTip(_(u"Cochez les activités et groupes à afficher")))

        self.AddColumn(_(u"Activité/groupe"))
        self.SetMinSize((Style.px(220), Style.px(180)))

        self.Bind(EVT_TREE_ITEM_CHECKED, self.OnCheckItem)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        wx.CallAfter(self._AjusterColonne)

    def OnSize(self, event):
        event.Skip()
        if self._resize_pending:
            return
        self._resize_pending = True
        wx.CallAfter(self._AjusterColonne)

    def _AjusterColonne(self):
        self._resize_pending = False
        try:
            largeur = self.GetClientSize().GetWidth()
            self.SetColumnWidth(0, max(Style.px(185), largeur - Style.espace(2)))
        except Exception:
            pass

    def SetDate(self, date=None):
        self.date = date
        self.MAJ()

    def OnCheckItem(self, event):
        if self.MAJenCours is False:
            item = event.GetItem()
            data = self.GetPyData(item)
            if data["type"] == "activite":
                if self.IsItemChecked(item):
                    self.EnableChildren(item, True)
                    self.cochesActivitesActives.add(data["ID"])
                else:
                    self.EnableChildren(item, False)
                    self.cochesActivitesActives.discard(data["ID"])
            else:
                cochesGroupes = self.cochesActives[data["IDactivite"]]
                if self.IsItemChecked(item):
                    cochesGroupes.add(data["ID"])
                else:
                    cochesGroupes.discard(data["ID"])
            self.parent.MAJactivites()

    def GetCoches(self):
        dictCoches = {}
        parent = self.root
        for _index in range(0, self.GetChildrenCount(self.root)):
            parent = self.GetNext(parent)
            if self.IsItemChecked(parent):
                IDactivite = self.GetPyData(parent)["ID"]
                listeGroupes = []
                item, _cookie = self.GetFirstChild(parent)
                for _indexGroupe in range(0, self.GetChildrenCount(parent)):
                    if self.IsItemChecked(item):
                        listeGroupes.append(self.GetPyData(item)["ID"])
                    item = self.GetNext(item)
                if len(listeGroupes) > 0:
                    dictCoches[IDactivite] = listeGroupes
        return dictCoches

    def GetActivitesEtGroupes(self):
        dictCoches = self.GetCoches()
        listeActivites = []
        listeGroupes = []
        for IDactivite, listeGroupesTemp in dictCoches.items():
            listeActivites.append(IDactivite)
            listeGroupes.extend(listeGroupesTemp)
        return listeActivites, listeGroupes

    def SetCocherParDefaut(self, etat=True):
        self.cocherParDefaut = etat

    def MAJ(self):
        self.dictActivites = self.Importation()
        self.MAJenCours = True
        self.DeleteAllItems()
        self.root = self.AddRoot(_(u"Racine"))
        self.Remplissage()
        self.MAJenCours = False
        wx.CallAfter(self._AjusterColonne)

    def Remplissage(self):
        listeActivites = sorted(
            (dictActivite["nom"], IDactivite)
            for IDactivite, dictActivite in self.dictActivites.items()
        )

        for nomActivite, IDactivite in listeActivites:
            dictActivite = self.dictActivites[IDactivite]

            if IDactivite not in self.cochesActives:
                if self.cocherParDefaut is True:
                    self.cochesActivitesActives.add(IDactivite)
                    self.cochesActives[IDactivite] = set(
                        d["IDgroupe"] for d in dictActivite["groupes"]
                    )
                else:
                    self.cochesActives[IDactivite] = set()

            niveauActivite = self.AppendItem(self.root, nomActivite, ct_type=1)
            self.SetPyData(niveauActivite, {
                "type": "activite",
                "ID": IDactivite,
                "nom": nomActivite,
            })
            self.SetItemBold(niveauActivite, True)

            for dictGroupe in dictActivite["groupes"]:
                IDgroupe = dictGroupe["IDgroupe"]
                niveauGroupe = self.AppendItem(niveauActivite, dictGroupe["nom"], ct_type=1)
                self.SetPyData(niveauGroupe, {
                    "type": "groupe",
                    "ID": IDgroupe,
                    "nom": dictGroupe["nom"],
                    "IDactivite": IDactivite,
                })
                if IDgroupe in self.cochesActives[IDactivite]:
                    self.CheckItem(niveauGroupe)

            if IDactivite in self.cochesActivitesActives:
                self.CheckItem(niveauActivite)
                self.EnableChildren(niveauActivite, True)
            else:
                self.EnableChildren(niveauActivite, False)

        self.ExpandAllChildren(self.root)

    def Importation(self):
        dictActivites = {}
        if self.date is None:
            return dictActivites
        DB = GestionDB.DB()
        req = """SELECT
        activites.IDactivite, activites.nom, activites.abrege,
        date_debut, date_fin,
        groupes.IDgroupe, groupes.nom
        FROM activites
        LEFT JOIN ouvertures ON ouvertures.IDactivite = activites.IDactivite
        LEFT JOIN groupes ON groupes.IDgroupe = ouvertures.IDgroupe
        WHERE ouvertures.date='%s'
        GROUP BY groupes.IDgroupe, activites.IDactivite
        ORDER BY groupes.ordre;""" % str(self.date)
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        for IDactivite, nom, abrege, date_debut, date_fin, IDgroupe, nomGroupe in listeDonnees:
            if IDgroupe is not None:
                if date_debut is not None:
                    date_debut = DateEngEnDateDD(date_debut)
                if date_fin is not None:
                    date_fin = DateEngEnDateDD(date_fin)
                if IDactivite not in dictActivites:
                    dictActivites[IDactivite] = {
                        "nom": nom,
                        "abrege": abrege,
                        "date_debut": date_debut,
                        "date_fin": date_fin,
                        "groupes": [],
                    }
                dictActivites[IDactivite]["groupes"].append({
                    "IDgroupe": IDgroupe,
                    "nom": nomGroupe,
                })
        return dictActivites


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        Style.appliquer_fenetre(self, "surface")
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(panel, "surface")
        self.ctrl = CTRL(panel)
        self.ctrl.MAJ()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, Style.espace(2))
        panel.SetSizer(sizer)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(panel, 1, wx.EXPAND)
        self.SetSizer(principal)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, _(u"TEST"), size=(Style.px(800), Style.px(400)))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
