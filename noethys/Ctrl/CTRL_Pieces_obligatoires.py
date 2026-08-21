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
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


def DateEngEnDateDD(dateEng):
    return datetime.date.fromisoformat(dateEng[:10])


def FormatDuree(duree):
    posM = duree.find("m")
    posA = duree.find("a")
    jours = int(duree[1:posM-1])
    mois = int(duree[posM+1:posA-1])
    annees = int(duree[posA+1:])
    return jours, mois, annees


def DateEngFr(textDate):
    text = str(textDate[8:10]) + "/" + str(textDate[5:7]) + "/" + str(textDate[:4])
    return text


class CTRL(HTL.HyperTreeList):
    def __init__(self, parent, IDfamille=None, IDindividu=None, dictFamillesRattachees={}, size=(-1, -1), largeurColonne=270):
        HTL.HyperTreeList.__init__(self, parent, -1, size=size)
        self.parent = parent
        self.IDfamille = IDfamille
        self.IDindividu = IDindividu
        self.dictFamillesRattachees = dictFamillesRattachees
        self.listePiecesObligatoires = []
        self.dictItems = {}

        self.AddColumn(_(u"Pièces à fournir"))
        self.SetColumnWidth(0, Style.px(largeurColonne))
        self.SetColumnAlignment(0, wx.ALIGN_LEFT)

        # Les trois pictogrammes conservent leur sens métier historique, mais
        # suivent désormais la taille d'icône commune et le DPI de Repens.
        taille_icone = Style.taille_icone("inline")
        il = wx.ImageList(taille_icone, taille_icone)
        self.img_ok = il.Add(wx.Bitmap(Chemins.GetStaticIconPath("Images/16x16/Ok.png", taille=taille_icone), wx.BITMAP_TYPE_ANY))
        self.img_attention = il.Add(wx.Bitmap(Chemins.GetStaticIconPath("Images/16x16/Attention.png", taille=taille_icone), wx.BITMAP_TYPE_ANY))
        self.img_pasok = il.Add(wx.Bitmap(Chemins.GetStaticIconPath("Images/16x16/Interdit.png", taille=taille_icone), wx.BITMAP_TYPE_ANY))
        self.AssignImageList(il)

        self.SetAGWWindowStyleFlag(wx.TR_HIDE_ROOT | wx.TR_NO_BUTTONS | wx.TR_HAS_VARIABLE_ROW_HEIGHT | HTL.TR_NO_HEADER)
        Style.appliquer_liste(self)

        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelection)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnDoubleClick)

    def OnSelection(self, event):
        item = event.GetItem()
        donnees = self.GetPyData(item)
        if self.GetParent().GetName() == "DLG_Saisie_piece":
            self.GetParent().OnSelectionPieceObligatoire(donnees)

    def OnDoubleClick(self, event):
        item = event.GetItem()
        donnees = self.GetPyData(item)
        if donnees is None:
            return
        if donnees["type"] != "piece":
            return
        if donnees["valide"] != "pasok":
            dlg = wx.MessageDialog(self, _(u"Une pièce valide existe déjà !"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False
        if self.GetParent().GetName() == "DLG_Individu_pieces" or self.GetParent().GetName() == "DLG_Famille_pieces":
            self.GetParent().OnAjoutExpress(donnees["IDfamille"], donnees["IDtype_piece"], donnees["IDindividu"])

    def MAJ(self):
        """Met à jour (redessine) tout le contrôle."""
        self.DeleteAllItems()
        self.Remplissage()

    def GetlistePiecesObligatoires(self):
        return self.listePiecesObligatoires

    def GetDonneesSelection(self):
        return self.GetPyData(self.GetSelection())

    def Remplissage(self):
        self.listePiecesObligatoires = []
        self.dictItems = {}

        condition = ""
        if self.IDfamille is not None:
            condition = "AND inscriptions.IDfamille=%d " % self.IDfamille
        if self.IDindividu is not None:
            condition = "AND inscriptions.IDindividu=%d " % self.IDindividu

        DB = GestionDB.DB()

        req = """
        SELECT
        inscriptions.IDfamille, pieces_activites.IDtype_piece, types_pieces.nom, types_pieces.public, types_pieces.valide_rattachement, individus.prenom, individus.IDindividu
        FROM pieces_activites
        LEFT JOIN types_pieces ON types_pieces.IDtype_piece = pieces_activites.IDtype_piece
        LEFT JOIN inscriptions ON inscriptions.IDactivite = pieces_activites.IDactivite
        LEFT JOIN individus ON individus.IDindividu = inscriptions.IDindividu
        LEFT JOIN activites ON activites.IDactivite = inscriptions.IDactivite
        WHERE inscriptions.statut='ok' AND activites.date_fin>='%s' %s
        GROUP BY inscriptions.IDfamille, pieces_activites.IDtype_piece, individus.IDindividu;
        """ % (datetime.date.today(), condition)
        DB.ExecuterReq(req)
        listePiecesObligatoires = DB.ResultatReq()

        dateDuJour = datetime.date.today()

        if self.IDindividu is not None:
            if self.dictFamillesRattachees is not None:
                listeIDfamille = []
                for IDfamille, dictFamille in self.dictFamillesRattachees.items():
                    if dictFamille["IDcategorie"] in (1, 2):
                        listeIDfamille.append(IDfamille)
                if len(listeIDfamille) == 0:
                    conditionIDfamille = "()"
                elif len(listeIDfamille) == 1:
                    conditionIDfamille = "(%d)" % listeIDfamille[0]
                else:
                    conditionIDfamille = str(tuple(listeIDfamille))
            else:
                conditionIDfamille = "()"
            req = """
            SELECT IDpiece, pieces.IDtype_piece, IDindividu, IDfamille, date_debut, date_fin, public
            FROM pieces
            LEFT JOIN types_pieces ON types_pieces.IDtype_piece = pieces.IDtype_piece
            WHERE date_debut <= '%s' AND date_fin >= '%s'
            AND (IDindividu=%d OR (IDfamille IN %s AND IDindividu IS NULL))
            ORDER BY date_fin
            ;""" % (str(dateDuJour), str(dateDuJour), self.IDindividu, conditionIDfamille)
        else:
            req = """
            SELECT IDindividu, IDcategorie
            FROM rattachements
            WHERE IDfamille=%d AND IDcategorie IN (1, 2);
            """ % self.IDfamille
            DB.ExecuterReq(req)
            listeDonnees = DB.ResultatReq()
            listeIDindividus = []
            for IDindividu, IDcategorie in listeDonnees:
                if IDindividu not in listeIDindividus:
                    listeIDindividus.append(IDindividu)
            if len(listeIDindividus) == 0:
                conditionIndividus = "()"
            elif len(listeIDindividus) == 1:
                conditionIndividus = "(%d)" % listeIDindividus[0]
            else:
                conditionIndividus = str(tuple(listeIDindividus))
            req = """
            SELECT IDpiece, pieces.IDtype_piece, IDindividu, IDfamille, date_debut, date_fin, public
            FROM pieces
            LEFT JOIN types_pieces ON types_pieces.IDtype_piece = pieces.IDtype_piece
            WHERE date_debut <= '%s' AND date_fin >= '%s'
            AND (IDfamille=%s OR (IDindividu IN %s AND IDfamille IS NULL))
            ORDER BY date_fin
            """ % (str(dateDuJour), str(dateDuJour), self.IDfamille, conditionIndividus)

        DB.ExecuterReq(req)
        listePiecesFournies = DB.ResultatReq()
        DB.Close()
        dictPiecesFournies = {}
        for IDpiece, IDtype_piece, IDindividu, IDfamille, date_debut, date_fin, publicPiece in listePiecesFournies:
            if publicPiece == "famille":
                IDindividu = None

            date_debut = DateEngEnDateDD(date_debut)
            date_fin = DateEngEnDateDD(date_fin)
            dictPiecesFournies[(IDfamille, IDtype_piece, IDindividu)] = (date_debut, date_fin)

        dictDonnees = {}
        for IDfamille, IDtype_piece, nomPiece, publicPiece, rattachementPiece, prenom, IDindividu in listePiecesObligatoires:
            if publicPiece == "famille":
                IDindividu = None
            if rattachementPiece == 1:
                IDfamille = None

            self.listePiecesObligatoires.append((IDfamille, IDtype_piece, IDindividu))

            if (IDfamille, IDtype_piece, IDindividu) in dictPiecesFournies:
                date_debut, date_fin = dictPiecesFournies[(IDfamille, IDtype_piece, IDindividu)]
                nbreJoursRestants = (date_fin - datetime.date.today()).days
                if nbreJoursRestants > 15:
                    valide = "ok"
                else:
                    valide = "attention"
            else:
                valide = "pasok"
            dictDonnees[(IDfamille, IDtype_piece, IDindividu)] = (IDfamille, IDtype_piece, nomPiece, publicPiece, prenom, IDindividu, valide)

        dictPieces = {}
        nbreFamilles = 0
        for key, valeurs in dictDonnees.items():
            IDfamille = valeurs[0]
            if IDfamille not in dictPieces:
                dictPieces[IDfamille] = []
                if IDfamille is not None:
                    nbreFamilles += 1
            dictPieces[IDfamille].append(valeurs)
            dictPieces[IDfamille].sort()

        self.root = self.AddRoot(_(u"Racine"))

        for IDfamille, valeurs in dictPieces.items():
            if nbreFamilles > 1:
                if IDfamille is None:
                    label = _(u"Pièces indépendantes")
                else:
                    if self.dictFamillesRattachees is not None and len(self.dictFamillesRattachees) > 0:
                        label = self.dictFamillesRattachees[IDfamille]["nomsTitulaires"]
                    else:
                        label = _(u"IDfamille=%d") % IDfamille
                niveau1 = self.AppendItem(self.root, label)
                self.SetPyData(niveau1, {"type": "famille", "IDfamille": IDfamille})
                self.SetItemBold(niveau1, True)
            else:
                niveau1 = self.root

            for IDfamille, IDtype_piece, nomPiece, publicPiece, prenom, IDindividu, valide in valeurs:
                if publicPiece == "famille" or self.IDindividu is not None:
                    label = nomPiece
                else:
                    label = _(u"%s de %s") % (nomPiece, prenom)
                niveau2 = self.AppendItem(niveau1, label)
                self.SetPyData(niveau2, {
                    "type": "piece",
                    "IDtype_piece": IDtype_piece,
                    "IDindividu": IDindividu,
                    "IDfamille": IDfamille,
                    "valide": valide,
                    "nomPiece": nomPiece,
                })
                self.dictItems[(IDfamille, IDtype_piece, IDindividu)] = niveau2
                if valide == "ok":
                    self.SetItemImage(niveau2, self.img_ok, which=wx.TreeItemIcon_Normal)
                if valide == "attention":
                    self.SetItemImage(niveau2, self.img_attention, which=wx.TreeItemIcon_Normal)
                if valide == "pasok":
                    self.SetItemImage(niveau2, self.img_pasok, which=wx.TreeItemIcon_Normal)

        if nbreFamilles < 2:
            self.SetAGWWindowStyleFlag(wx.TR_NO_LINES | wx.TR_HIDE_ROOT | wx.TR_NO_BUTTONS | wx.TR_HAS_VARIABLE_ROW_HEIGHT | HTL.TR_NO_HEADER)

        self.ExpandAllChildren(self.root)

    def SelectPiece(self, IDfamille=None, IDtype_piece=None, IDindividu=None):
        if (IDfamille, IDtype_piece, IDindividu) in self.dictItems:
            item = self.dictItems[(IDfamille, IDtype_piece, IDindividu)]
            self.SelectItem(item)
            return True
        return False


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        Style.appliquer_fenetre(panel, "surface")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = CTRL(panel, IDfamille=None, IDindividu=27)
        self.myOlv.MAJ()
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 1, wx.ALL | wx.EXPAND, Style.espace(1))
        panel.SetSizer(sizer_2)
        self.Layout()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
