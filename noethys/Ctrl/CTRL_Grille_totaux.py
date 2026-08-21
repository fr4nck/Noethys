#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:          Licence GNU GPL
#-----------------------------------------------------------

import wx
import wx.lib.agw.hypertreelist as HTL

from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


class CTRL_Unite_remplissage(wx.Panel):
    """Petite cellule de total, alignée sur les surfaces du design system."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        self.parent = parent
        self.ctrl = wx.StaticText(self, -1, u"XXX", style=wx.ALIGN_RIGHT)

        Style.appliquer_fenetre(self, "surface_container_high")
        Style.appliquer_texte(
            self.ctrl,
            role="body_emphasis",
            role_texte="on_surface",
            role_fond="surface_container_high",
        )

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddStretchSpacer(1)
        sizer.Add(self.ctrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, Style.espace(1))
        self.SetSizer(sizer)
        self.SetMinSize((Style.px(60), Style.cible_action("compact")))

    def SetValeur(self, valeur=""):
        self.ctrl.SetLabel(str(valeur))
        self.Layout()
        self.Refresh()


class CTRL(HTL.HyperTreeList):
    """Totaux de la grille de consommations, thème et largeur responsive."""

    def __init__(self, parent, grille=None):
        HTL.HyperTreeList.__init__(self, parent, -1)
        self.parent = parent
        self.grille = grille
        self.date = None
        self._resize_pending = False

        Style.appliquer_liste(self)
        try:
            main = self.GetMainWindow()
            Style.appliquer_liste(main)
        except Exception:
            pass

        if 'phoenix' in wx.PlatformInfo:
            TR_COLUMN_LINES = HTL.TR_COLUMN_LINES
        else:
            TR_COLUMN_LINES = wx.TR_COLUMN_LINES
        self.SetAGWWindowStyleFlag(
            TR_COLUMN_LINES | wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS |
            wx.TR_HAS_VARIABLE_ROW_HEIGHT | wx.TR_FULL_ROW_HIGHLIGHT | HTL.TR_NO_HEADER
        )
        self.SetMinSize((Style.px(320), Style.px(180)))
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def OnSize(self, event):
        event.Skip()
        if self._resize_pending:
            return
        self._resize_pending = True
        wx.CallAfter(self._AjusterColonnes)

    def _AjusterColonnes(self):
        self._resize_pending = False
        try:
            nbre = self.GetColumnCount()
            if nbre <= 0:
                return
            largeur = self.GetClientSize().GetWidth()
            marge = Style.espace(2)
            largeur_groupe = max(Style.px(150), int(largeur * 0.34))
            largeur_groupe = min(largeur_groupe, max(Style.px(150), largeur - marge))
            self.SetColumnWidth(0, largeur_groupe)
            if nbre > 1:
                disponible = max(0, largeur - largeur_groupe - marge)
                largeur_unite = max(Style.px(54), disponible // (nbre - 1) if disponible else 0)
                for index in range(1, nbre):
                    self.SetColumnWidth(index, largeur_unite)
        except Exception:
            pass

    def MAJ(self, date=None):
        if date is not None:
            self.date = date
        self.Freeze()
        try:
            self.DeleteAllItems()
            for numColonne in range(self.GetColumnCount() - 1, -1, -1):
                self.RemoveColumn(numColonne)
            self.Remplissage()
        finally:
            self.Thaw()
        wx.CallAfter(self._AjusterColonnes)

    def Remplissage(self):
        self.dictGroupes = self.grille.dictGroupes
        self.dictActivites = self.grille.dictActivites
        self.listeActivites = self.grille.listeActivites
        self.dictListeUnites = self.grille.dictListeUnites
        self.dictUnites = self.grille.dictUnites
        self.dictRemplissage = self.grille.dictRemplissage
        self.dictRemplissage2 = self.grille.dictRemplissage2
        self.dictUnitesRemplissage = self.grille.dictUnitesRemplissage
        self.dictConsoUnites = self.grille.dictConsoUnites

        self.dictBranches = {"activites": {}, "groupes": {}, "totaux": {}}

        listeGroupes = sorted((dictGroupe["ordre"], IDgroupe) for IDgroupe, dictGroupe in self.dictGroupes.items())
        self.dictGroupeTmp = {}
        for ordre, IDgroupe in listeGroupes:
            dictGroupe = self.dictGroupes[IDgroupe]
            IDactivite = dictGroupe["IDactivite"]
            self.dictGroupeTmp.setdefault(IDactivite, []).append((IDgroupe, dictGroupe["nom"]))

        for IDactivite in self.listeActivites:
            self.dictGroupeTmp.setdefault(IDactivite, [(0, _(u"Groupe unique"))])

        self.dictUnitesRemplissageTemp = {}
        for IDunite_remplissage, dictUniteRemplissage in self.dictRemplissage.items():
            if "IDactivite" in dictUniteRemplissage:
                IDactivite = dictUniteRemplissage["IDactivite"]
                self.dictUnitesRemplissageTemp.setdefault(IDactivite, []).append((
                    dictUniteRemplissage["ordre"],
                    IDunite_remplissage,
                    dictUniteRemplissage["abrege"],
                ))
                self.dictUnitesRemplissageTemp[IDactivite].sort()

        listeNbreUnites = []
        for IDactivite in self.listeActivites:
            nbre = len(self.dictListeUnites.get(IDactivite, []))
            nbre += len(self.dictUnitesRemplissageTemp.get(IDactivite, []))
            listeNbreUnites.append(nbre)
        if len(listeNbreUnites) == 0:
            return

        self.AddColumn(_(u"Groupe"))
        self.SetColumnAlignment(0, wx.ALIGN_LEFT)
        for _index in range(max(listeNbreUnites)):
            self.AddColumn(u"")
            self.SetColumnAlignment(self.GetColumnCount() - 1, wx.ALIGN_CENTER)

        self.root = self.AddRoot(_(u"Racine"))
        couleur_activite = Style.couleur("surface_container_high")
        couleur_total = Style.couleur("danger")

        for IDactivite in self.listeActivites:
            label = self.dictActivites[IDactivite]["nom"] if IDactivite in self.dictActivites else u"?"
            activite = self.AppendItem(self.root, label)
            self.dictBranches["activites"][IDactivite] = activite
            self.SetPyData(activite, IDactivite)
            self.SetItemBold(activite, True)
            self.SetItemBackgroundColour(activite, couleur_activite)

            indexColonne = 1
            for dictUnite in self.dictListeUnites.get(IDactivite, []):
                self.SetItemText(activite, dictUnite["abrege"], indexColonne)
                indexColonne += 1
            for ordre, IDunite_remplissage, nomUniteRemplissage in self.dictUnitesRemplissageTemp.get(IDactivite, []):
                self.SetItemText(activite, nomUniteRemplissage, indexColonne)
                indexColonne += 1

            for IDgroupe, nomGroupe in self.dictGroupeTmp[IDactivite]:
                groupe = self.AppendItem(activite, nomGroupe)
                self.dictBranches["groupes"][IDgroupe] = groupe
                self.SetPyData(groupe, IDgroupe)

            total = self.AppendItem(activite, _(u"Total"))
            self.dictBranches["totaux"][IDactivite] = total
            self.SetPyData(total, None)
            self.SetItemTextColour(total, couleur_total)
            self.SetItemBold(total, True)

        self.ExpandAllChildren(self.root)
        self.MAJ_contenu()
        wx.CallAfter(self._AjusterColonnes)

    def MAJ_donnees(self):
        self.dictGroupes = self.grille.dictGroupes
        self.dictActivites = self.grille.dictActivites
        self.listeActivites = self.grille.listeActivites
        self.dictListeUnites = self.grille.dictListeUnites
        self.dictUnites = self.grille.dictUnites
        self.dictRemplissage = self.grille.dictRemplissage
        self.dictRemplissage2 = self.grille.dictRemplissage2
        self.dictUnitesRemplissage = self.grille.dictUnitesRemplissage
        self.dictConsoUnites = self.grille.dictConsoUnites

    def MAJ_contenu(self):
        for IDactivite in self.listeActivites:
            dictTotaux = {}
            for IDgroupe, nomGroupe in self.dictGroupeTmp[IDactivite]:
                groupe = self.dictBranches["groupes"][IDgroupe]
                indexColonne = 1

                for dictUnite in self.dictListeUnites.get(IDactivite, []):
                    IDunite = dictUnite["IDunite"]
                    try:
                        nbre = self.dictConsoUnites[IDunite][IDgroupe]
                        dictTotaux[indexColonne] = dictTotaux.get(indexColonne, 0) + nbre
                    except Exception:
                        nbre = 0
                    self.SetItemText(groupe, str(nbre) if nbre != 0 else "", indexColonne)
                    indexColonne += 1

                for ordre, IDunite_remplissage, nomUniteRemplissage in self.dictUnitesRemplissageTemp.get(IDactivite, []):
                    nbre = 0
                    if IDunite_remplissage in self.dictRemplissage2:
                        if self.date in self.dictRemplissage2[IDunite_remplissage]:
                            if IDgroupe in self.dictRemplissage2[IDunite_remplissage][self.date]:
                                d = self.dictRemplissage2[IDunite_remplissage][self.date][IDgroupe]
                                nbre += d.get("reservation", 0)
                                nbre += d.get("present", 0)
                                dictTotaux[indexColonne] = dictTotaux.get(indexColonne, 0) + nbre
                    self.SetItemText(groupe, str(nbre) if nbre != 0 else "", indexColonne)
                    indexColonne += 1

            total = self.dictBranches["totaux"][IDactivite]
            for indexColonne in range(1, self.GetColumnCount()):
                nbre = dictTotaux.get(indexColonne, 0)
                self.SetItemText(total, str(nbre) if nbre != 0 else "", indexColonne)

    def OnCompareItems(self, item1, item2):
        data1 = self.GetPyData(item1)
        data2 = self.GetPyData(item2)
        if data1 is None or data2 is None:
            return 0
        if data1 > data2:
            return 1
        if data1 < data2:
            return -1
        return 0

    def RAZ(self):
        self.DeleteAllItems()
        for indexColonne in range(self.GetColumnCount() - 1, -1, -1):
            self.RemoveColumn(indexColonne)
        try:
            self.DeleteRoot()
        except Exception:
            pass
