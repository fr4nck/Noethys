#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import html as html_std
import re

import Chemins
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _
import wx


def _texte_simple(texte):
    """Convertit les quelques balises historiques en texte natif lisible."""
    if texte in (None, ""):
        return u""
    texte = str(texte)
    texte = re.sub(r"(?i)<\s*br\s*/?\s*>", "\n", texte)
    texte = re.sub(r"(?i)</\s*p\s*>", "\n", texte)
    texte = re.sub(r"<[^>]+>", "", texte)
    try:
        texte = html_std.unescape(texte)
    except Exception:
        pass
    return texte.strip()


def _bitmap_adapte(chemin, taille):
    """Charge une illustration historique sans imposer son ancienne géométrie."""
    try:
        bitmap = wx.Bitmap(Chemins.GetStaticIconPath(chemin, taille=taille), wx.BITMAP_TYPE_ANY)
        if bitmap.IsOk() and (bitmap.GetWidth() != taille or bitmap.GetHeight() != taille):
            image = bitmap.ConvertToImage().Scale(taille, taille, wx.IMAGE_QUALITY_HIGH)
            bitmap = wx.Bitmap(image)
        return bitmap
    except Exception:
        return wx.NullBitmap


class TexteIntro(wx.StaticText):
    """Texte de bandeau natif qui se recompose avec la largeur disponible."""

    def __init__(self, parent, texte=u""):
        self.texte_original = _texte_simple(texte)
        wx.StaticText.__init__(self, parent, -1, self.texte_original, style=wx.ST_NO_AUTORESIZE)
        self.SetMinSize((-1, UTILS_UIMetrics.row_height("compact")))
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.AppliquerTheme()
        wx.CallAfter(self.Reflow)

    def AppliquerTheme(self):
        try:
            self.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface_variant"))
            self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container"))
        except Exception:
            pass

    def SetTexte(self, texte):
        self.texte_original = _texte_simple(texte)
        self.Reflow()

    def Reflow(self):
        try:
            largeur = int(self.GetClientSize().GetWidth())
        except Exception:
            largeur = 0
        self.SetLabel(self.texte_original)
        if largeur > UTILS_UIMetrics.px(120):
            try:
                self.Wrap(max(UTILS_UIMetrics.px(120), largeur - UTILS_UIMetrics.spacing(1)))
            except Exception:
                pass
        try:
            self.InvalidateBestSize()
            parent = self.GetParent()
            if parent is not None:
                parent.Layout()
        except Exception:
            pass

    def OnSize(self, event):
        event.Skip()
        wx.CallAfter(self.Reflow)


class Bandeau(wx.Panel):
    """En-tête commun des dialogues Noethys, compact et réellement responsive."""

    def __init__(self, parent, titre="", texte="", hauteurHtml=25, nomImage=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        self.nomImage = nomImage
        self.image = None
        # ``hauteurHtml`` reste accepté pour compatibilité API, mais aucune
        # hauteur de texte n'est désormais figée par cette valeur.
        self.hauteurHtml = hauteurHtml

        if self.nomImage is not None:
            taille = UTILS_UIMetrics.icon_size("hero")
            self.image = wx.StaticBitmap(self, -1, _bitmap_adapte(self.nomImage, taille))

        self.ctrl_titre = wx.StaticText(self, -1, titre)
        self.ctrl_intro = TexteIntro(self, texte)
        self.ligne = wx.StaticLine(self, -1)

        self.__set_properties()
        self.__do_layout()
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def __set_properties(self):
        self.AppliquerTheme()

        police = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        try:
            police = wx.Font(police)
            base = max(8, police.GetPointSize())
            facteur = UTILS_Interface.GetTailleTexte() / 100.0
            police.SetPointSize(max(9, int(round((base + 1) * facteur))))
            police.SetWeight(wx.FONTWEIGHT_SEMIBOLD if hasattr(wx, "FONTWEIGHT_SEMIBOLD") else wx.FONTWEIGHT_BOLD)
            self.ctrl_titre.SetFont(police)
        except Exception:
            pass

    def AppliquerTheme(self):
        fond = UTILS_Interface.GetCouleurRole("surface_container")
        texte = UTILS_Interface.GetCouleurRole("on_surface")
        bordure = UTILS_Interface.GetCouleurRole("outline_variant")

        try:
            self.SetBackgroundColour(fond)
            self.ctrl_titre.SetBackgroundColour(fond)
            self.ctrl_titre.SetForegroundColour(texte)
            self.ligne.SetForegroundColour(bordure)
            self.ligne.SetBackgroundColour(bordure)
        except Exception:
            pass

        if self.image is not None:
            try:
                self.image.SetBackgroundColour(fond)
            except Exception:
                pass

        try:
            self.ctrl_intro.AppliquerTheme()
        except Exception:
            pass

    def __do_layout(self):
        """Le texte récupère toute la largeur libre, sans hauteur HTML fixe."""
        marge_x = UTILS_UIMetrics.spacing(3)
        marge_y = UTILS_UIMetrics.spacing(2)

        contenu = wx.BoxSizer(wx.HORIZONTAL)
        if self.image is not None:
            contenu.Add(self.image, 0, wx.ALIGN_TOP | wx.RIGHT, marge_x)

        textes = wx.BoxSizer(wx.VERTICAL)
        textes.Add(self.ctrl_titre, 0, wx.EXPAND | wx.BOTTOM, max(2, UTILS_UIMetrics.spacing(1)))
        textes.Add(self.ctrl_intro, 0, wx.EXPAND)
        contenu.Add(textes, 1, wx.EXPAND)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(contenu, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, marge_x)
        principal.Add(self.ligne, 0, wx.EXPAND)

        self.SetSizer(principal)
        self.SetMinSize((-1, UTILS_UIMetrics.panel_min_height("compact")))
        self.Layout()

    def OnSize(self, event):
        event.Skip()
        wx.CallAfter(self.ctrl_intro.Reflow)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = Bandeau(panel, _(u"COUCOU"), _(u"coincoin"), nomImage="Images/32x32/Femme.png")
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.EXPAND)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 200))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
