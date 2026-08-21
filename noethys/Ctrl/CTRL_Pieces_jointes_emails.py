#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-12 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import os

import wx

import Chemins
from Utils import UTILS_Adaptations
from Utils import UTILS_IconesRepens
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _

if wx.VERSION < (2, 9, 0, 0):
    from Outils import ultimatelistctrl as ULC
else:
    from wx.lib.agw import ultimatelistctrl as ULC


ID_AJOUTER = 10
ID_SUPPRIMER = 30


class CTRL(ULC.UltimateListCtrl):
    """Liste des pièces jointes avec icônes informatives et actions Repens."""

    def __init__(self, parent, listePieces=None):
        ULC.UltimateListCtrl.__init__(
            self,
            parent,
            -1,
            agwStyle=wx.LC_LIST | ULC.ULC_SINGLE_SEL,
        )
        self.parent = parent
        self.listePieces = listePieces or []
        self._taille_icone = UTILS_UIMetrics.icon_size("inline")

        try:
            self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
            self.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
            police = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
            facteur = UTILS_Interface.GetTailleTexte() / 100.0
            police.SetPointSize(max(8, int(round(police.GetPointSize() * facteur))))
            self.SetFont(police)
        except Exception:
            pass
        self.SetMinSize((UTILS_UIMetrics.px(260), UTILS_UIMetrics.panel_min_height("secondary")))
        self.SetToolTip(wx.ToolTip(_(u"Pièces jointes. Clic droit pour ajouter ou supprimer un fichier.")))

        # Les pictogrammes d'extension portent une information métier et sont
        # donc conservés ; seules les commandes passent au catalogue Repens.
        self.dictImages = {}
        il = wx.ImageList(self._taille_icone, self._taille_icone, True)
        listeExtensions = ["bmp", "doc", "docx", "gif", "jpeg", "jpg", "pdf", "png", "tous", "xls", "xlsx", "zip"]
        for extension in listeExtensions:
            chemin = Chemins.GetStaticIconPath("Images/16x16/Fichier_%s.png" % extension, taille=self._taille_icone)
            bitmap = wx.Bitmap(chemin, wx.BITMAP_TYPE_ANY)
            if bitmap.IsOk() and (bitmap.GetWidth() != self._taille_icone or bitmap.GetHeight() != self._taille_icone):
                image = bitmap.ConvertToImage().Scale(self._taille_icone, self._taille_icone, wx.IMAGE_QUALITY_HIGH)
                bitmap = wx.Bitmap(image)
            self.dictImages[extension] = il.Add(bitmap)
        self.AssignImageList(il, wx.IMAGE_LIST_SMALL)

        self.Bind(ULC.EVT_LIST_ITEM_RIGHT_CLICK, self.OnContextMenu)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnContextMenu)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_MENU, self.Ajouter, id=ID_AJOUTER)
        self.Bind(wx.EVT_MENU, self.Supprimer, id=ID_SUPPRIMER)
        self.MAJ()

    def MAJ(self):
        self.DeleteAllItems()
        for index, dictFichier in enumerate(self.listePieces):
            nomFichier = os.path.basename(dictFichier["nom"])
            extension = dictFichier["extension"]
            taille = dictFichier["taille"]
            obligatoire = dictFichier["obligatoire"]

            if taille is not None:
                if taille >= 1000000:
                    texteTaille = u"%.1f Mo" % (taille / 1000000.0)
                else:
                    texteTaille = u"%.0f Ko" % (taille / 1000.0)
                label = u"%s (%s)" % (nomFichier, texteTaille)
            else:
                label = nomFichier

            bmp = self.dictImages.get(extension, self.dictImages["tous"])
            self.InsertImageStringItem(index, label, bmp)
            self.SetItemData(index, dictFichier)

            if obligatoire is True:
                self.EnableItem(index, enable=False)
                self.SetItemTextColour(index, UTILS_Interface.GetCouleurRole("on_surface_variant"))

        try:
            if len(self.listePieces) > 0:
                self.parent.box_pieces_staticbox.SetLabel(_(u"Pièces jointes communes (%d)") % len(self.listePieces))
            else:
                self.parent.box_pieces_staticbox.SetLabel(_(u"Pièces jointes communes"))
        except Exception:
            pass

    def OnKeyDown(self, event):
        code = event.GetKeyCode()
        if code in (wx.WXK_DELETE, wx.WXK_BACK):
            self.Supprimer(None)
            return
        if code == wx.WXK_INSERT:
            self.Ajouter(None)
            return
        event.Skip()

    def _BitmapMenu(self, nom, role="on_surface"):
        try:
            bitmap = UTILS_IconesRepens.GetBitmap(
                nom,
                taille=UTILS_UIMetrics.icon_size("compact"),
                role=role,
            )
            if bitmap is not None and bitmap.IsOk():
                return bitmap
        except Exception:
            pass
        return wx.NullBitmap

    def OnContextMenu(self, event):
        try:
            point = (event.GetX(), event.GetY())
            item, flags = self.HitTest(point)
        except Exception:
            item, flags = wx.NOT_FOUND, 0

        if item != wx.NOT_FOUND and flags & wx.LIST_HITTEST_ONITEM:
            self.Select(item)
            noSelection = False
        else:
            noSelection = True
            self.ToutDeselectionner()

        menuPop = UTILS_Adaptations.Menu()
        item_ajouter = wx.MenuItem(menuPop, ID_AJOUTER, _(u"Ajouter une pièce jointe…"))
        bitmap = self._BitmapMenu("add")
        if bitmap.IsOk():
            item_ajouter.SetBitmap(bitmap)
        menuPop.AppendItem(item_ajouter)

        item_supprimer = wx.MenuItem(menuPop, ID_SUPPRIMER, _(u"Supprimer la pièce jointe"))
        bitmap = self._BitmapMenu("delete", role="danger_text")
        if bitmap.IsOk():
            item_supprimer.SetBitmap(bitmap)
        menuPop.AppendItem(item_supprimer)
        if noSelection is True:
            item_supprimer.Enable(False)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def ToutDeselectionner(self):
        index = self.GetFirstSelected()
        while index != -1:
            self.Select(index, False)
            index = self.GetNextSelected(index)

    def Ajouter(self, event):
        rep = wx.StandardPaths.Get().GetDocumentsDir()
        dlg = wx.FileDialog(
            self,
            message=_(u"Veuillez sélectionner le ou les fichiers à joindre"),
            defaultDir=rep,
            defaultFile="",
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST,
        )
        try:
            if dlg.ShowModal() != wx.ID_OK:
                return
            chemins = dlg.GetPaths()
        finally:
            dlg.Destroy()

        for fichier in chemins:
            valide = True
            for dictFichier in self.listePieces:
                if fichier == dictFichier["nom"]:
                    dlg = wx.MessageDialog(
                        self,
                        _(u"Le fichier '%s' est déjà dans la liste !") % os.path.basename(fichier),
                        _(u"Erreur"),
                        wx.OK | wx.ICON_EXCLAMATION,
                    )
                    dlg.ShowModal()
                    dlg.Destroy()
                    valide = False
                    break
            if valide is True:
                extension = fichier.split('.')[-1].lower()
                taille = os.path.getsize(fichier)
                self.listePieces.append({"nom": fichier, "extension": extension, "taille": taille, "obligatoire": False})
        self.MAJ()

    def Supprimer(self, event):
        if self.GetSelectedItemCount() == 0:
            if event is not None:
                dlg = wx.MessageDialog(
                    self,
                    _(u"Vous n'avez sélectionné aucune pièce jointe à enlever de la liste !"),
                    _(u"Erreur"),
                    wx.OK | wx.ICON_EXCLAMATION,
                )
                dlg.ShowModal()
                dlg.Destroy()
            return
        index = self.GetFirstSelected()
        if self.listePieces[index]["obligatoire"] is True:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous ne pouvez pas désélectionner cette pièce !"),
                _(u"Erreur"),
                wx.OK | wx.ICON_EXCLAMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return
        self.listePieces.pop(index)
        self.MAJ()

    def SetPieces(self, listePieces=None):
        self.listePieces = listePieces or []
        self.MAJ()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        listePieces = [{"nom": _(u"Facture"), "extension": "pdf", "taille": None, "obligatoire": True}]
        self.ctrl = CTRL(panel, listePieces=listePieces)
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
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
