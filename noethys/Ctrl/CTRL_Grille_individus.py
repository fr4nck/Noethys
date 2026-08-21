#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:          Licence GNU GPL
#-----------------------------------------------------------

import datetime
import html as html_std

import wx
import wx.html as wxhtml

import Chemins
from Ctrl import CTRL_Photo
from Data import DATA_Civilites as Civilites
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _

if wx.VERSION < (2, 9, 0, 0):
    from Outils import ultimatelistctrl as ULC
else:
    from wx.lib.agw import ultimatelistctrl as ULC


DICT_CIVILITES = Civilites.GetDictCivilites()


def DateEngEnDateDD(dateEng):
    return datetime.date.fromisoformat(dateEng[:10])


def CalculeAge(dateReference, date_naiss):
    return (dateReference.year - date_naiss.year) - int(
        (dateReference.month, dateReference.day) < (date_naiss.month, date_naiss.day)
    )


def _CouleurHtml(couleur):
    try:
        return "#%02X%02X%02X" % (couleur.Red(), couleur.Green(), couleur.Blue())
    except Exception:
        return "#202020"


def _TexteContraste(fond):
    try:
        luminance = 0.2126 * fond.Red() + 0.7152 * fond.Green() + 0.0722 * fond.Blue()
        return wx.Colour(24, 24, 24) if luminance >= 150 else wx.Colour(248, 248, 248)
    except Exception:
        return Style.couleur("on_surface")


class CTRL_famille(wxhtml.HtmlWindow):
    """Bandeau famille compact, sans couleur historique imposée."""

    def __init__(self, parent, IDfamille, dictIndividus, texte="", hauteur=None, couleurFond=None):
        wxhtml.HtmlWindow.__init__(
            self,
            parent,
            -1,
            style=wxhtml.HW_NO_SELECTION | wxhtml.HW_SCROLLBAR_NEVER | wx.NO_FULL_REPAINT_ON_RESIZE,
        )
        self.IDfamille = IDfamille
        self.dictIndividus = dictIndividus
        self.couleurFond = couleurFond or Style.couleur("surface_container_high")
        self.couleurTexte = (
            _TexteContraste(self.couleurFond)
            if couleurFond is not None
            else Style.couleur("on_surface")
        )
        self.SetBackgroundColour(self.couleurFond)
        self.SetForegroundColour(self.couleurTexte)
        self.SetBorders(Style.espace(2))
        if hauteur is None:
            hauteur = Style.cible_action("compact")
        self.SetMinSize((-1, hauteur))
        try:
            police = Style.police("body")
            self.SetStandardFonts(police.GetPointSize(), police.GetFaceName(), police.GetFaceName())
        except Exception:
            if "gtk2" in wx.PlatformInfo:
                self.SetStandardFonts()

        texte = _(u"Famille de %s") % self.GetNomsTitulaires()
        self.SetTexte(texte)

    def SetTexte(self, texte=""):
        self.SetPage(
            u"<B><FONT COLOR='%s'>%s</FONT></B>" % (
                _CouleurHtml(self.couleurTexte),
                html_std.escape(str(texte)),
            )
        )
        self.SetBackgroundColour(self.couleurFond)

    def GetNomsTitulaires(self):
        listeTitulaires = []
        for _IDindividu, dictIndividu in self.dictIndividus.items():
            if dictIndividu["titulaire"] == 1:
                listeTitulaires.append(u"%s %s" % (dictIndividu["nom"], dictIndividu["prenom"]))
        if len(listeTitulaires) == 1:
            return listeTitulaires[0]
        if len(listeTitulaires) == 2:
            return _(u"%s et %s") % (listeTitulaires[0], listeTitulaires[1])
        if len(listeTitulaires) > 2:
            return _(u"%s et %s") % (u", ".join(listeTitulaires[:-1]), listeTitulaires[-1])
        return u""


