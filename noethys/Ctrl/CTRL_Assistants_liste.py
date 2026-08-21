#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-18 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
from Utils import UTILS_StyleRepens as Style
import wx
import six
if wx.VERSION < (2, 9, 0, 0):
    from Outils import ultimatelistctrl as ULC
else:
    from wx.lib.agw import ultimatelistctrl as ULC

from Ctrl import CTRL_Assistant_annuelle
from Ctrl import CTRL_Assistant_sejour
from Ctrl import CTRL_Assistant_stage
from Ctrl import CTRL_Assistant_cantine
from Ctrl import CTRL_Assistant_sorties


LISTE_ASSISTANTS = [
    {"code": "nouveau", "image": "Generation.png", "nom": _(u"Créer une nouvelle activité"),
     "description": _(u"Personnalisez votre nouvelle activité de A à Z")},
    {"code": "annuelle", "image": "Basket.png", "nom": _(u"Une activité culturelle ou sportive annuelle"),
     "description": _(u"Assistant pour créer une activité annuelle : club de gym, danse, couture, etc...")},
    {"code": "sejour", "image": "Camping.png", "nom": _(u"Un séjour"),
     "description": _(u"Assistant pour créer un séjour, un camp, un mini-camp...")},
    {"code": "stage", "image": "Guitare.png", "nom": _(u"Un stage"),
     "description": _(u"Assistant pour créer un stage de théâtre, de danse, de guitare, etc...")},
    {"code": "cantine", "image": "Repas.png", "nom": _(u"Une cantine"),
     "description": _(u"Assistant pour créer une cantine avec un ou plusieurs services")},
    {"code": "sorties", "image": "Bus.png", "nom": _(u"Des sorties familiales"),
     "description": _(u"Assistant pour créer une activité de gestion de sorties familiales...")},
]


def _BitmapActivite(nom):
    """Conserve les pictos métier riches, mais les adapte à l'échelle Repens."""
    taille = Style.taille_icone("hero")
    try:
        bitmap = wx.Bitmap(Chemins.GetStaticIconPath("Images/32x32/%s" % nom, taille=taille), wx.BITMAP_TYPE_ANY)
        if bitmap.IsOk() and (bitmap.GetWidth() != taille or bitmap.GetHeight() != taille):
            bitmap = wx.Bitmap(bitmap.ConvertToImage().Scale(taille, taille, wx.IMAGE_QUALITY_HIGH))
        return bitmap
    except Exception:
        return wx.NullBitmap


class FirstColumnRenderer(object):
    def __init__(self, parent, dictItem=None):
        self.parent = parent
        dictItem = dictItem or {}

        self.normalFont = Style.police("label")
        self.smallerFont = Style.police("body_small")

        self.code = dictItem.get("code")
        self.icon = _BitmapActivite(dictItem.get("image", ""))
        self.text = dictItem.get("nom", "")
        self.description = dictItem.get("description", "")

    def _Ellipsize(self, texte, dc, largeur):
        if largeur <= 20:
            return ""
        try:
            return wx.Control.Ellipsize(texte, dc, wx.ELLIPSIZE_END, largeur)
        except Exception:
            return texte

    def DrawSubItem(self, dc, rect, line, highlighted, enabled):
        bmpWidth, bmpHeight = self.icon.GetWidth(), self.icon.GetHeight()
        marge = Style.espace(2)
        x_icon = rect.x + marge
        y_icon = rect.y + max(0, (rect.height - bmpHeight) // 2)
        if self.icon.IsOk():
            dc.DrawBitmap(self.icon, int(x_icon), int(y_icon), True)

        x_texte = rect.x + bmpWidth + marge * 2
        largeur_texte = max(20, rect.width - (x_texte - rect.x) - marge)

        dc.SetFont(self.normalFont)
        dc.SetTextForeground(Style.couleur("on_surface"))
        _, h_titre = dc.GetTextExtent(self.text)
        titre = self._Ellipsize(self.text, dc, largeur_texte)
        dc.DrawText(titre, int(x_texte), int(rect.y + max(marge, rect.height * 0.22 - h_titre / 2)))

        if self.description:
            dc.SetFont(self.smallerFont)
            dc.SetTextForeground(Style.couleur("on_surface_variant"))
            _, h_desc = dc.GetTextExtent(self.description)
            description = self._Ellipsize(self.description, dc, largeur_texte)
            dc.DrawText(description, int(x_texte), int(rect.y + rect.height * 0.68 - h_desc / 2))

    def GetLineHeight(self):
        icon_h = self.icon.GetHeight() if self.icon.IsOk() else 0
        return max(Style.px(58), icon_h + Style.espace(4))

    def GetSubItemWidth(self):
        try:
            largeur = self.parent.GetClientSize().GetWidth()
        except Exception:
            largeur = 0
        return max(Style.px(320), largeur - Style.espace(2))


class CTRL(ULC.UltimateListCtrl):
    def __init__(self, parent):
        ULC.UltimateListCtrl.__init__(
            self,
            parent,
            -1,
            style=wx.BORDER_NONE,
            agwStyle=wx.LC_REPORT | wx.LC_NO_HEADER | wx.LC_HRULES | ULC.ULC_HAS_VARIABLE_ROW_HEIGHT,
        )
        Style.appliquer_liste(self)
        self.EnableSelectionVista()
        self.Bind(wx.EVT_SIZE, self._OnSize)
        self.Remplissage()

    def _OnSize(self, event):
        event.Skip()
        wx.CallAfter(self._AjusteColonne)

    def _AjusteColonne(self):
        try:
            largeur = max(Style.px(320), self.GetClientSize().GetWidth() - Style.espace(1))
            self.SetColumnWidth(0, largeur)
        except Exception:
            pass

    def Remplissage(self):
        self.ClearAll()
        self.InsertColumn(0, "")

        for dictItem in LISTE_ASSISTANTS:
            index = self.InsertStringItem(six.MAXSIZE, "")
            self.SetItemCustomRenderer(index, 0, FirstColumnRenderer(self, dictItem))
            self.SetItemPyData(index, dictItem)

        wx.CallAfter(self._AjusteColonne)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(self, "surface")
        Style.appliquer_fenetre(panel, "surface")
        self.ctrl = CTRL(panel)
        self.Bind(ULC.EVT_LIST_ITEM_ACTIVATED, self.OnSelection, self.ctrl)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.EXPAND)
        panel.SetSizer(sizer)
        cadre = wx.BoxSizer(wx.VERTICAL)
        cadre.Add(panel, 1, wx.EXPAND)
        self.SetSizer(cadre)
        self.Layout()
        self.CentreOnScreen()

    def OnSelection(self, event):
        index = self.ctrl.GetFirstSelected()
        print(self.ctrl.GetItemPyData(index))


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(600, 600))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
