#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import wx
import wx.lib.agw.customtreectrl as CT

import Chemins
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


class CTRL_Objets(CT.CustomTreeCtrl):
    def __init__(self, parent, liste_objets=[], id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BORDER_THEME):
        CT.CustomTreeCtrl.__init__(self, parent, id, pos, size, style)
        self.parent = parent
        self.liste_objets = liste_objets
        self.root = self.AddRoot(_(u"Objets"))

        Style.appliquer_liste(self)
        self.SetAGWWindowStyleFlag(wx.TR_HIDE_ROOT | wx.TR_HAS_VARIABLE_ROW_HEIGHT | CT.TR_AUTO_CHECK_PARENT | CT.TR_AUTO_CHECK_CHILD)
        self.EnableSelectionVista(True)

        # Ces pictogrammes décrivent la nature métier de l'objet statistique :
        # on les conserve, mais leur taille suit le socle Repens.
        taille_icone = Style.taille_icone("inline")
        chemins = {
            "rubrique": "Images/16x16/Rubrique.png",
            "page": "Images/16x16/Page.png",
            "texte": "Images/16x16/Texte2.png",
            "tableau": "Images/16x16/Tableau.png",
            "graphe": "Images/16x16/Barres2.png",
        }
        self.dictImages = {}
        il = wx.ImageList(taille_icone, taille_icone)
        for code, chemin in chemins.items():
            bitmap = wx.Bitmap(Chemins.GetStaticIconPath(chemin, taille=taille_icone), wx.BITMAP_TYPE_ANY)
            if bitmap.IsOk() and (bitmap.GetWidth() != taille_icone or bitmap.GetHeight() != taille_icone):
                bitmap = wx.Bitmap(bitmap.ConvertToImage().Scale(taille_icone, taille_icone, wx.IMAGE_QUALITY_HIGH))
            self.dictImages[code] = {"img": bitmap, "index": il.Add(bitmap)}
        self.AssignImageList(il)

        self.Bind(CT.EVT_TREE_ITEM_CHECKED, self.OnCheck)

    def MAJ(self):
        self.DeleteAllItems()
        self.root = self.AddRoot(_(u"Objets"))

        for dictRubrique in self.liste_objets:
            brancheRubrique = self.AppendItem(self.root, dictRubrique["nom"], ct_type=1)
            self.SetPyData(brancheRubrique, {"categorie": "rubrique", "code": dictRubrique["code"]})
            self.SetItemBold(brancheRubrique)
            self.SetItemImage(brancheRubrique, self.dictImages["rubrique"]["index"])
            if dictRubrique["visible"] is True:
                brancheRubrique.Check()

            for dictPage in dictRubrique["pages"]:
                branchePage = self.AppendItem(brancheRubrique, dictPage["nom"], ct_type=1)
                self.SetPyData(branchePage, {"categorie": "page", "code": dictPage["code"]})
                self.SetItemImage(branchePage, self.dictImages["page"]["index"])
                if dictPage["visible"] is True:
                    branchePage.Check()

                for objet in dictPage["objets"]:
                    nomObjet = objet.nom.replace("<BR>", "")
                    brancheObjet = self.AppendItem(branchePage, nomObjet, ct_type=1)
                    self.SetItemFont(brancheObjet, Style.police("caption"))
                    self.SetPyData(brancheObjet, {"categorie": "objet", "code": objet.code})
                    self.SetItemImage(brancheObjet, self.dictImages[objet.categorie]["index"])
                    if objet.visible is True:
                        brancheObjet.Check()

        self.ExpandAll()

    def OnCheck(self, event):
        # L'état est directement porté par l'arbre ; aucun état parallèle à maintenir.
        event.Skip()

    def GetCoches(self):
        """Obtient la liste des éléments cochés."""
        listeCodes = []

        def hasEnfantsCoches(branche):
            hasCoches = False
            brancheEnfant = self.GetFirstChild(branche)[0]
            for indexTemp in range(self.GetChildrenCount(branche, recursively=False)):
                if self.IsItemChecked(brancheEnfant):
                    hasCoches = True
                brancheEnfant = self.GetNextChild(branche, indexTemp + 1)[0]
            return hasCoches

        brancheRubrique = self.GetFirstChild(self.root)[0]
        for index1 in range(self.GetChildrenCount(self.root, recursively=False)):
            if self.IsItemChecked(brancheRubrique) and hasEnfantsCoches(brancheRubrique):
                code = self.GetItemPyData(brancheRubrique)["code"]
                listeCodes.append(code)

                branchePage = self.GetFirstChild(brancheRubrique)[0]
                for index2 in range(self.GetChildrenCount(brancheRubrique, recursively=False)):
                    if self.IsItemChecked(branchePage) and hasEnfantsCoches(branchePage):
                        code = self.GetItemPyData(branchePage)["code"]
                        listeCodes.append(code)

                        brancheObjet = self.GetFirstChild(branchePage)[0]
                        for index3 in range(self.GetChildrenCount(branchePage, recursively=False)):
                            if self.IsItemChecked(brancheObjet):
                                code = self.GetItemPyData(brancheObjet)["code"]
                                listeCodes.append(code)
                            brancheObjet = self.GetNextChild(branchePage, index3 + 1)[0]
                    branchePage = self.GetNextChild(brancheRubrique, index2 + 1)[0]
            brancheRubrique = self.GetNextChild(self.root, index1 + 1)[0]

        return listeCodes

    def Coche(self, etat=True):
        brancheRubrique = self.GetFirstChild(self.root)[0]
        for index1 in range(self.GetChildrenCount(self.root, recursively=False)):
            self.CheckItem(brancheRubrique, etat)

            branchePage = self.GetFirstChild(brancheRubrique)[0]
            for index2 in range(self.GetChildrenCount(brancheRubrique, recursively=False)):
                self.CheckItem(branchePage, etat)

                brancheObjet = self.GetFirstChild(branchePage)[0]
                for index3 in range(self.GetChildrenCount(branchePage, recursively=False)):
                    self.CheckItem(brancheObjet, etat)
                    brancheObjet = self.GetNextChild(branchePage, index3 + 1)[0]
                branchePage = self.GetNextChild(brancheRubrique, index2 + 1)[0]
            brancheRubrique = self.GetNextChild(self.root, index1 + 1)[0]


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        Style.appliquer_fenetre(panel, "surface")
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(panel, 1, wx.EXPAND)
        self.SetSizer(principal)

        from Dlg.DLG_Stats import LISTE_OBJETS as liste_objets
        self.myOlv = CTRL_Objets(panel, liste_objets=liste_objets)
        self.myOlv.MAJ()

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
