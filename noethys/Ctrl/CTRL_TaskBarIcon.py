#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-17 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import Chemins
import wx

from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _

try:
    from wx import TaskBarIcon as TaskBarIcon
except Exception:
    from wx.adv import TaskBarIcon as TaskBarIcon


class CustomTaskBarIcon():
    def __init__(self, parent=None):
        self.tbicon = TaskBarIcon()

        # Binds
        # wx.EVT_TASKBAR_LEFT_DCLICK(self.tbicon, self.OnTaskBarLeftDClick)
        # wx.EVT_TASKBAR_RIGHT_UP(self.tbicon, self.OnTaskBarRightClick)

    def Cacher(self):
        try:
            self.tbicon.RemoveIcon()
        except Exception:
            pass

    def Detruire(self):
        try:
            self.tbicon.Destroy()
        except Exception:
            pass

    def Connecthys(self, nbre=None, texte=""):
        if nbre not in (None, 0):
            chemin_logo = Chemins.GetStaticPath("Images/16x16/Nomadhys.png")
            bmp = wx.Bitmap(chemin_logo, wx.BITMAP_TYPE_ANY)
            bmp = self.AjouteTexteImage(bmp, str(nbre), taille_police=6)
            self.SetIcone(bmp=bmp, texte=texte)
        else:
            self.Cacher()

    def SetIcone(self, bmp=None, texte=""):
        if 'phoenix' in wx.PlatformInfo:
            icon = wx.Icon()
        else:
            icon = wx.EmptyIcon()
        icon.CopyFromBitmap(bmp)
        self.tbicon.SetIcon(icon, texte)

    def _PoliceBadge(self, taille_police):
        """Police compacte dérivée de la typographie Repens."""
        try:
            facteur = max(0.55, float(taille_police) / 9.0)
        except Exception:
            facteur = 1.0
        return Style.police("caption", bold=True, scale=facteur)

    def AjouteTexteImage(self, image=None, texte="", alignement="droite-bas", padding=0, taille_police=9):
        """Ajoute un badge sémantique sur une image bitmap."""
        largeurImage, hauteurImage = image.GetSize()
        if 'phoenix' in wx.PlatformInfo:
            bmp = wx.Bitmap(largeurImage, hauteurImage)
        else:
            bmp = wx.EmptyBitmap(largeurImage, hauteurImage)
        mdc = wx.MemoryDC(bmp)
        dc = wx.GCDC(mdc)

        # Le noir reste uniquement la clé de transparence historique du bitmap.
        mdc.SetBackground(wx.Brush("black"))
        mdc.Clear()

        dc.SetBrush(wx.Brush(Style.couleur("danger")))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetFont(self._PoliceBadge(taille_police))
        dc.SetTextForeground(Style.couleur("danger_text"))

        largeurTexte, hauteurTexte = dc.GetTextExtent(texte)
        mdc.DrawBitmap(image, 0, 0)

        hauteurRond = max(1, int(round(hauteurTexte + padding * 2)))
        largeurRond = max(
            hauteurRond,
            int(round(largeurTexte + padding * 2 + hauteurRond / 2.0)),
        )

        xRond = 1 if "gauche" in alignement else max(0, largeurImage - largeurRond - 1)
        yRond = 1 if "haut" in alignement else max(0, hauteurImage - hauteurRond - 1)
        rect = wx.Rect(int(xRond), int(yRond), int(largeurRond), int(hauteurRond))
        rayon = max(1, int(round(hauteurRond / 2.0)))

        if 'phoenix' in wx.PlatformInfo:
            dc.DrawRoundedRectangle(rect, rayon)
        else:
            dc.DrawRoundedRectangleRect(rect, rayon)

        xTexte = int(round(xRond + largeurRond / 2.0 - largeurTexte / 2.0))
        yTexte = int(round(yRond + hauteurRond / 2.0 - hauteurTexte / 2.0 - 1))
        dc.DrawText(texte, xTexte, yTexte)

        mdc.SelectObject(wx.NullBitmap)
        bmp.SetMaskColour("black")
        return bmp


if __name__ == u"__main__":
    app = wx.App(0)
    taskBarIcon = CustomTaskBarIcon()
    taskBarIcon.Connecthys(2, "2 demandes")
    app.MainLoop()
