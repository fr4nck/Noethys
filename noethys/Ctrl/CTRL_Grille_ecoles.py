#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteurs:         Ivan LUCAS, Cliss XXI
# Copyright:       (c) 2010-11 Ivan LUCAS
#                  (c) 2017 Cliss XXI
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import datetime

import wx
import wx.lib.agw.hypertreelist as HTL
from wx.lib.agw.customtreectrl import EVT_TREE_ITEM_CHECKED, EVT_TREE_ITEM_RIGHT_CLICK

import Chemins
import GestionDB
from Utils import UTILS_Adaptations
from Utils import UTILS_Dates
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _


class CTRL(HTL.HyperTreeList):
    """Sélection des écoles/classes affichées dans les grilles métier."""

    def __init__(self, parent):
        HTL.HyperTreeList.__init__(self, parent, -1)
        self.parent = parent
        self.date = None
        self.dictEcoles = {}
        self.MAJenCours = False
        self.cocherParDefaut = True
        self.cocheInconnue = True
        self.cochesActives = {}
        self.cochesEcolesActives = set()
        self._resize_pending = False

        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
        self.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        try:
            main = self.GetMainWindow()
            main.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
            main.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        except Exception:
            pass
        try:
            police = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
            facteur = UTILS_Interface.GetTailleTexte() / 100.0
            police.SetPointSize(max(8, int(round(police.GetPointSize() * facteur))))
            self.SetFont(police)
            self.GetMainWindow().SetFont(police)
        except Exception:
            pass

        self.SetAGWWindowStyleFlag(
            HTL.TR_NO_HEADER | wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS |
            wx.TR_HAS_VARIABLE_ROW_HEIGHT | wx.TR_FULL_ROW_HIGHLIGHT
        )
        self.EnableSelectionVista(True)
        self.SetToolTip(wx.ToolTip(_(u"Cochez les écoles et classes à afficher. Clic droit pour tout cocher ou décocher.")))

        self.AddColumn(_(u"École / classe"))
        self.SetMinSize((UTILS_UIMetrics.px(300), UTILS_UIMetrics.px(220)))

        self.Bind(EVT_TREE_ITEM_CHECKED, self.OnCheckItem)
        self.Bind(EVT_TREE_ITEM_RIGHT_CLICK, self.OnContextMenu)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        wx.CallAfter(self._AjusterColonne)

    def _BitmapMenu(self, image):
        taille = UTILS_UIMetrics.icon_size("compact")
        chemin = Chemins.GetStaticIconPath(image, taille=taille)
        bitmap = wx.Bitmap(chemin, wx.BITMAP_TYPE_ANY)
        if bitmap.IsOk() and (bitmap.GetWidth() != taille or bitmap.GetHeight() != taille):
            bitmap = wx.Bitmap(bitmap.ConvertToImage().Scale(taille, taille, wx.IMAGE_QUALITY_HIGH))
        return bitmap

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
            self.SetColumnWidth(0, max(UTILS_UIMetrics.px(280), largeur - UTILS_UIMetrics.spacing(2)))
        except Exception:
            pass

    def SetDate(self, date=None):
        self.date = date
        self.MAJ()

    def SetCocherParDefaut(self, etat=True):
        self.cocherParDefaut = etat

    def OnCheckItem(self, event):
        if self.MAJenCours is False:
            item = event.GetItem()
            data = self.GetPyData(item)
            if data["type"] == "ecole":
                if self.IsItemChecked(item):
                    self.EnableChildren(item, True)
                    self.cochesEcolesActives.add(data["ID"])
                else:
                    self.EnableChildren(item, False)
                    self.cochesEcolesActives.discard(data["ID"])
            elif data["type"] == "classe":
                cochesGroupes = self.cochesActives[data["IDecole"]]
                if self.IsItemChecked(item):
                    cochesGroupes.add(data["ID"])
                else:
                    cochesGroupes.discard(data["ID"])
            else:
                self.cocheInconnue = self.IsItemChecked(item)
            if hasattr(self.parent, "MAJecoles"):
                self.parent.MAJecoles()

    def OnContextMenu(self, event):
        menu = UTILS_Adaptations.Menu()
        self.ID_COCHER_TOUTES = wx.Window.NewControlId()
        self.ID_COCHER_AUCUNE = wx.Window.NewControlId()

        item = wx.MenuItem(menu, self.ID_COCHER_TOUTES, _(u"Tout cocher"), _(u"Cocher toutes les écoles et classes"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Cocher.png"))
        menu.AppendItem(item)

        item = wx.MenuItem(menu, self.ID_COCHER_AUCUNE, _(u"Tout décocher"), _(u"Décocher toutes les écoles et classes"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Decocher.png"))
        menu.AppendItem(item)

        self.Bind(wx.EVT_MENU, self.OnCocher, id=self.ID_COCHER_TOUTES)
        self.Bind(wx.EVT_MENU, self.OnCocher, id=self.ID_COCHER_AUCUNE)
        try:
            self.PopupMenu(menu, event.GetPoint())
        except Exception:
            self.PopupMenu(menu)
        menu.Destroy()

    def OnCocher(self, event):
        ID = event.GetId()
        if ID == self.ID_COCHER_TOUTES:
            self.CocheListeTout()
        elif ID == self.ID_COCHER_AUCUNE:
            self.CocheListeRien()
        else:
            return
        if hasattr(self.parent, "MAJecoles"):
            self.parent.MAJecoles()

    def Cocher(self, etat=True):
        self.MAJenCours = True
        item = self.root
        for _index in range(0, self.GetChildrenCount(self.root)):
            item = self.GetNext(item)
            self.CheckItem(item, etat)
        if etat:
            self.EnableChildren(self.root, True)
        self.MAJenCours = False

    def CocheListeTout(self):
        self.Cocher(True)
        self.cocheInconnue = True
        self.cochesEcolesActives = set(self.dictEcoles.keys())
        self.cochesActives = {
            ID: set(d["IDclasse"] for d in self.dictEcoles[ID]["classes"])
            for ID in self.cochesEcolesActives
        }

    def CocheListeRien(self):
        self.Cocher(False)
        self.cocheInconnue = False
        self.cochesEcolesActives.clear()
        self.cochesActives = {ID: set() for ID in self.dictEcoles.keys()}

    def MAJ(self):
        self.dictEcoles = self.Importation()
        self.MAJenCours = True
        self.DeleteAllItems()
        self.root = self.AddRoot(_(u"Racine"))
        self.Remplissage()
        self.MAJenCours = False
        wx.CallAfter(self._AjusterColonne)

    def Importation(self):
        dictEcoles = {}
        if not self.date:
            return dictEcoles

        DB = GestionDB.DB()
        req = """SELECT ecoles.IDecole, ecoles.nom,
        classes.IDclasse, classes.nom, classes.niveaux,
        classes.date_debut, classes.date_fin
        FROM scolarite
        LEFT JOIN ecoles ON ecoles.IDecole = scolarite.IDecole
        LEFT JOIN classes ON classes.IDclasse = scolarite.IDclasse
        WHERE scolarite.IDclasse IS NOT NULL
              AND scolarite.date_debut<='{0}' AND scolarite.date_fin>='{0}'
        GROUP BY scolarite.IDclasse, ecoles.IDecole;""".format(self.date)
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()

        for IDecole, nomEcole, IDclasse, nomClasse, niveaux, date_debut, date_fin in listeDonnees:
            if date_debut is not None:
                date_debut = UTILS_Dates.DateEngEnDateDD(date_debut)
            if date_fin is not None:
                date_fin = UTILS_Dates.DateEngEnDateDD(date_fin)
            if IDecole not in dictEcoles:
                dictEcoles[IDecole] = {"nom": nomEcole, "classes": []}
            dictEcoles[IDecole]["classes"].append({
                "IDclasse": IDclasse,
                "nom": nomClasse,
                "date_debut": date_debut,
                "date_fin": date_fin,
            })
        return dictEcoles

    def Remplissage(self):
        listeEcoles = sorted((dictEcole["nom"], IDecole) for IDecole, dictEcole in self.dictEcoles.items())

        for nomEcole, IDecole in listeEcoles:
            dictEcole = self.dictEcoles[IDecole]
            if IDecole not in self.cochesActives:
                if self.cocherParDefaut is True:
                    self.cochesEcolesActives.add(IDecole)
                    self.cochesActives[IDecole] = set(d["IDclasse"] for d in dictEcole["classes"])
                else:
                    self.cochesActives[IDecole] = set()

            niveauEcole = self.AppendItem(self.root, nomEcole, ct_type=1)
            self.SetPyData(niveauEcole, {"type": "ecole", "ID": IDecole, "nom": nomEcole})
            self.SetItemBold(niveauEcole, True)

            for dictClasse in dictEcole["classes"]:
                IDclasse = dictClasse["IDclasse"]
                nomClasse = dictClasse["nom"]
                label = _(u"{0} (du {1} au {2})").format(
                    nomClasse,
                    UTILS_Dates.DateEngFr(dictClasse["date_debut"]),
                    UTILS_Dates.DateEngFr(dictClasse["date_fin"]),
                )
                niveauClasse = self.AppendItem(niveauEcole, label, ct_type=1)
                self.SetPyData(niveauClasse, {
                    "type": "classe", "ID": IDclasse, "nom": nomClasse, "IDecole": IDecole,
                })
                if IDclasse in self.cochesActives[IDecole]:
                    self.CheckItem(niveauClasse)

            if IDecole in self.cochesEcolesActives:
                self.CheckItem(niveauEcole)
                self.EnableChildren(niveauEcole, True)
            else:
                self.EnableChildren(niveauEcole, False)

        item = self.AppendItem(self.root, _(u"Scolarité inconnue"), ct_type=1)
        self.SetPyData(item, {"type": "inconnu"})
        if self.cocheInconnue:
            self.CheckItem(item)
        self.ExpandAllChildren(self.root)

    def GetCoches(self, typeTemp="ecole"):
        listeCoches = []
        item = self.root
        for _index in range(0, self.GetChildrenCount(self.root)):
            item = self.GetNext(item)
            if self.IsItemChecked(item) and self.IsItemEnabled(item):
                data = self.GetPyData(item)
                if data["type"] == typeTemp:
                    listeCoches.append(data["ID"])
        return listeCoches

    def GetListeEcoles(self):
        return self.GetCoches(typeTemp="ecole")

    def GetListeClasses(self):
        return self.GetCoches(typeTemp="classe")

    def GetScolariteInconnue(self):
        item = self.GetLastChild(self.root)
        return self.IsItemChecked(item) and self.IsItemEnabled(item)

    def GetDictEcoles(self):
        return self.dictEcoles


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        self.ctrl = CTRL(panel)
        self.ctrl.MAJ()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(2))
        panel.SetSizer(sizer)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(panel, 1, wx.EXPAND)
        self.SetSizer(principal)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, _(u"TEST"), size=(800, 400))
    frame_1.ctrl.SetDate(datetime.datetime.now())
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
