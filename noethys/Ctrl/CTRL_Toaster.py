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
from Utils import UTILS_Adaptations
from Utils import UTILS_Interface
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import wx.lib.agw.toasterbox as Toaster


def _PoliceSysteme(coefficient=1.0, gras=False):
    """Police du toaster dérivée de la police native de la plateforme."""
    try:
        police = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
        if hasattr(police, "GetFractionalPointSize") and hasattr(police, "SetFractionalPointSize"):
            police.SetFractionalPointSize(max(5.0, police.GetFractionalPointSize() * coefficient))
        else:
            police.SetPointSize(max(5, int(round(police.GetPointSize() * coefficient))))
        if gras:
            police.SetWeight(wx.FONTWEIGHT_BOLD)
        return police
    except Exception:
        return wx.NullFont


def ToasterUtilisateur(parent, titre=u"", prenom=_(u"Philippe"), nomImage="Femme", taille=(200, 100), couleurFond=None):
    """ Affiche une boîte de dialogue temporaire """
    sombre = UTILS_Interface.EstSombre()

    # Si un appelant fournit une couleur historique/personnalisée, elle garde
    # la priorité. Sinon le toaster suit automatiquement le design system.
    if couleurFond is None:
        fond = UTILS_Interface.GetCouleurRole("surface_container_highest", sombre=sombre)
        texte_principal = UTILS_Interface.GetCouleurRole("on_surface", sombre=sombre)
        texte_secondaire = UTILS_Interface.GetCouleurRole("on_surface_variant", sombre=sombre)
    else:
        fond = couleurFond
        # Pour un fond explicite, on conserve une lecture robuste sans deviner
        # l'intention métier de l'appelant.
        texte_principal = wx.WHITE
        texte_secondaire = wx.Colour(210, 210, 210)

    facteur_interface = UTILS_Interface.GetEchelle() / 100.0
    largeur = max(320, int(round(400 * facteur_interface)))
    hauteur = max(132, int(round(148 * facteur_interface)))

    tb = Toaster.ToasterBox(parent, Toaster.TB_COMPLEX, Toaster.TB_DEFAULT_STYLE, Toaster.TB_ONTIME) # TB_CAPTION
    tb.SetTitle(titre)
    tb.SetPopupSize((largeur, hauteur))
    if 'phoenix' in wx.PlatformInfo:
        largeurEcran, hauteurEcran = wx.ScreenDC().GetSize()
    else :
        largeurEcran, hauteurEcran = wx.ScreenDC().GetSizeTuple()
    tb.SetPopupPosition((largeurEcran-largeur-10, hauteurEcran-hauteur-50))
    tb.SetPopupPauseTime(3000)
    tb.SetPopupScrollSpeed(4)
    tb.SetPopupBackgroundColour(fond)
    tb.SetPopupTextColour(texte_principal)

    tbpanel = tb.GetToasterBoxWindow()
    panel = wx.Panel(tbpanel, -1)
    panel.SetBackgroundColour(fond)
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizerHoriz = wx.BoxSizer(wx.HORIZONTAL)
    sizerTexte = wx.BoxSizer(wx.VERTICAL)

    # Image
    bmp = wx.StaticBitmap(panel, -1, wx.Bitmap(Chemins.GetStaticPath("Images/Avatars/128x128/%s.png" % nomImage), wx.BITMAP_TYPE_PNG))
    try:
        bmp.SetBackgroundColour(fond)
    except Exception:
        pass
    sizerHoriz.Add(bmp, 0, wx.ALL, max(6, int(round(10 * facteur_interface))))

    # Texte1
    texte1 = _(u"Bonjour")
    label1 = wx.StaticText(panel, -1, texte1, style=wx.ALIGN_CENTER)
    label1.SetFont(_PoliceSysteme(1.05, gras=True))
    label1.SetForegroundColour(texte_secondaire)
    label1.SetBackgroundColour(fond)
    sizerTexte.Add(label1, 1, wx.TOP | wx.EXPAND, max(24, int(round(40 * facteur_interface))))

    # Texte 2
    texte2 = prenom
    label2 = wx.StaticText(panel, -1, texte2, style=wx.ALIGN_CENTER)
    label2.SetFont(_PoliceSysteme(1.45, gras=True))
    label2.SetForegroundColour(texte_principal)
    label2.SetBackgroundColour(fond)
    sizerTexte.Add(label2, 1, wx.TOP | wx.EXPAND, 0)

    sizerHoriz.Add(sizerTexte, 1, wx.EXPAND, 0)
    sizer.Add(sizerHoriz, 0, wx.EXPAND)
    panel.SetSizer(sizer)
    panel.Layout()

    # Le moteur commun applique ici la taille de texte indépendante choisie par
    # l'utilisateur, sans changer le contrat métier ni le contenu du toaster.
    try:
        UTILS_Interface.AppliquerAffichage(panel, recursif=True)
        panel.SetBackgroundColour(fond)
        label1.SetBackgroundColour(fond)
        label2.SetBackgroundColour(fond)
    except Exception:
        pass

    tb.AddPanel(panel)
    tb.Play()



if __name__ == '__main__':
    app = wx.App(0)
    ToasterUtilisateur(None)
    app.MainLoop()
