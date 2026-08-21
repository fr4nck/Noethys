#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import wx
import six

from Utils import UTILS_Adaptations
from Utils import UTILS_IconesRepens
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


def ChargeImage(fichier):
    """Charge un fichier image dans un objet wx.Image."""
    return wx.Image(fichier, wx.BITMAP_TYPE_ANY)


def wxtopil(image):
    """Convertit une wx.Image vers une image PIL lorsque PIL est fourni par l'appelant."""
    data = image.GetData()
    if 'phoenix' in wx.PlatformInfo:
        data = bytes(data)
    pil = Image.new('RGB', (image.GetWidth(), image.GetHeight()))
    pil.paste(pil.frombytes(data), (10, 10))
    return pil


def piltowx(image):
    """Convertit une image PIL vers wx.Image."""
    largeur, hauteur = image.size
    imagewx = wx.EmptyImage(largeur, hauteur)
    imagewx.SetData(image.tobytes('raw', 'RGB'))
    imagewx.SetAlphaData(image.convert("RGBA").tobytes()[3::4])
    return imagewx


def _TailleAffichage(size):
    if size in (None, wx.DefaultSize):
        return wx.DefaultSize
    try:
        largeur, hauteur = size
        largeur = Style.px(largeur) if largeur > 0 else largeur
        hauteur = Style.px(hauteur) if hauteur > 0 else hauteur
        return (largeur, hauteur)
    except Exception:
        return size


