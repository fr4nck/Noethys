#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-12 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import wx.lib.wordwrap as wordwrap

import Chemins
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _

if 'phoenix' in wx.PlatformInfo:
    from wx.adv import OwnerDrawnComboBox, ODCB_PAINTING_CONTROL, ODCB_PAINTING_SELECTED
else:
    from wx.combo import OwnerDrawnComboBox, ODCB_PAINTING_CONTROL, ODCB_PAINTING_SELECTED


class CTRL(OwnerDrawnComboBox):
    """Choix enrichi à deux niveaux typographiques, piloté par Repens."""

    def __init__(self, parent, donnees=[], nbreLignesDescription=1, wrap=False, hauteur=None, style=wx.CB_READONLY):
        self.donnees = donnees
        self.nbreLignesDescription = nbreLignesDescription
        if hauteur is None:
            self.hauteurItem = max(
                Style.cible_action("compact"),
                Style.hauteur_ligne("comfortable") + Style.px(self.nbreLignesDescription * 14),
            )
        else:
            self.hauteurItem = max(Style.hauteur_ligne("compact"), Style.px(hauteur))
        self.wrap = wrap
        self.selection = None

        listeLabels = [donnee["label"] for donnee in self.donnees]
        OwnerDrawnComboBox.__init__(
            self,
            parent,
            -1,
            choices=listeLabels,
            size=(-1, self.hauteurItem),
            style=style,
        )
        Style.appliquer_saisie(self)
        self.SetMinSize((-1, self.hauteurItem))
        self.Bind(wx.EVT_COMBOBOX, self.OnSelection)

    def OnSelection(self, event):
        self.selection = event.GetSelection()
        event.Skip()

    def SetDonnees(self, donnees):
        self.donnees = donnees
        self.SetItems([donnee["label"] for donnee in self.donnees])

    def GetSelection2(self):
        return self.selection

    def SetSelection2(self, index=None):
        if index is not None:
            self.Select(index)
            self.selection = index

    def OnDrawItem(self, dc, rect, item, flags):
        if item == wx.NOT_FOUND:
            self.selection = None
            return

        r = wx.Rect(*rect)
        marge = Style.espace(1)
        r.Deflate(marge, marge)

        if len(self.donnees) > 0:
            dictItem = self.donnees[item]
            if flags & ODCB_PAINTING_CONTROL:
                self.selection = item
                self.DessineItemActif(dc, r, dictItem, flags)
            else:
                self.DessineItem(dc, r, dictItem, flags)

    def DessineItemActif(self, dc, r, dictItem, flags=0):
        self.DessineItem(dc, r, dictItem, flags)

    def DessineItem(self, dc, r, dictItem, flags=0):
        """Dessine un item dans la liste popup."""
        selectionne = bool(flags & ODCB_PAINTING_SELECTED)
        texte_natif = dc.GetTextForeground()
        texte_principal = texte_natif if selectionne else Style.couleur("on_surface")
        texte_secondaire = texte_natif if selectionne else Style.couleur("on_surface_variant")
        espace = Style.espace(1)

        if "image" not in dictItem or dictItem["image"] is None:
            tailleImage = (0, 0)
        else:
            tailleImage = dictItem["image"].GetSize()
            dc.DrawBitmap(
                dictItem["image"],
                int(r.x),
                int(r.y + ((r.height / 2) - dc.GetCharHeight()) / 2),
            )

        dc.SetTextForeground(texte_principal)
        dc.SetFont(Style.police("body_emphasis"))
        hauteur_label = dc.GetCharHeight()
        x_texte = int(r.x + tailleImage[0] + espace)
        dc.DrawText(
            dictItem["label"],
            x_texte,
            int(r.y + max(0, (r.height / 2 - hauteur_label) / 2)),
        )

        description = dictItem.get("description", u"")
        dc.SetTextForeground(texte_secondaire)
        dc.SetFont(Style.police("body_small"))
        largeur = max(1, int(r.width - tailleImage[0] - espace))
        description = wordwrap.wordwrap(description, largeur, dc)
        y_description = int(r.y + max(hauteur_label + Style.espace(1), r.height / 2))
        if self.wrap is False:
            if "\n" in description:
                description = u"%s…" % description[0:max(0, description.index("\n") - 1)]
            dc.DrawText(description, x_texte, y_description)
        else:
            dc.DrawLabel(
                description,
                wx.Rect(
                    x_texte,
                    y_description,
                    largeur,
                    int(max(Style.hauteur_ligne("compact"), r.height - (y_description - r.y))),
                ),
            )

    def OnDrawBackground(self, dc, rect, item, flags):
        # Le contrôle fermé et la sélection conservent les conventions natives.
        if flags & (ODCB_PAINTING_CONTROL | ODCB_PAINTING_SELECTED):
            OwnerDrawnComboBox.OnDrawBackground(self, dc, rect, item, flags)
            return

        role = "surface_container_lowest" if item % 2 == 0 else "surface_container_low"
        fond = Style.couleur(role)
        dc.SetBrush(wx.Brush(fond))
        dc.SetPen(wx.Pen(fond))
        if 'phoenix' in wx.PlatformInfo:
            dc.DrawRectangle(rect)
        else:
            dc.DrawRectangleRect(rect)

    def OnMeasureItem(self, item):
        return self.hauteurItem

    def OnMeasureItemWidth(self, item):
        return -1


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        Style.appliquer_fenetre(panel, "surface")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer_1)

        donnees = [
            {"image": wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Loupe.png"), wx.BITMAP_TYPE_ANY), "label": _(u"Item 1"), "description": _(u"Ceci est la description de l'item 1 qui est vraiment un texte très long qui devrait normalement dépasser.")},
            {"image": wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Loupe.png"), wx.BITMAP_TYPE_ANY), "label": _(u"Item 2"), "description": _(u"Ceci est la description de l'item 2")},
            {"image": None, "label": _(u"Item 3"), "description": _(u"Ceci est la description de l'item 3")},
            {"label": _(u"Item 4"), "description": _(u"Ceci est la description de l'item 4")},
        ]
        self.ctrl1 = CTRL(panel, donnees=donnees, nbreLignesDescription=1)
        self.ctrl1.Select(0)

        donnees = []
        for x in range(1, 100):
            donnees.append({
                "image": wx.Bitmap(Chemins.GetStaticPath("Images/32x32/Loupe.png"), wx.BITMAP_TYPE_ANY),
                "label": _(u"Item %d") % x,
                "description": _(u"Ceci est la description de l'item %d") % x,
            })
        self.ctrl2 = CTRL(panel, donnees=donnees)

        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl1, 0, wx.ALL | wx.EXPAND, Style.espace(2))
        sizer_2.Add(self.ctrl2, 0, wx.ALL | wx.EXPAND, Style.espace(2))
        panel.SetSizer(sizer_2)
        self.Layout()

        self.Bind(wx.EVT_COMBOBOX, self.OnSelection2, self.ctrl2)

    def OnSelection2(self, event):
        print("Selection =", self.ctrl2.GetSelection2())


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "OL TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
