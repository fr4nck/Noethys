#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-12 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import datetime

import wx
import wx.lib.agw.customtreectrl as CT

import Chemins
import GestionDB
from Ctrl.CTRL_Saisie_transport import DICT_CATEGORIES
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


class CTRL(CT.CustomTreeCtrl):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BORDER_THEME):
        CT.CustomTreeCtrl.__init__(self, parent, id, pos, size, style)
        self.parent = parent
        self.root = self.AddRoot(_(u"Transports"))
        self.listeBranches = []

        Style.appliquer_liste(self)
        self.SetAGWWindowStyleFlag(wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_HAS_VARIABLE_ROW_HEIGHT | CT.TR_AUTO_CHECK_PARENT | CT.TR_AUTO_CHECK_CHILD)
        self.EnableSelectionVista(True)

        # Les pictogrammes de catégories restent métier ; leur taille est
        # désormais issue du socle Repens.
        taille_icone = Style.taille_icone("inline")
        self.dictImages = {}
        il = wx.ImageList(taille_icone, taille_icone)
        for code, valeurs in DICT_CATEGORIES.items():
            chemin = Chemins.GetStaticIconPath('Images/16x16/%s.png' % valeurs["image"], taille=taille_icone)
            bitmap = wx.Bitmap(chemin, wx.BITMAP_TYPE_ANY)
            if bitmap.IsOk() and (bitmap.GetWidth() != taille_icone or bitmap.GetHeight() != taille_icone):
                bitmap = wx.Bitmap(bitmap.ConvertToImage().Scale(taille_icone, taille_icone, wx.IMAGE_QUALITY_HIGH))
            self.dictImages[code] = {"img": bitmap, "index": il.Add(bitmap)}
        self.AssignImageList(il)

        self.Bind(CT.EVT_TREE_ITEM_CHECKED, self.OnCheck)

    def MAJ(self, date_debut=None, date_fin=None, listeDates=[]):
        self.listeBranches = []
        self.DeleteAllItems()
        self.root = self.AddRoot(_(u"Objets"))

        if date_debut is not None and date_fin is not None:
            conditionDates = "(depart_date>='%s' AND depart_date<='%s') OR (arrivee_date>='%s' AND arrivee_date<='%s')" % (date_debut, date_fin, date_debut, date_fin)
        else:
            if len(listeDates) == 0:
                conditionDates = "depart_date='2999-01-01' "
            elif len(listeDates) == 1:
                conditionDates = "(depart_date='%s' OR arrivee_date='%s')" % (listeDates[0], listeDates[0])
            else:
                listeTmp = [str(dateTmp) for dateTmp in listeDates]
                conditionDates = "(depart_date IN %s OR arrivee_date IN %s)" % (str(tuple(listeTmp)), str(tuple(listeTmp)))

        DB = GestionDB.DB()

        req = """SELECT IDligne, categorie, nom
        FROM transports_lignes;"""
        DB.ExecuterReq(req)
        dictLignes = {IDligne: nom for IDligne, categorie, nom in DB.ResultatReq()}

        req = """SELECT IDarret, IDligne, nom
        FROM transports_arrets
        ORDER BY ordre;"""
        DB.ExecuterReq(req)
        dictArrets = {IDarret: {"IDligne": IDligne, "nom": nom} for IDarret, IDligne, nom in DB.ResultatReq()}

        req = """SELECT IDlieu, categorie, nom
        FROM transports_lieux;"""
        DB.ExecuterReq(req)
        dictLieux = {IDlieu: nom for IDlieu, categorie, nom in DB.ResultatReq()}

        req = """SELECT IDtransport, categorie, IDligne, depart_IDarret, depart_IDlieu, arrivee_IDarret, arrivee_IDlieu
        FROM transports
        WHERE %s;""" % conditionDates
        DB.ExecuterReq(req)
        listeValeurs = DB.ResultatReq()
        DB.Close()

        dictResultats = {}
        for IDtransport, categorie, IDligne, depart_IDarret, depart_IDlieu, arrivee_IDarret, arrivee_IDlieu in listeValeurs:
            typeTransports = DICT_CATEGORIES[categorie]["type"]
            if categorie not in dictResultats:
                dictResultats[categorie] = {"lignes": [], "arrets": [], "lieux": []}

            if typeTransports == "lignes":
                if IDligne not in dictResultats[categorie]["lignes"]:
                    dictResultats[categorie]["lignes"].append(IDligne)
                if depart_IDarret not in dictResultats[categorie]["arrets"]:
                    dictResultats[categorie]["arrets"].append(depart_IDarret)
                if arrivee_IDarret not in dictResultats[categorie]["arrets"]:
                    dictResultats[categorie]["arrets"].append(arrivee_IDarret)

            if typeTransports == "lieux":
                if depart_IDlieu not in dictResultats[categorie]["lieux"]:
                    dictResultats[categorie]["lieux"].append(depart_IDlieu)
                if arrivee_IDlieu not in dictResultats[categorie]["lieux"]:
                    dictResultats[categorie]["lieux"].append(arrivee_IDlieu)

        listeCategories = sorted(dictResultats.keys())

        for categorie in listeCategories:
            brancheCategorie = self.AppendItem(self.root, DICT_CATEGORIES[categorie]["label"], ct_type=1)
            self.SetPyData(brancheCategorie, {"categorie": "categories", "code": categorie})
            self.SetItemBold(brancheCategorie)
            self.SetItemImage(brancheCategorie, self.dictImages[categorie]["index"])
            brancheCategorie.Check()
            self.listeBranches.append(brancheCategorie)

            listeLignes = []
            for IDligne in dictResultats[categorie]["lignes"]:
                label = dictLignes.get(IDligne, _(u"Ligne inconnue"))
                listeLignes.append((label, IDligne))
            listeLignes.sort()

            for label, IDligne in listeLignes:
                brancheLigne = self.AppendItem(brancheCategorie, label, ct_type=1)
                self.SetPyData(brancheLigne, {"categorie": "lignes", "code": IDligne})
                brancheLigne.Check()
                self.listeBranches.append(brancheLigne)

                for IDarret in dictResultats[categorie]["arrets"]:
                    label = dictArrets.get(IDarret, {}).get("nom", _(u"Arrêt inconnu"))
                    if IDarret is None or (IDarret in dictArrets and dictArrets[IDarret]["IDligne"] == IDligne):
                        brancheArret = self.AppendItem(brancheLigne, label, ct_type=1)
                        self.SetPyData(brancheArret, {"categorie": "arrets", "code": IDarret})
                        brancheArret.Check()
                        self.listeBranches.append(brancheArret)

            listeLieux = []
            for IDlieu in dictResultats[categorie]["lieux"]:
                label = dictLieux.get(IDlieu, _(u"Lieu inconnu"))
                listeLieux.append((label, IDlieu))
            listeLieux.sort()

            for label, IDlieu in listeLieux:
                brancheLieu = self.AppendItem(brancheCategorie, label, ct_type=1)
                self.SetPyData(brancheLieu, {"categorie": "lieux", "code": IDlieu})
                brancheLieu.Check()
                self.listeBranches.append(brancheLieu)

        self.ExpandAll()

    def OnCheck(self, event):
        try:
            self.parent.OnCocheFiltres()
        except Exception:
            pass
        event.Skip()

    def GetCoches(self):
        """Obtient la liste des éléments cochés."""
        dictCoches = {}
        for branche in self.listeBranches:
            if self.IsItemChecked(branche) is True:
                data = self.GetPyData(branche)
                dictCoches.setdefault(data["categorie"], []).append(data["code"])
        return dictCoches

    def Coche(self, etat=True):
        """Coche tout ou rien."""
        for branche in self.listeBranches:
            self.CheckItem(branche, etat)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        Style.appliquer_fenetre(panel, "surface")
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(panel, 1, wx.EXPAND)
        self.SetSizer(principal)

        self.myOlv = CTRL(panel)
        self.myOlv.MAJ(date_debut=datetime.date(2012, 3, 4), date_fin=datetime.date(2012, 5, 22))

        contenu = wx.BoxSizer(wx.VERTICAL)
        contenu.Add(self.myOlv, 1, wx.ALL | wx.EXPAND, Style.espace(1))
        panel.SetSizer(contenu)
        self.SetSize((900, 500))
        self.Layout()
        self.CenterOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
