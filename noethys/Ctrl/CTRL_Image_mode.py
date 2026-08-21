#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:          Licence GNU GPL
#-----------------------------------------------------------

import os

import six
import wx

import Chemins
import GestionDB
from Ctrl import CTRL_ActionRepens
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


TAILLE_IMAGE = (132, 72)


class CTRL(wx.StaticBitmap):
    """Image métier avec rendu DPI-aware et surface sémantique.

    ``tailleImage`` reste le format logique/source attendu par les écrans
    historiques. Le bitmap affiché est, lui, adapté à l'échelle d'interface ;
    aucune donnée enregistrée en base n'est donc modifiée par la modernisation.
    """

    def __init__(self, parent, table="", key="", IDkey=None, imageDefaut=None, tailleImage=TAILLE_IMAGE, style=0):
        self.tailleImageSource = tuple(tailleImage or TAILLE_IMAGE)
        self.tailleImage = self._TailleAffichage(self.tailleImageSource)
        wx.StaticBitmap.__init__(self, parent, id=-1, style=style)
        self.parent = parent

        self.bmpBuffer = None
        self.table = table
        self.key = key
        self.IDkey = IDkey
        self.imageDefaut = imageDefaut
        self.modeDefaut = False

        self.SetMinSize(self.tailleImage)
        self.SetBackgroundColour(Style.couleur("surface_container_low"))
        self.SetToolTip(wx.ToolTip(_(u"Image associée. Utilisez les commandes de l'écran pour la modifier.")))

        bitmap = self.GetPhoto()
        self.SetBitmap(bitmap if bitmap is not None else wx.NullBitmap)

    def _TailleAffichage(self, taille):
        try:
            return (
                max(1, Style.px(taille[0])),
                max(1, Style.px(taille[1])),
            )
        except Exception:
            return tuple(taille)

    def _AdapterBitmap(self, bitmap):
        if bitmap is None or not getattr(bitmap, "IsOk", lambda: False)():
            return wx.NullBitmap
        if bitmap.GetWidth() == self.tailleImage[0] and bitmap.GetHeight() == self.tailleImage[1]:
            return bitmap
        image = bitmap.ConvertToImage().Rescale(
            width=self.tailleImage[0],
            height=self.tailleImage[1],
            quality=wx.IMAGE_QUALITY_HIGH,
        )
        return image.ConvertToBitmap()

    def GetPhoto(self):
        """Récupère l'image enregistrée ou l'image par défaut."""
        if self.IDkey is not None:
            DB = GestionDB.DB()
            req = "SELECT image FROM %s WHERE %s=%d;" % (self.table, self.key, self.IDkey)
            DB.ExecuterReq(req)
            listeDonnees = DB.ResultatReq()
            DB.Close()
            if listeDonnees:
                self.bmpBuffer = listeDonnees[0][0]
                if self.bmpBuffer is not None:
                    io = six.BytesIO(self.bmpBuffer)
                    if 'phoenix' in wx.PlatformInfo:
                        img = wx.Image(io, wx.BITMAP_TYPE_JPEG)
                    else:
                        img = wx.ImageFromStream(io, wx.BITMAP_TYPE_JPEG)
                    img = img.Rescale(
                        width=self.tailleImage[0],
                        height=self.tailleImage[1],
                        quality=wx.IMAGE_QUALITY_HIGH,
                    )
                    self.modeDefaut = False
                    return img.ConvertToBitmap()

        if self.imageDefaut is not None:
            self.bmpBuffer = None
            return self.GetImageDefaut()

        self.bmpBuffer = None
        self.modeDefaut = False
        return wx.NullBitmap

    def GetImageDefaut(self):
        if self.imageDefaut and os.path.isfile(self.imageDefaut):
            bitmap = wx.Bitmap(self.imageDefaut, wx.BITMAP_TYPE_ANY)
            self.modeDefaut = True
            return self._AdapterBitmap(bitmap)
        self.modeDefaut = False
        return wx.NullBitmap

    def Ajouter(self, sauvegarder=True):
        """Permet la sélection et le retouchage d'une image."""
        wildcard = (
            "Toutes les images|*.jpg;*.png;*.gif|"
            "Image JPEG (*.jpg)|*.jpg|"
            "Image PNG (*.png)|*.png|"
            "Image GIF (*.gif)|*.gif|"
            "Tous les fichiers (*.*)|*.*"
        )
        cheminDefaut = wx.StandardPaths.Get().GetDocumentsDir()
        dlg = wx.FileDialog(
            self,
            message=_(u"Choisissez une image"),
            defaultDir=cheminDefaut,
            defaultFile="",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        try:
            if dlg.ShowModal() != wx.ID_OK:
                return
            nomFichierLong = dlg.GetPath()
        finally:
            dlg.Destroy()

        from Dlg import DLG_Editeur_photo
        dlg = DLG_Editeur_photo.Dialog(None, image=nomFichierLong, tailleCadre=self.tailleImageSource)
        try:
            if dlg.ShowModal() != wx.ID_OK:
                return
            buffer = dlg.GetBuffer()
            self.bmpBuffer = buffer.read()
            bitmap = dlg.GetBmp()
        finally:
            dlg.Destroy()

        if sauvegarder is True:
            DB = GestionDB.DB()
            DB.MAJimage(self.table, self.key, self.IDkey, self.bmpBuffer)
            DB.Close()
        self.modeDefaut = False
        self.SetBitmap(self._AdapterBitmap(bitmap))
        self.Refresh()

    def Supprimer(self, sauvegarder=True):
        """Suppression de l'image."""
        if self.modeDefaut is True:
            dlg = wx.MessageDialog(
                self,
                _(u"Aucune image n'est enregistrée !"),
                _(u"Suppression impossible"),
                wx.OK | wx.ICON_EXCLAMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return

        dlgConfirm = wx.MessageDialog(
            self,
            _(u"Souhaitez-vous vraiment supprimer cette image ?"),
            _(u"Confirmation de suppression"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        reponse = dlgConfirm.ShowModal()
        dlgConfirm.Destroy()
        if reponse != wx.ID_YES:
            return

        if sauvegarder is True:
            DB = GestionDB.DB()
            DB.ReqMAJ(self.table, [("image", None)], self.key, self.IDkey)
            DB.Close()

        self.bmpBuffer = None
        bitmap = self.GetImageDefaut()
        self.SetBitmap(bitmap if bitmap is not None else wx.NullBitmap)
        self.Refresh()

    def Sauvegarder(self):
        """Permet de sauvegarder ultérieurement l'image."""
        DB = GestionDB.DB()
        if self.bmpBuffer is not None:
            DB.MAJimage(self.table, self.key, self.IDkey, self.bmpBuffer)
        else:
            DB.ReqMAJ(self.table, [("image", None)], self.key, self.IDkey)
        DB.Close()


class Dialog(wx.Dialog):
    """Petit hôte de démonstration/édition conservé pour compatibilité."""

    def __init__(self, parent, IDmode=None):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.SetTitle(_(u"Image du mode de règlement"))
        Style.appliquer_fenetre(self, "surface")

        self.ctrl_image = CTRL(
            self,
            table="modes_reglements",
            key="IDmode",
            IDkey=IDmode or 1,
            imageDefaut=Chemins.GetStaticPath("Images/Special/Image_non_disponible.png"),
        )
        self.bouton_ajouter_image = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Choisir une image"),
            icone="add",
            variante="secondaire",
            tooltip=_(u"Sélectionner ou remplacer l'image"),
        )
        self.bouton_supprimer_image = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Supprimer"),
            icone="delete",
            variante="danger",
            tooltip=_(u"Supprimer l'image enregistrée"),
        )

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_ajouter_image, 0, wx.RIGHT, Style.espace(1))
        actions.Add(self.bouton_supprimer_image, 0)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(self.ctrl_image, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, Style.espace(3))
        principal.Add(actions, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT, Style.espace(3))
        self.SetSizer(principal)
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.Layout()
        self.CentreOnParent() if parent is not None else self.CentreOnScreen()

        self.Bind(wx.EVT_BUTTON, self.OnAjouterImage, self.bouton_ajouter_image)
        self.Bind(wx.EVT_BUTTON, self.OnSupprimerImage, self.bouton_supprimer_image)

    def OnAjouterImage(self, event):
        self.ctrl_image.Ajouter(sauvegarder=False)

    def OnSupprimerImage(self, event):
        self.ctrl_image.Supprimer(sauvegarder=False)


if __name__ == u"__main__":
    app = wx.App(0)
    dialog_1 = Dialog(None, IDmode=1)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()
