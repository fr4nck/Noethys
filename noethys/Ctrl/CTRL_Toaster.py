#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import Chemins
import wx
import wx.lib.agw.toasterbox as Toaster

from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


def _CouleursFondExplicite(fond):
    """Choisit un texte lisible lorsqu'un appelant impose un fond historique."""
    try:
        texte = wx.BLACK if fond.GetLuminance() >= 0.55 else wx.WHITE
    except Exception:
        texte = wx.WHITE
    return texte, texte


def ToasterUtilisateur(parent, titre=u"", prenom=_(u"Philippe"), nomImage="Femme", taille=(200, 100), couleurFond=None):
    """Affiche une boîte de dialogue temporaire."""
    # Si un appelant fournit une couleur historique/personnalisée, elle garde
    # la priorité. Sinon le toaster suit automatiquement Repens Design.
    if couleurFond is None:
        fond = Style.couleur("surface_container_highest")
        texte_principal = Style.couleur("on_surface")
        texte_secondaire = Style.couleur("on_surface_variant")
    else:
        fond = couleurFond
        texte_principal, texte_secondaire = _CouleursFondExplicite(fond)

    largeur = Style.px(400)
    hauteur = Style.px(148)

    tb = Toaster.ToasterBox(parent, Toaster.TB_COMPLEX, Toaster.TB_DEFAULT_STYLE, Toaster.TB_ONTIME) # TB_CAPTION
    tb.SetTitle(titre)
    tb.SetPopupSize((largeur, hauteur))
    if 'phoenix' in wx.PlatformInfo:
        largeurEcran, hauteurEcran = wx.ScreenDC().GetSize()
    else:
        largeurEcran, hauteurEcran = wx.ScreenDC().GetSizeTuple()
    tb.SetPopupPosition((largeurEcran-largeur-Style.espace(2), hauteurEcran-hauteur-Style.px(50)))
    tb.SetPopupPauseTime(3000)
    tb.SetPopupScrollSpeed(4)
    tb.SetPopupBackgroundColour(fond)
    tb.SetPopupTextColour(texte_principal)

    tbpanel = tb.GetToasterBoxWindow()
    panel = wx.Panel(tbpanel, -1)
    panel.SetBackgroundColour(fond)
    panel.SetForegroundColour(texte_principal)
    panel.SetFont(Style.police("body"))

    sizer = wx.BoxSizer(wx.VERTICAL)
    sizerHoriz = wx.BoxSizer(wx.HORIZONTAL)
    sizerTexte = wx.BoxSizer(wx.VERTICAL)

    # Image
    bmp = wx.StaticBitmap(panel, -1, wx.Bitmap(Chemins.GetStaticPath("Images/Avatars/128x128/%s.png" % nomImage), wx.BITMAP_TYPE_PNG))
    try:
        bmp.SetBackgroundColour(fond)
    except Exception:
        pass
    sizerHoriz.Add(bmp, 0, wx.ALL, Style.espace(2))

    # Texte 1
    texte1 = _(u"Bonjour")
    label1 = wx.StaticText(panel, -1, texte1, style=wx.ALIGN_CENTER)
    label1.SetFont(Style.police("h5"))
    label1.SetForegroundColour(texte_secondaire)
    label1.SetBackgroundColour(fond)
    sizerTexte.Add(label1, 1, wx.TOP | wx.EXPAND, Style.espace(10))

    # Texte 2
    texte2 = prenom
    label2 = wx.StaticText(panel, -1, texte2, style=wx.ALIGN_CENTER)
    label2.SetFont(Style.police("h2"))
    label2.SetForegroundColour(texte_principal)
    label2.SetBackgroundColour(fond)
    sizerTexte.Add(label2, 1, wx.EXPAND)

    sizerHoriz.Add(sizerTexte, 1, wx.EXPAND)
    sizer.Add(sizerHoriz, 0, wx.EXPAND)
    panel.SetSizer(sizer)
    panel.Layout()

    tb.AddPanel(panel)
    tb.Play()


if __name__ == '__main__':
    app = wx.App(0)
    ToasterUtilisateur(None)
    app.MainLoop()