class CTRL_individus(ULC.UltimateListCtrl):
    """Sélection visuelle des membres inscrits d'une famille."""

    def __init__(self, parent, IDfamille=None, dictIndividus={}, listeSelectionIndividus=[], selectionTous=False):
        ULC.UltimateListCtrl.__init__(self, parent, -1, agwStyle=wx.LC_ICON | wx.LC_ALIGN_LEFT)
        self.parent = parent
        self.IDfamille = IDfamille
        self.dictIndividus = dictIndividus

        Style.appliquer_liste(self)
        try:
            self.SetFirstGradientColour(None)
            self.SetSecondGradientColour(None)
            self.EnableSelectionGradient(False)
            self.EnableSelectionVista(True)
        except Exception:
            pass
        try:
            self.SetDisabledTextColour(Style.couleur("on_surface_variant"))
        except Exception:
            pass

        listeIndividus = []
        for IDindividu, dictIndividu in self.dictIndividus.items():
            if len(dictIndividu["inscriptions"]) > 0:
                listeIndividus.append((dictIndividu["prenom"], IDindividu))
        listeIndividus.sort()

        self.dictPhotos = {}
        taillePhoto = min(Style.px(96), max(Style.px(56), Style.px(64)))
        il = wx.ImageList(taillePhoto, taillePhoto, True)
        for _prenom, IDindividu in listeIndividus:
            dictIndividu = self.dictIndividus[IDindividu]
            IDcivilite = dictIndividu["IDcivilite"]
            nomFichier = Chemins.GetStaticPath("Images/128x128/%s" % DICT_CIVILITES[IDcivilite]["nomImage"])
            _IDphoto, bmp = CTRL_Photo.GetPhoto(
                IDindividu=IDindividu,
                nomFichier=nomFichier,
                taillePhoto=(taillePhoto, taillePhoto),
                qualite=100,
            )
            self.dictPhotos[IDindividu] = il.Add(bmp)
        self.AssignImageList(il, wx.IMAGE_LIST_NORMAL)

        for index, (_prenom, IDindividu) in enumerate(listeIndividus):
            dictIndividu = self.dictIndividus[IDindividu]
            label = dictIndividu["prenom"] or " "
            self.InsertImageStringItem(index, label, self.dictPhotos[IDindividu])
            self.SetItemData(index, IDindividu)
            if IDindividu in listeSelectionIndividus or selectionTous is True:
                self.Select(index)

        self.SetMinSize((Style.px(220), taillePhoto + Style.espace(5)))
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)

    def OnLeftUp(self, event):
        self.OnSelection()

    def OnSelection(self):
        listeSelections = self.GetSelections()
        self.GetGrandParent().SetListeSelectionIndividus(listeSelections)
        self.GetGrandParent().MAJ_grille()

    def SetSelections(self, listeIDindividus=[]):
        for IDindividu in listeIDindividus:
            index = self.FindItemData(-1, IDindividu)
            if index != -1:
                self.Select(index)

    def DeselectTout(self):
        for index in range(0, self.GetItemCount()):
            self.Select(index, False)

    def GetSelections(self):
        listeIDselections = []
        for index in range(0, self.GetItemCount()):
            if self.IsSelected(index):
                listeIDselections.append(self.GetItemData(index))
        return listeIDselections


class CTRL(wx.Panel):
    def __init__(self, parent, IDfamille=None, dictIndividus={}, selectionIndividus=[], selectionTous=False):
        wx.Panel.__init__(self, parent, -1, style=wx.BORDER_NONE | wx.TAB_TRAVERSAL)
        self.parent = parent
        Style.appliquer_fenetre(self, "surface")

        self.ctrl_famille = CTRL_famille(self, IDfamille, dictIndividus)
        self.ctrl_individus = CTRL_individus(self, IDfamille, dictIndividus, selectionIndividus, selectionTous)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl_famille, 0, wx.EXPAND)
        sizer.Add(self.ctrl_individus, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()

    def SetSelections(self, listeIDindividus=[]):
        self.ctrl_individus.SetSelections(listeIDindividus)

    def GetSelections(self):
        return self.ctrl_individus.GetSelections()

    def DeselectTout(self):
        self.ctrl_individus.DeselectTout()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        Style.appliquer_fenetre(self, "surface")
        panel = wx.Panel(self, -1, name="test1")
        Style.appliquer_fenetre(panel, "surface")
        self.myOlv = CTRL(panel, IDfamille=209)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.myOlv, 1, wx.ALL | wx.EXPAND, Style.espace(2))
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
