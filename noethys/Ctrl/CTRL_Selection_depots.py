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

import GestionDB
from Utils.UTILS_Traduction import _
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics


def DateComplete(dateDD):
    """Transforme une date DD en date complète : ex. lundi 15 janvier 2008."""
    listeJours = (_(u"Lundi"), _(u"Mardi"), _(u"Mercredi"), _(u"Jeudi"), _(u"Vendredi"), _(u"Samedi"), _(u"Dimanche"))
    listeMois = (_(u"janvier"), _(u"février"), _(u"mars"), _(u"avril"), _(u"mai"), _(u"juin"), _(u"juillet"), _(u"août"), _(u"septembre"), _(u"octobre"), _(u"novembre"), _(u"décembre"))
    return listeJours[dateDD.weekday()] + " " + str(dateDD.day) + " " + listeMois[dateDD.month - 1] + " " + str(dateDD.year)


def DateEngEnDateDD(dateEng):
    return datetime.date.fromisoformat(dateEng[:10])


class CTRL(HTL.HyperTreeList):
    """Sélection hiérarchique des dépôts, responsive et compatible thèmes."""

    def __init__(self, parent):
        HTL.HyperTreeList.__init__(self, parent, -1)
        self.parent = parent
        self.MAJenCours = False
        self._noethys_resize_pending = False

        self.SetAGWWindowStyleFlag(
            HTL.TR_NO_HEADER
            | wx.TR_HIDE_ROOT
            | wx.TR_HAS_BUTTONS
            | wx.TR_HAS_VARIABLE_ROW_HEIGHT
            | wx.TR_FULL_ROW_HIGHLIGHT
            | HTL.TR_AUTO_CHECK_CHILD
            | HTL.TR_AUTO_CHECK_PARENT
        )
        self.EnableSelectionVista(True)
        self.SetToolTip(wx.ToolTip(_(u"Cochez les dépôts à afficher")))

        self.AddColumn(_(u"Dépôts"))
        self._AppliquerStyle()
        self.Bind(wx.EVT_SIZE, self.OnSize)
        wx.CallAfter(self._AjusterLargeur)

    def _AppliquerStyle(self):
        try:
            fond = UTILS_Interface.GetCouleurRole("surface_container_lowest")
            texte = UTILS_Interface.GetCouleurRole("on_surface")
            self.SetBackgroundColour(fond)
            self.SetForegroundColour(texte)
            try:
                main = self.GetMainWindow()
                main.SetBackgroundColour(fond)
                main.SetForegroundColour(texte)
            except Exception:
                pass
        except Exception:
            pass

        try:
            police = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
            facteur = UTILS_Interface.GetTailleTexte() / 100.0
            police.SetPointSize(max(8, int(round(police.GetPointSize() * facteur))))
            self.SetFont(police)
            try:
                self.GetMainWindow().SetFont(police)
            except Exception:
                pass
        except Exception:
            pass

        try:
            self.SetMinSize((UTILS_UIMetrics.px(240), UTILS_UIMetrics.panel_min_height("secondary")))
        except Exception:
            pass

    def OnSize(self, event):
        event.Skip()
        if self._noethys_resize_pending:
            return
        self._noethys_resize_pending = True
        wx.CallAfter(self._AjusterLargeur)

    def _AjusterLargeur(self):
        self._noethys_resize_pending = False
        try:
            largeur = self.GetClientSize().GetWidth()
            marge = UTILS_UIMetrics.spacing(2)
            self.SetColumnWidth(0, max(UTILS_UIMetrics.px(220), largeur - marge))
        except Exception:
            pass

    def OnCheckItem(self, event):
        if self.MAJenCours is False:
            item = event.GetItem()
            if self.GetPyData(item)["type"] == "annee":
                if self.IsItemChecked(item):
                    self.EnableChildren(item, True)
                    self.CheckChilds(item)
                else:
                    self.CheckChilds(item, False)
                    self.EnableChildren(item, False)

    def GetCoches(self):
        dictCoches = {}
        parent = self.root
        for _index in range(0, self.GetChildrenCount(self.root)):
            parent = self.GetNext(parent)
            annee = self.GetPyData(parent)["ID"]
            listeDepots = []
            item, cookie = self.GetFirstChild(parent)
            for _index in range(0, self.GetChildrenCount(parent)):
                if self.IsItemChecked(item):
                    IDdepot = self.GetPyData(item)["ID"]
                    listeDepots.append(IDdepot)
                item = self.GetNext(item)
            if len(listeDepots) > 0:
                dictCoches[annee] = listeDepots
        return dictCoches

    def GetDepots(self):
        dictCoches = self.GetCoches()
        listeDepots = []
        for _annee, listeDepotsTemp in dictCoches.items():
            for IDdepot in listeDepotsTemp:
                listeDepots.append(IDdepot)
        return listeDepots

    def MAJ(self):
        """Met à jour (redessine) tout le contrôle."""
        self.listeDepots = self.Importation()
        self.MAJenCours = True
        self.DeleteAllItems()
        self.root = self.AddRoot(_(u"Racine"))
        self.Remplissage()
        self.MAJenCours = False
        wx.CallAfter(self._AjusterLargeur)

    def Remplissage(self):
        dictDepots = {}
        for dictDepot in self.listeDepots:
            date = dictDepot["date"]
            annee = None if date is None else date.year
            if annee not in dictDepots:
                dictDepots[annee] = []
            dictDepots[annee].append(dictDepot)

        # Python 3 ne compare pas directement None et int : les dépôts sans
        # date restent groupés en fin de liste sans modifier la logique métier.
        listeAnnees = sorted(dictDepots.keys(), key=lambda annee: (annee is None, annee or 0))

        for annee in listeAnnees:
            label = _(u"Sans date de dépôt") if annee is None else str(annee)
            niveauAnnee = self.AppendItem(self.root, label, ct_type=1)
            self.SetPyData(niveauAnnee, {"type": "annee", "ID": annee, "label": label})
            self.SetItemBold(niveauAnnee, True)

            for dictDepot in dictDepots[annee]:
                if dictDepot["date"] is None:
                    dateStr = u""
                else:
                    dateStr = u"(%02d/%02d/%04d)" % (
                        dictDepot["date"].day,
                        dictDepot["date"].month,
                        dictDepot["date"].year,
                    )
                label = u"%s %s" % (dictDepot["nom"], dateStr)
                niveauDepot = self.AppendItem(niveauAnnee, label, ct_type=1)
                self.SetPyData(niveauDepot, {"type": "depot", "ID": dictDepot["IDdepot"], "label": label})

            if annee == datetime.date.today().year:
                self.Expand(niveauAnnee)

    def Importation(self):
        listeDepots = []
        DB = GestionDB.DB()
        req = """SELECT IDdepot, date, nom, verrouillage, IDcompte
        FROM depots
        ORDER BY date;"""
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        for IDdepot, date, nom, verrouillage, IDcompte in listeDonnees:
            if date is not None:
                date = DateEngEnDateDD(date)
            listeDepots.append({
                "IDdepot": IDdepot,
                "date": date,
                "nom": nom,
                "verrouillage": verrouillage,
                "IDcompte": IDcompte,
            })
        return listeDepots


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        self.ctrl = CTRL(panel)
        self.ctrl.MAJ()
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
