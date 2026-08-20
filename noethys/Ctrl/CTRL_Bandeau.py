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
from Utils import UTILS_Adaptations
from Utils import UTILS_Interface
from Utils.UTILS_Traduction import _
import wx
import wx.html as html


def _couleur_html(couleur):
    """Convertit une wx.Colour en couleur HTML sans dupliquer la palette."""
    try:
        return u"#%02X%02X%02X" % (couleur.Red(), couleur.Green(), couleur.Blue())
    except Exception:
        return u"#000000"


class MyHtml(html.HtmlWindow):
    def __init__(self, parent, texte="", hauteur=25):
        html.HtmlWindow.__init__(self, parent, -1, style=wx.html.HW_NO_SELECTION | wx.html.HW_SCROLLBAR_NEVER | wx.NO_FULL_REPAINT_ON_RESIZE)
        if "gtk2" in wx.PlatformInfo:
            self.SetStandardFonts()
        self.texte = texte
        self.SetBorders(0)
        self.SetMinSize((-1, hauteur))
        self.AppliquerTheme()

    def AppliquerTheme(self):
        """Applique au texte d'introduction les couleurs du design system."""
        sombre = UTILS_Interface.EstSombre()
        fond = UTILS_Interface.GetCouleurRole("surface_container_lowest", sombre=sombre)
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
    def __init__(self, parent, titre="", texte="", hauteurHtml=25, nomImage=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.nomImage = nomImage
        if self.nomImage != None :
            img = wx.Bitmap(Chemins.GetStaticPath(self.nomImage), wx.BITMAP_TYPE_ANY)
            self.image = wx.StaticBitmap(self, -1, img)
        self.ctrl_titre = wx.StaticText(self, -1, titre)
        self.ctrl_intro = MyHtml(self, texte, hauteurHtml)
        self.ligne = wx.StaticLine(self, -1)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        # Le bandeau reste une couche fonctionnelle légère : surface claire en
        # mode clair, surface profonde mais distincte en sombre. Aucun écran
        # métier n'a besoin de connaître les RGB correspondants.
        self.AppliquerTheme()

        # Conserve la typographie système de la plateforme et ne fixe plus une
        # famille/taille historique. Le moteur global d'affichage pourra ainsi
        # appliquer correctement l'échelle et la taille de texte choisies.
        police = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        try:
            police = wx.Font(police)
            if hasattr(police, "GetFractionalPointSize") and hasattr(police, "SetFractionalPointSize"):
                police.SetFractionalPointSize(max(5.0, police.GetFractionalPointSize() + 1.0))
            else:
                police.SetPointSize(max(5, police.GetPointSize() + 1))
            police.SetWeight(wx.FONTWEIGHT_BOLD)
            self.ctrl_titre.SetFont(police)
        except Exception:
            pass

    def AppliquerTheme(self):
        """Actualise les couleurs sémantiques du bandeau et de ses enfants."""
        sombre = UTILS_Interface.EstSombre()
        fond = UTILS_Interface.GetCouleurRole("surface_container_lowest", sombre=sombre)
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

        if hasattr(self, "image"):
            try:
                self.image.SetBackgroundColour(fond)
            except Exception:
                pass

        try:
            self.ctrl_intro.AppliquerTheme()
        except Exception:
            pass

    def __do_layout(self):
        grid_sizer_vertical = wx.FlexGridSizer(rows=2, cols=1, vgap=4, hgap=4)
        grid_sizer_horizontal = wx.FlexGridSizer(rows=1, cols=2, vgap=0, hgap=0)
        grid_sizer_texte = wx.FlexGridSizer(rows=2, cols=1, vgap=4, hgap=4)
        if self.nomImage != None :
            grid_sizer_horizontal.Add(self.image, 0, wx.ALL, 10)
        else :
            grid_sizer_horizontal.Add( (2, 2), 0, wx.ALL, 10)
        grid_sizer_texte.Add(self.ctrl_titre, 0, wx.TOP, 7)
        grid_sizer_texte.Add(self.ctrl_intro, 0, wx.RIGHT|wx.EXPAND, 5)
        grid_sizer_texte.AddGrowableRow(1)
        grid_sizer_texte.AddGrowableCol(0)
        grid_sizer_horizontal.Add(grid_sizer_texte, 1, wx.EXPAND, 0)
        grid_sizer_horizontal.AddGrowableRow(0)
        grid_sizer_horizontal.AddGrowableCol(1)
        grid_sizer_vertical.Add(grid_sizer_horizontal, 1, wx.EXPAND, 0)
        grid_sizer_vertical.Add(self.ligne, 0, wx.EXPAND, 0)
        self.SetSizer(grid_sizer_vertical)
        grid_sizer_vertical.Fit(self)
        grid_sizer_vertical.AddGrowableRow(0)
        grid_sizer_vertical.AddGrowableCol(0)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL|wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl= Bandeau(panel, _(u"COUCOU"), _(u"coincoin"), nomImage="Images/32x32/Femme.png")
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL|wx.EXPAND, 0)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()

if __name__ == '__main__':
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 200))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
