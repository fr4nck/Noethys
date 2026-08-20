#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import Chemins
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _
import wx
import wx.html as html


def _couleur_html(couleur):
    try:
        return u"#%02X%02X%02X" % (couleur.Red(), couleur.Green(), couleur.Blue())
    except Exception:
        return u"#000000"


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


class MyHtml(html.HtmlWindow):
    def __init__(self, parent, texte="", hauteur=25):
        html.HtmlWindow.__init__(
            self,
            parent,
            -1,
            style=wx.html.HW_NO_SELECTION | wx.html.HW_SCROLLBAR_NEVER | wx.NO_FULL_REPAINT_ON_RESIZE,
        )
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()
        self.texte = texte
        self.SetBorders(0)
        self.SetMinSize((-1, max(UTILS_UIMetrics.px(hauteur), UTILS_UIMetrics.row_height("compact"))))
        self.AppliquerTheme()

    def AppliquerTheme(self):
        sombre = UTILS_Interface.EstSombre()
        fond = UTILS_Interface.GetCouleurRole("surface_container", sombre=sombre)
        texte = UTILS_Interface.GetCouleurRole("on_surface_variant", sombre=sombre)
        try:
            self.SetBackgroundColour(fond)
            self.SetForegroundColour(texte)
        except Exception:
            pass
        self.SetPage(
            u'<BODY BGCOLOR="%s" TEXT="%s"><FONT SIZE=-2>%s</FONT></BODY>' % (
                _couleur_html(fond),
                _couleur_html(texte),
                self.texte,
            )
        )


class Bandeau(wx.Panel):
    """En-tête commun des dialogues Noethys, compact et réellement responsive."""

    def __init__(self, parent, titre="", texte="", hauteurHtml=25, nomImage=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.nomImage = nomImage
        self.image = None

        if self.nomImage is not None:
            taille = UTILS_UIMetrics.icon_size("hero")
            self.image = wx.StaticBitmap(self, -1, _bitmap_adapte(self.nomImage, taille))

        self.ctrl_titre = wx.StaticText(self, -1, titre)
        self.ctrl_intro = MyHtml(self, texte, hauteurHtml)
        self.ligne = wx.StaticLine(self, -1)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.AppliquerTheme()

        police = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        try:
            police = wx.Font(police)
            base = max(8, police.GetPointSize())
            facteur = (UTILS_Interface.GetTailleTexte() / 100.0)
            police.SetPointSize(max(9, int(round((base + 1) * facteur))))
            police.SetWeight(wx.FONTWEIGHT_SEMIBOLD if hasattr(wx, "FONTWEIGHT_SEMIBOLD") else wx.FONTWEIGHT_BOLD)
            self.ctrl_titre.SetFont(police)
        except Exception:
            pass

    def AppliquerTheme(self):
        sombre = UTILS_Interface.EstSombre()
        fond = UTILS_Interface.GetCouleurRole("surface_container", sombre=sombre)
        texte = UTILS_Interface.GetCouleurRole("on_surface", sombre=sombre)
        bordure = UTILS_Interface.GetCouleurRole("outline_variant", sombre=sombre)

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
        """BoxSizer volontaire : le texte doit récupérer toute la largeur libre."""
        marge_x = UTILS_UIMetrics.spacing(3)
        marge_y = UTILS_UIMetrics.spacing(2)
        espace = UTILS_UIMetrics.spacing(2)

        contenu = wx.BoxSizer(wx.HORIZONTAL)
        if self.image is not None:
            contenu.Add(self.image, 0, wx.ALIGN_TOP | wx.RIGHT, marge_x)

        textes = wx.BoxSizer(wx.VERTICAL)
        textes.Add(self.ctrl_titre, 0, wx.EXPAND | wx.BOTTOM, max(2, UTILS_UIMetrics.spacing(1)))
        textes.Add(self.ctrl_intro, 1, wx.EXPAND)
        contenu.Add(textes, 1, wx.EXPAND)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(contenu, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, marge_x)
        principal.Add(self.ligne, 0, wx.EXPAND)

        self.SetSizer(principal)
        self.SetMinSize((-1, max(UTILS_UIMetrics.panel_min_height("compact"), self.GetBestSize().GetHeight())))
        self.Layout()


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
