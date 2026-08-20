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

import Chemins
import GestionDB
from Utils import UTILS_Adaptations
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils import UTILS_Utilisateurs
from Utils.UTILS_Traduction import _


def DateEngEnDateDD(dateEng):
    return datetime.date.fromisoformat(dateEng[:10])


def DateEngFr(textDate):
    return str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])


class CTRL(HTL.HyperTreeList):
    """Arbre des classes scolaires, responsive et compatible thèmes."""

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_HAS_VARIABLE_ROW_HEIGHT,
                 modeSelection=False):
        HTL.HyperTreeList.__init__(self, parent, id, pos, size, style)
        self.parent = parent
        self.modeSelection = modeSelection
        self.IDecole = None
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

        self.dictNiveaux = self.ImportationNiveaux()

        taille_icone = UTILS_UIMetrics.icon_size("inline")
        il = wx.ImageList(taille_icone, taille_icone)
        self.img_ecole = il.Add(self._Bitmap("Images/16x16/Ecole.png", taille_icone))
        self.img_classe = il.Add(self._Bitmap("Images/16x16/Classe.png", taille_icone))
        self.AssignImageList(il)

        self.AddColumn(_(u"Saison / Classe"))
        self.AddColumn(_(u"Niveaux scolaires"))
        self.SetMainColumn(0)

        self.root = self.AddRoot(_(u"Classes"))
        self.SetPyData(self.root, {"type": "root", "ID": None})
        if 'phoenix' in wx.PlatformInfo:
            TR_COLUMN_LINES = HTL.TR_COLUMN_LINES
        else:
            TR_COLUMN_LINES = wx.TR_COLUMN_LINES
        self.SetAGWWindowStyleFlag(wx.TR_HIDE_ROOT | TR_COLUMN_LINES | wx.TR_HAS_BUTTONS | wx.TR_HAS_VARIABLE_ROW_HEIGHT)
        self.SetMinSize((UTILS_UIMetrics.px(320), UTILS_UIMetrics.px(220)))

        if self.modeSelection is False:
            self.Bind(wx.EVT_TREE_ITEM_RIGHT_CLICK, self.OnContextMenu)
            self.GetMainWindow().Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)
        else:
            self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelectItem)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        wx.CallAfter(self._AjusterColonnes)

    def _Bitmap(self, image, taille=None):
        if taille is None:
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
        wx.CallAfter(self._AjusterColonnes)

    def _AjusterColonnes(self):
        self._resize_pending = False
        try:
            largeur = self.GetClientSize().GetWidth()
            if largeur <= 0:
                return
            marge = UTILS_UIMetrics.spacing(3)
            disponible = max(UTILS_UIMetrics.px(300), largeur - marge)
            largeur_niveaux = max(UTILS_UIMetrics.px(130), int(disponible * 0.28))
            largeur_classe = max(UTILS_UIMetrics.px(220), disponible - largeur_niveaux)
            self.SetColumnWidth(0, largeur_classe)
            self.SetColumnWidth(1, largeur_niveaux)
        except Exception:
            pass

    def MAJ(self, IDecole=None, selection=None):
        self.IDecole = IDecole
        self.DeleteChildren(self.root)
        if self.IDecole is not None:
            self.CreationBranches()
            if selection is not None and selection in self.dictBranches:
                self.SelectItem(self.dictBranches[selection])
        wx.CallAfter(self._AjusterColonnes)

    def ImportationNiveaux(self):
        dictNiveaux = {}
        DB = GestionDB.DB()
        req = """SELECT IDniveau, ordre, nom, abrege
        FROM niveaux_scolaires
        ORDER BY ordre;"""
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        for IDniveau, ordre, nom, abrege in listeDonnees:
            dictNiveaux[IDniveau] = {"nom": nom, "abrege": abrege, "ordre": ordre}
        return dictNiveaux

    def CreationBranches(self):
        self.dictBranches = {}
        DB = GestionDB.DB()
        req = """SELECT IDclasse, nom, date_debut, date_fin, niveaux
        FROM classes
        WHERE IDecole=%d
        ORDER BY date_debut, nom;""" % self.IDecole
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()

        dictClasses = {}
        for IDclasse, nom, date_debut, date_fin, niveaux in listeDonnees:
            date_debut = DateEngEnDateDD(date_debut)
            date_fin = DateEngEnDateDD(date_fin)
            saison = (date_debut, date_fin)

            listeOrdresNiveaux = []
            txtNiveaux = u""
            if niveaux not in (None, "", " "):
                txtTemp = []
                for niveau in niveaux.split(";"):
                    IDniveau = int(niveau)
                    if IDniveau in self.dictNiveaux:
                        txtTemp.append(self.dictNiveaux[IDniveau]["abrege"])
                        listeOrdresNiveaux.append(self.dictNiveaux[IDniveau]["ordre"])
                txtNiveaux = ", ".join(txtTemp)

            dictClasses.setdefault(saison, []).append((listeOrdresNiveaux, nom, txtNiveaux, IDclasse))

        listeSaisons = sorted(dictClasses.keys())
        for indexSaison, saison in enumerate(listeSaisons, start=1):
            nomSaison = _(u"Du %s au %s") % (DateEngFr(str(saison[0])), DateEngFr(str(saison[1])))
            brancheSaison = self.AppendItem(self.root, nomSaison)
            self.SetPyData(brancheSaison, {"type": "saison", "ID": saison, "nom": nomSaison})
            self.SetItemBold(brancheSaison, True)

            listeClasses = dictClasses[saison]
            listeClasses.sort()
            for listeOrdresNiveaux, nomClasse, txtNiveaux, IDclasse in listeClasses:
                brancheClasse = self.AppendItem(brancheSaison, nomClasse, image=self.img_classe)
                self.SetPyData(brancheClasse, {"type": "classe", "ID": IDclasse, "nom": nomClasse})
                self.SetItemText(brancheClasse, txtNiveaux, 1)
                self.dictBranches[IDclasse] = brancheClasse

            if indexSaison == len(listeSaisons):
                self.Expand(brancheSaison)

    def _GetDonneesSelection(self):
        try:
            item = self.GetSelection()
            if not item:
                return None
            return self.GetMainWindow().GetItemPyData(item)
        except Exception:
            return None

    def OnLeftDClick(self, event):
        dictItem = self._GetDonneesSelection()
        if dictItem and dictItem["type"] == "classe":
            self.Modifier(dictItem["ID"])
        event.Skip()

    def OnContextMenu(self, event):
        dictItem = self._GetDonneesSelection() or {"type": "root", "ID": None}
        type_item = dictItem["type"]

        menuPop = UTILS_Adaptations.Menu()
        item_ajouter = wx.MenuItem(menuPop, 10, _(u"Ajouter"))
        item_ajouter.SetBitmap(self._Bitmap("Images/16x16/Ajouter.png"))
        menuPop.AppendItem(item_ajouter)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=10)

        if type_item == "classe":
            menuPop.AppendSeparator()
            item_modifier = wx.MenuItem(menuPop, 20, _(u"Modifier"))
            item_modifier.SetBitmap(self._Bitmap("Images/16x16/Modifier.png"))
            menuPop.AppendItem(item_modifier)
            self.Bind(wx.EVT_MENU, self.Modifier, id=20)

            item_supprimer = wx.MenuItem(menuPop, 30, _(u"Supprimer"))
            item_supprimer.SetBitmap(self._Bitmap("Images/16x16/Supprimer.png"))
            menuPop.AppendItem(item_supprimer)
            self.Bind(wx.EVT_MENU, self.Supprimer, id=30)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Ajouter(self, event=None):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_classes", "creer") is False:
            return
        from Dlg import DLG_Saisie_classe
        dlg = DLG_Saisie_classe.Dialog(self, IDecole=self.IDecole)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ(IDecole=self.IDecole, selection=dlg.GetIDclasse())
        dlg.Destroy()

    def Modifier(self, event=None):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_classes", "modifier") is False:
            return
        dictItem = self._GetDonneesSelection()
        if not dictItem or dictItem["type"] != "classe":
            dlg = wx.MessageDialog(self, _(u"Vous n'avez sélectionné aucune classe à modifier !"), _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        from Dlg import DLG_Saisie_classe
        dlg = DLG_Saisie_classe.Dialog(self, IDecole=self.IDecole, IDclasse=dictItem["ID"])
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ(IDecole=self.IDecole, selection=dlg.GetIDclasse())
        dlg.Destroy()

    def Supprimer(self, event=None):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_classes", "supprimer") is False:
            return
        dictItem = self._GetDonneesSelection()
        if not dictItem or dictItem["type"] != "classe":
            dlg = wx.MessageDialog(self, _(u"Vous n'avez sélectionné aucune classe à supprimer !"), _(u"Erreur"), wx.OK | wx.ICON_QUESTION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        IDclasse = dictItem["ID"]

        DB = GestionDB.DB()
        req = """SELECT COUNT(IDclasse)
        FROM scolarite
        WHERE IDclasse=%d;""" % IDclasse
        DB.ExecuterReq(req)
        nbre = int(DB.ResultatReq()[0][0])
        DB.Close()
        if nbre > 0:
            dlg = wx.MessageDialog(self, _(u"Cette classe a déjà été attribuée %d fois.\n\nVous ne pouvez donc pas la supprimer !") % nbre, _(u"Suppression impossible"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        dlg = wx.MessageDialog(self, _(u"Souhaitez-vous vraiment supprimer cette classe ?"), _(u"Suppression"), wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_EXCLAMATION)
        if dlg.ShowModal() == wx.ID_YES:
            DB = GestionDB.DB()
            DB.ReqDEL("classes", "IDclasse", IDclasse)
            DB.Close()
            self.MAJ(IDecole=self.IDecole)
        dlg.Destroy()

    def OnSelectItem(self, event=None):
        try:
            self.parent.OnChoixClasse()
        except Exception:
            pass

    def GetClasse(self):
        dictItem = self._GetDonneesSelection()
        if dictItem and dictItem["type"] == "classe":
            return dictItem["ID"]
        return None


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        self.myOlv = CTRL(panel)
        self.myOlv.MAJ(IDecole=2)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.myOlv, 1, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(2))
        panel.SetSizer(sizer)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(panel, 1, wx.EXPAND)
        self.SetSizer(principal)
        self.Layout()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