class CTRL(wx.StaticBitmap):
    """Image/logo éditable avec géométrie, surface et menus pilotés par Repens."""

    def __init__(self, parent, qualite=100, couleurFond=None, tailleMaxi=1000, size=(83, 83), mode="ecriture", style=wx.BORDER_THEME):
        taille_affichage = _TailleAffichage(size)
        wx.StaticBitmap.__init__(self, parent, id=-1, size=taille_affichage, style=style)
        self.parent = parent
        self.qualite = qualite
        self.couleurFond = couleurFond
        self.tailleMaxi = tailleMaxi
        self.estModifie = False
        self.mode = mode
        self.imagewx = None

        if taille_affichage != wx.DefaultSize:
            self.SetMinSize(taille_affichage)
        self._AppliqueFond()
        self.SetToolTip(wx.ToolTip(_(u"Cliquez sur l'image pour accéder aux fonctions")))

        self.Bind(wx.EVT_LEFT_DOWN, self.Menu)
        self.Bind(wx.EVT_RIGHT_DOWN, self.Menu)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def _AppliqueFond(self):
        if self.couleurFond is None:
            self.SetBackgroundColour(Style.couleur("surface_container_lowest"))
        else:
            self.SetBackgroundColour(self.couleurFond)

    def _CouleurFondRGB(self):
        try:
            couleur = self.GetBackgroundColour()
            return couleur.Red(), couleur.Green(), couleur.Blue()
        except Exception:
            return 255, 255, 255

    def _BitmapMenu(self, nom, role="on_surface"):
        try:
            bitmap = UTILS_IconesRepens.GetBitmap(
                nom,
                taille=Style.taille_icone("compact"),
                role=role,
            )
            if bitmap is not None and bitmap.IsOk():
                return bitmap
        except Exception:
            pass
        return wx.NullBitmap

    def OnSize(self, event):
        self.MAJ()
        event.Skip()

    def Menu(self, event):
        """Ouvre le menu contextuel de l'image."""
        menuPop = UTILS_Adaptations.Menu()

        if self.mode == "ecriture":
            item = wx.MenuItem(menuPop, 10, _(u"Importer une image"))
            bmp = self._BitmapMenu("add")
            if bmp.IsOk():
                item.SetBitmap(bmp)
            menuPop.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.Menu_Ajouter, id=10)

            item = wx.MenuItem(menuPop, 30, _(u"Supprimer"))
            bmp = self._BitmapMenu("delete", role="danger_text")
            if bmp.IsOk():
                item.SetBitmap(bmp)
            menuPop.AppendItem(item)
            self.Bind(wx.EVT_MENU, self.Menu_Supprimer, id=30)
            if self.imagewx is None:
                item.Enable(False)

        item = wx.MenuItem(menuPop, 40, _(u"Visualiser"))
        bmp = self._BitmapMenu("search")
        if bmp.IsOk():
            item.SetBitmap(bmp)
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Visualiser, id=40)
        if self.imagewx is None:
            item.Enable(False)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Menu_Ajouter(self, event):
        self.Ajouter()

    def Menu_Supprimer(self, event):
        self.Supprimer()

    def Ajouter(self, event=None):
        """Importe une image."""
        wildcard = "Toutes les images (*.bmp; *.gif; *.jpg; *.png)|*.bmp;*.gif;*.jpg;*.png|Image JPEG (*.jpg)|*.jpg|Image PNG (*.png)|*.png|Image GIF (*.gif)|*.gif|Tous les fichiers (*.*)|*.*"
        cheminDefaut = wx.StandardPaths.Get().GetDocumentsDir()

        dlg = wx.FileDialog(
            self,
            message=_(u"Sélectionnez une image"),
            defaultDir=cheminDefaut,
            defaultFile="",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        try:
            if dlg.ShowModal() != wx.ID_OK:
                return
            nomFichier = dlg.GetPath()
        finally:
            dlg.Destroy()

        img = ChargeImage(nomFichier)
        tailleMaxi = self.tailleMaxi
        largeur, hauteur = img.GetSize()
        if max(largeur, hauteur) > tailleMaxi:
            if largeur > hauteur:
                hauteur = hauteur * tailleMaxi / largeur
                largeur = tailleMaxi
            else:
                largeur = largeur * tailleMaxi / hauteur
                hauteur = tailleMaxi
            img.Rescale(width=int(largeur), height=int(hauteur), quality=wx.IMAGE_QUALITY_HIGH)

        self.imagewx = img
        self.MAJ()
        self.estModifie = True

    def MAJ(self, event=None):
        if self.imagewx is None:
            self.SetBitmap(wx.NullBitmap)
            return
        try:
            img = self.imagewx.Copy()
        except Exception:
            return

        largeurCadre, hauteurCadre = self.GetClientSize()
        if largeurCadre <= 0 or hauteurCadre <= 0:
            largeurCadre, hauteurCadre = self.GetSize()
        if largeurCadre <= 0 or hauteurCadre <= 0:
            return

        largeurImage, hauteurImage = img.GetSize()
        if largeurImage <= 0 or hauteurImage <= 0:
            return
        ratioImage = 1.0 * largeurImage / hauteurImage
        espace = Style.espace(2)

        hauteurImage = max(1, hauteurCadre - espace)
        largeurImage = hauteurImage * ratioImage
        if largeurImage > largeurCadre - espace:
            largeurImage = max(1, largeurCadre - espace)
            hauteurImage = largeurImage / ratioImage

        largeurImage = max(1, int(round(largeurImage)))
        hauteurImage = max(1, int(round(hauteurImage)))
        img.Rescale(width=largeurImage, height=hauteurImage, quality=wx.IMAGE_QUALITY_HIGH)
        position = (
            int(round((largeurCadre - largeurImage) / 2.0)),
            int(round((hauteurCadre - hauteurImage) / 2.0)),
        )
        rouge, vert, bleu = self._CouleurFondRGB()
        img.Resize((largeurCadre, hauteurCadre), position, rouge, vert, bleu)

        if 'phoenix' in wx.PlatformInfo:
            bmp = wx.Bitmap(img)
        else:
            bmp = wx.BitmapFromImage(img)
        self.SetBitmap(bmp)

    def Supprimer(self, event=None):
        if self.imagewx is None:
            dlg = wx.MessageDialog(self, _(u"Il n'y a aucune image à supprimer !"), _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        dlg = wx.MessageDialog(self, _(u"Confirmez-vous la suppression de cette image ?"), _(u"Suppression"), wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION)
        reponse = dlg.ShowModal()
        dlg.Destroy()
        if reponse != wx.ID_YES:
            return

        self.imagewx = None
        self.MAJ()
        self.estModifie = True

    def ChargeFromBuffer(self, buffer=None):
        """Charge l'image à partir d'un buffer."""
        if buffer is None:
            self.imagewx = None
        else:
            io = six.BytesIO(buffer)
            if 'phoenix' in wx.PlatformInfo:
                self.imagewx = wx.Image(io, wx.BITMAP_TYPE_PNG)
            else:
                self.imagewx = wx.ImageFromStream(io, wx.BITMAP_TYPE_PNG)
        self.MAJ()

    def GetBuffer(self):
        """Récupère le buffer de l'image."""
        if self.imagewx is None:
            return None
        buffer = six.BytesIO()
        if 'phoenix' in wx.PlatformInfo:
            self.imagewx.SaveFile(buffer, wx.BITMAP_TYPE_PNG)
        else:
            self.imagewx.SaveStream(buffer, wx.BITMAP_TYPE_PNG)
        buffer.seek(0)
        return buffer.read()

    def Visualiser(self, event=None):
        if self.imagewx is None:
            dlg = wx.MessageDialog(self, _(u"Il n'y a aucune image à visualiser !"), _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        from Dlg import DLG_Visualiseur_image
        dlg = DLG_Visualiseur_image.MyFrame(None, imgWX=self.imagewx)
        dlg.Show(True)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(panel, "surface")
        self.ctrl = CTRL(panel, size=(83, 83))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, Style.espace(1))
        panel.SetSizer(sizer)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(panel, 1, wx.EXPAND)
        self.SetSizer(principal)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(200, 200))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
