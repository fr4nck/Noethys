#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:        (c) 2010-15 Ivan LUCAS
# Licence:          Licence GNU GPL
#------------------------------------------------------------------------

import os
import wx
import PIL.Image as Image
import PIL.ImageOps as ImageOps

import Chemins
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics


def PILtoWx(image):
    largeur, hauteur = image.size
    if 'phoenix' in wx.PlatformInfo:
        imagewx = wx.Image(largeur, hauteur)
        imagewx.SetData(image.convert("RGB").tobytes())
        imagewx.SetAlpha(image.convert("RGBA").tobytes()[3::4])
    else:
        imagewx = wx.EmptyImage(largeur, hauteur)
        imagewx.SetData(image.convert("RGB").tobytes())
        imagewx.SetAlphaData(image.convert("RGBA").tobytes()[3::4])
    return imagewx


class CTRL(wx.Button):
    """Bouton d'action commun Noethys, natif et DPI-aware.

    ``cheminImage`` reste compatible avec les écrans historiques. Les écrans
    migrés utilisent ``iconeFluent`` explicitement, sans substitution globale.
    """

    def __init__(self, parent, id=-1, texte="", cheminImage=None, tailleImage=(20, 20),
                 margesImage=(4, 0, 0, 0), positionImage=wx.LEFT, margesTexte=(0, 1),
                 iconeFluent=None, roleIcone="on_surface"):
        wx.Button.__init__(self, parent, id=id, label=texte)
        self.parent = parent
        self.texte = texte
        self.cheminImage = cheminImage
        self.tailleImage = tailleImage
        self.margesImage = margesImage
        self.positionImage = positionImage
        self.margesTexte = margesTexte
        self.iconeFluent = iconeFluent
        self.roleIcone = roleIcone

        try:
            self._fond_natif = self.GetBackgroundColour()
            self._texte_natif = self.GetForegroundColour()
        except Exception:
            self._fond_natif = None
            self._texte_natif = None
        self._survole = False
        self._presse = False

        self.Bind(wx.EVT_ENTER_WINDOW, self._OnEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self._OnLeave)
        self.Bind(wx.EVT_SET_FOCUS, self._OnFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self._OnFocus)
        self.Bind(wx.EVT_LEFT_DOWN, self._OnPress)
        self.Bind(wx.EVT_LEFT_UP, self._OnRelease)
        self.MAJ()

    def _TailleImage(self):
        try:
            largeur, hauteur = self.tailleImage
        except Exception:
            largeur = hauteur = 20
        try:
            facteur = max(1.0, UTILS_UIMetrics.get_scale())
        except Exception:
            facteur = 1.0
        return (max(12, int(round(float(largeur) * facteur))),
                max(12, int(round(float(hauteur) * facteur))))

    def _BitmapFluent(self):
        if not self.iconeFluent:
            return None
        try:
            from Utils import UTILS_FluentIcons
            largeur, hauteur = self._TailleImage()
            return UTILS_FluentIcons.GetBitmap(self.iconeFluent, taille=max(largeur, hauteur), role=self.roleIcone)
        except Exception:
            return None

    def _BitmapHistorique(self):
        if self.cheminImage in ("", None):
            return wx.NullBitmap
        chemin = self.cheminImage
        if not os.path.isabs(chemin):
            chemin = Chemins.GetStaticPath(chemin)
        try:
            img = Image.open(chemin).convert("RGBA")
            try:
                img = img.resize(self._TailleImage(), Image.Resampling.LANCZOS)
            except AttributeError:
                img = img.resize(self._TailleImage(), Image.LANCZOS)
            img = ImageOps.expand(img, border=self.margesImage)
            return PILtoWx(img).ConvertToBitmap()
        except Exception:
            return wx.NullBitmap

    def MAJ(self):
        bitmap = self._BitmapFluent()
        if bitmap is None or not getattr(bitmap, "IsOk", lambda: False)():
            bitmap = self._BitmapHistorique()
        try:
            self.SetBitmap(bitmap, self.positionImage)
            if bitmap is not None and bitmap.IsOk():
                self.SetBitmapMargins(self.margesTexte)
        except Exception:
            pass

        try:
            police = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
            facteur = UTILS_Interface.GetTailleTexte() / 100.0
            police.SetPointSize(max(8, int(round(police.GetPointSize() * facteur))))
            self.SetFont(police)
        except Exception:
            pass

        try:
            UTILS_Interface.AppliquerAffichage(self, recursif=False)
        except Exception:
            pass

        try:
            cible = UTILS_UIMetrics.action_target("standard")
            self.SetMinSize((max(cible, self.GetBestSize().GetWidth()), cible))
        except Exception:
            pass

        self._AppliquerEtat()
        try:
            self.InvalidateBestSize()
        except Exception:
            pass
        try:
            parent = self.GetParent()
            if parent is not None:
                parent.Layout()
        except Exception:
            pass

    def _AppliquerEtat(self):
        sombre = UTILS_Interface.EstSombre()
        if not sombre:
            try:
                if self._fond_natif is not None and self._fond_natif.IsOk():
                    self.SetBackgroundColour(self._fond_natif)
                if self._texte_natif is not None and self._texte_natif.IsOk():
                    self.SetForegroundColour(self._texte_natif)
                self.Refresh()
            except Exception:
                pass
            return

        try:
            actif = self.IsEnabled()
        except Exception:
            actif = True
        if not actif:
            fond = UTILS_Interface.GetCouleurRole("disabled", sombre=True)
            try:
                texte = UTILS_Interface.GetCouleurRole("disabled_text", sombre=True)
            except Exception:
                texte = UTILS_Interface.GetCouleurRole("on_surface_variant", sombre=True)
        elif self._presse:
            etat = UTILS_Interface.GetEtatCouleurs("pressed", sombre=True)
            fond, texte = etat["background"], etat["foreground"]
        elif self._survole:
            fond = UTILS_Interface.GetCouleurRole("surface_container_highest", sombre=True)
            texte = UTILS_Interface.GetCouleurRole("on_surface", sombre=True)
        else:
            fond = UTILS_Interface.GetCouleurRole("surface_container_high", sombre=True)
            texte = UTILS_Interface.GetCouleurRole("on_surface", sombre=True)
        try:
            self.SetBackgroundColour(fond)
            self.SetForegroundColour(texte)
            self.Refresh()
        except Exception:
            pass

    def _OnEnter(self, event):
        self._survole = True
        self._AppliquerEtat()
        event.Skip()

    def _OnLeave(self, event):
        self._survole = False
        self._presse = False
        self._AppliquerEtat()
        event.Skip()

    def _OnFocus(self, event):
        self._AppliquerEtat()
        event.Skip()

    def _OnPress(self, event):
        self._presse = True
        self._AppliquerEtat()
        event.Skip()

    def _OnRelease(self, event):
        self._presse = False
        self._AppliquerEtat()
        event.Skip()

    def Enable(self, enable=True):
        resultat = wx.Button.Enable(self, enable)
        self._AppliquerEtat()
        return resultat

    def Disable(self):
        return self.Enable(False)

    def SetImage(self, cheminImage=""):
        self.iconeFluent = None
        self.cheminImage = cheminImage
        self.MAJ()

    def SetIconeFluent(self, nom="", role="on_surface"):
        self.cheminImage = None
        self.iconeFluent = nom
        self.roleIcone = role
        self.MAJ()

    def SetTexte(self, texte=""):
        self.texte = texte
        self.SetLabel(texte)
        self.MAJ()

    def SetImageEtTexte(self, cheminImage="", texte=""):
        self.iconeFluent = None
        self.cheminImage = cheminImage
        self.texte = texte
        self.SetLabel(texte)
        self.MAJ()

    def SetIconeEtTexte(self, iconeFluent="", texte="", role="on_surface"):
        self.cheminImage = None
        self.iconeFluent = iconeFluent
        self.roleIcone = role
        self.texte = texte
        self.SetLabel(texte)
        self.MAJ()


if __name__ == '__main__':
    app = wx.App(0)
    frame = wx.Frame(None, -1, "Bouton Noethys", size=(480, 180))
    panel = wx.Panel(frame)
    bouton = CTRL(panel, texte="Paramètres", iconeFluent="settings", tailleImage=(24, 24))
    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(bouton, 0, wx.ALL, UTILS_UIMetrics.spacing(4))
    panel.SetSizer(sizer)
    frame.Show()
    app.MainLoop()
