#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import base64
import os

import six
import wx
from PIL import Image

import Chemins
import GestionDB
from Utils import UTILS_Adaptations
from Utils import UTILS_Fichiers
from Utils import UTILS_IconesRepens
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils import UTILS_Utilisateurs
from Utils.UTILS_Traduction import _


ID_IMPORTER = 10
ID_CAPTURER = 20
ID_SUPPRIMER = 30


def GetPhoto(IDindividu=None, nomFichier=None, taillePhoto=(128, 128), qualite=wx.IMAGE_QUALITY_HIGH):
    """Retourne la photo d'un individu sans modifier le format stocké."""
    if IDindividu is not None:
        DB = GestionDB.DB(suffixe="PHOTOS")
        if DB.echec != 1:
            req = "SELECT IDphoto, photo FROM photos WHERE IDindividu=%d;" % IDindividu
            DB.ExecuterReq(req)
            listeDonnees = DB.ResultatReq()
            DB.Close()
            if listeDonnees:
                IDphoto, bufferPhoto = listeDonnees[0]
                io = six.BytesIO(bufferPhoto)
                if 'phoenix' in wx.PlatformInfo:
                    img = wx.Image(io, wx.BITMAP_TYPE_JPEG)
                else:
                    img = wx.ImageFromStream(io, wx.BITMAP_TYPE_JPEG)
                img = img.Rescale(width=taillePhoto[0], height=taillePhoto[1], quality=qualite)
                return IDphoto, img.ConvertToBitmap()

    if nomFichier is not None and os.path.isfile(nomFichier):
        bmp = wx.Bitmap(nomFichier, wx.BITMAP_TYPE_ANY)
        img = bmp.ConvertToImage()
        img = img.Rescale(width=taillePhoto[0], height=taillePhoto[1], quality=qualite)
        return None, img.ConvertToBitmap()

    return None, None


def GetPhotos(listeIndividus=None, taillePhoto=None, qualite=wx.IMAGE_QUALITY_HIGH):
    """Retourne plusieurs photos. Entrée : ``[(IDindividu, image_defaut), ...]``."""
    listeIndividus = listeIndividus or []
    if not listeIndividus:
        return {}

    dictImagesDefaut = {}
    listeIDindividus = []
    for IDindividu, nomFichier in listeIndividus:
        listeIDindividus.append(IDindividu)
        if nomFichier is not None and nomFichier not in dictImagesDefaut and os.path.isfile(nomFichier):
            bmp = wx.Bitmap(nomFichier, wx.BITMAP_TYPE_ANY)
            if taillePhoto is not None:
                img = bmp.ConvertToImage()
                img = img.Rescale(width=taillePhoto[0], height=taillePhoto[1], quality=qualite)
                bmp = img.ConvertToBitmap()
            dictImagesDefaut[nomFichier] = bmp

    dictPhotosDB = {}
    DB = GestionDB.DB(suffixe="PHOTOS")
    if DB.echec == 0:
        if len(listeIDindividus) == 1:
            condition = "(%d)" % listeIDindividus[0]
        else:
            condition = str(tuple(listeIDindividus))
        req = "SELECT IDphoto, IDindividu, photo FROM photos WHERE IDindividu IN %s;" % condition
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()
        for IDphoto, IDindividu, bufferPhoto in listeDonnees:
            dictPhotosDB[IDindividu] = {"IDphoto": IDphoto, "bufferPhoto": bufferPhoto}

    dictPhotos = {}
    for IDindividu, nomFichier in listeIndividus:
        if IDindividu in dictPhotosDB:
            IDphoto = dictPhotosDB[IDindividu]["IDphoto"]
            bufferPhoto = dictPhotosDB[IDindividu]["bufferPhoto"]
            io = six.BytesIO(bufferPhoto)
            if 'phoenix' in wx.PlatformInfo:
                img = wx.Image(io, wx.BITMAP_TYPE_JPEG)
            else:
                img = wx.ImageFromStream(io, wx.BITMAP_TYPE_JPEG)
            if taillePhoto is not None:
                img = img.Rescale(width=taillePhoto[0], height=taillePhoto[1], quality=qualite)
            bmp = img.ConvertToBitmap()
        else:
            IDphoto = None
            bmp = dictImagesDefaut.get(nomFichier)
        dictPhotos[IDindividu] = {"bmp": bmp, "IDphoto": IDphoto}
    return dictPhotos


class CTRL_Photo(wx.StaticBitmap):
    """Photo individuelle : moteur historique, chrome Repens.

    Les opérations métier (base PHOTOS, import, recadrage, webcam et base64)
    restent inchangées. Seule la présentation et la construction du menu sont
    modernisées.
    """

    def __init__(self, parent, IDindividu=None, style=0, modeBase64=False):
        wx.StaticBitmap.__init__(self, parent, id=-1, style=style)
        self.parent = parent
        self.IDphoto = None
        self.IDindividu = IDindividu
        self.modeBase64 = modeBase64
        self.image_base64 = None

        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_low"))
        self.SetToolTip(wx.ToolTip(_(u"Cliquez sur la photo pour l'importer, la capturer ou la supprimer.")))
        self.SetMinSize((UTILS_UIMetrics.px(128), UTILS_UIMetrics.px(128)))

        self.Bind(wx.EVT_LEFT_DOWN, self.MenuPhoto)
        self.Bind(wx.EVT_RIGHT_DOWN, self.MenuPhoto)
        self.Bind(wx.EVT_MENU, self.Menu_Ajouter, id=ID_IMPORTER)
        self.Bind(wx.EVT_MENU, self.Menu_Capturer, id=ID_CAPTURER)
        self.Bind(wx.EVT_MENU, self.Menu_Supprimer, id=ID_SUPPRIMER)

    def _BitmapMenu(self, nom, role="on_surface"):
        try:
            bitmap = UTILS_IconesRepens.GetBitmap(
                nom,
                taille=UTILS_UIMetrics.icon_size("compact"),
                role=role,
            )
            if bitmap is not None and bitmap.IsOk():
                return bitmap
        except Exception:
            pass
        return wx.NullBitmap

    def _BitmapVide(self, taille=(128, 128)):
        largeur = max(1, int(taille[0]))
        hauteur = max(1, int(taille[1]))
        bitmap = wx.Bitmap(largeur, hauteur)
        dc = wx.MemoryDC(bitmap)
        try:
            dc.SetBackground(wx.Brush(UTILS_Interface.GetCouleurRole("surface_container_low")))
            dc.Clear()
        finally:
            dc.SelectObject(wx.NullBitmap)
        return bitmap

    def GetImageBase64(self):
        return self.image_base64

    def SetPhoto(self, IDindividu=None, nomFichier=None, taillePhoto=(128, 128), qualite=wx.IMAGE_QUALITY_HIGH, imgbase64=None):
        if imgbase64 is not None:
            self.image_base64 = imgbase64
            io = six.BytesIO(base64.b64decode(imgbase64))
            if 'phoenix' in wx.PlatformInfo:
                img = wx.Image(io, wx.BITMAP_TYPE_JPEG)
            else:
                img = wx.ImageFromStream(io, wx.BITMAP_TYPE_JPEG)
            self.SetBitmap(img.ConvertToBitmap())
            self.Refresh()
            return

        self.IDindividu = IDindividu
        IDphoto, bmp = GetPhoto(IDindividu, nomFichier, taillePhoto, qualite)
        if bmp is not None:
            self.SetBitmap(bmp)
            self.IDphoto = IDphoto
            self.Refresh()

    def GetIDphoto(self):
        return self.IDphoto

    def MenuPhoto(self, event):
        if not UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("individus_photo", "modifier"):
            return

        menuPop = UTILS_Adaptations.Menu()

        item_importer = wx.MenuItem(menuPop, ID_IMPORTER, _(u"Importer une photo…"))
        bitmap = self._BitmapMenu("add")
        if bitmap.IsOk():
            item_importer.SetBitmap(bitmap)
        menuPop.AppendItem(item_importer)

        item_capturer = wx.MenuItem(menuPop, ID_CAPTURER, _(u"Capturer avec la webcam…"))
        bitmap = self._BitmapMenu("camera")
        if bitmap.IsOk():
            item_capturer.SetBitmap(bitmap)
        menuPop.AppendItem(item_capturer)

        menuPop.AppendSeparator()
        item_supprimer = wx.MenuItem(menuPop, ID_SUPPRIMER, _(u"Supprimer la photo"))
        bitmap = self._BitmapMenu("delete", role="danger_text")
        if bitmap.IsOk():
            item_supprimer.SetBitmap(bitmap)
        menuPop.AppendItem(item_supprimer)
        if self.IDphoto is None and self.modeBase64 is False:
            item_supprimer.Enable(False)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Menu_Ajouter(self, event):
        self.Ajoute_image()

    def Ajoute_image(self):
        """Permet la sélection et le retouchage d'une photo pour la personne."""
        wildcard = (
            "Toutes les images|*.bmp;*.gif;*.jpg;*.png|"
            "Image JPEG (*.jpg)|*.jpg|"
            "Image PNG (*.png)|*.png|"
            "Image GIF (*.gif)|*.gif|"
            "Tous les fichiers (*.*)|*.*"
        )
        cheminDefaut = wx.StandardPaths.Get().GetDocumentsDir()
        dlg = wx.FileDialog(
            self,
            message=_(u"Choisissez une photo"),
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
        self.ChargeEditeurPhoto(nomFichierLong)

    def ChargeEditeurPhoto(self, nomFichierLong="", listeVisages=None):
        from Dlg import DLG_Editeur_photo
        dlg = DLG_Editeur_photo.Dialog(
            None,
            image=nomFichierLong,
            tailleCadre=(128, 128),
            listeVisages=listeVisages or [],
        )
        try:
            if dlg.ShowModal() != wx.ID_OK:
                return
            buffer = dlg.GetBuffer()
            bmp = buffer.read()
        finally:
            dlg.Destroy()

        if self.modeBase64 is True:
            imgbase64 = base64.b64encode(bmp)
            self.SetPhoto(imgbase64=imgbase64)
            return

        DB = GestionDB.DB(suffixe="PHOTOS")
        if DB.echec != 1:
            req = "SELECT IDphoto, photo FROM photos WHERE IDindividu=%d;" % self.IDindividu
            DB.ExecuterReq(req)
            listePhotos = DB.ResultatReq()
            if not listePhotos:
                DB.InsertPhoto(IDindividu=self.IDindividu, blobPhoto=bmp)
            else:
                DB.MAJPhoto(IDphoto=listePhotos[0][0], IDindividu=self.IDindividu, blobPhoto=bmp)
            DB.Close()
        self.SetPhoto(self.IDindividu)

    def Menu_Capturer(self, event):
        self.Capture_image()

    def Capture_image(self):
        """Capture la photo à partir d'une caméra."""
        from Dlg import DLG_Capture_video_opencv_2 as dlg_module
        image = None
        listeVisages = []
        dlg = dlg_module.Dialog(self)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                image = dlg.GetImage()
                listeVisages = dlg.GetListeVisages()
        finally:
            dlg.Destroy()
        if image is not None:
            fichier = UTILS_Fichiers.GetRepTemp(fichier="capture_video.jpg")
            image.SaveFile(fichier, type=wx.BITMAP_TYPE_JPEG)
            self.ChargeEditeurPhoto(fichier, listeVisages=listeVisages)

    def Menu_Supprimer(self, event):
        dlgConfirm = wx.MessageDialog(
            self,
            _(u"Souhaitez-vous vraiment supprimer cette photo ?"),
            _(u"Confirmation de suppression"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        reponse = dlgConfirm.ShowModal()
        dlgConfirm.Destroy()
        if reponse != wx.ID_YES:
            return

        if self.modeBase64 is True:
            self.image_base64 = None
            self.IDphoto = None
            self.SetBitmap(self._BitmapVide())
            self.Refresh()
            return

        DB = GestionDB.DB(suffixe="PHOTOS")
        DB.ReqDEL("photos", "IDindividu", self.IDindividu)
        DB.Close()
        self.IDphoto = None

        DB = GestionDB.DB()
        req = "SELECT IDcivilite FROM individus WHERE IDindividu=%d;" % self.IDindividu
        DB.ExecuterReq(req)
        resultats = DB.ResultatReq()
        DB.Close()
        if not resultats or resultats[0][0] is None:
            self.SetBitmap(self._BitmapVide())
            self.Refresh()
            return

        IDcivilite = resultats[0][0]
        nomFichier = None
        from Data import DATA_Civilites as Civilites
        for rubrique, civilites in Civilites.LISTE_CIVILITES:
            for civilite in civilites:
                if civilite[0] == IDcivilite:
                    nomFichier = civilite[3]
                    break
            if nomFichier is not None:
                break
        if nomFichier is None:
            self.SetBitmap(self._BitmapVide())
            self.Refresh()
            return

        nomFichier = Chemins.GetStaticPath("Images/128x128/%s" % nomFichier)
        self.SetPhoto(self.IDindividu, nomFichier)

    def Menu_Imprimer(self, event):
        """Impression historique de la photo, conservée pour compatibilité."""
        DB = GestionDB.DB()
        req = "SELECT IDpersonne, nom, prenom FROM personnes WHERE IDpersonne=%d;" % self.IDpersonne
        DB.executerReq(req)
        donnees = DB.resultatReq()[0]
        DB.close()
        import Impression_photo
        frame = Impression_photo.MyFrame(None, listePersonnes=[[self.IDpersonne, donnees[1], donnees[2], None]])
        frame.Show()

    def wxtopil(self, image):
        """Convertit wx.Image vers PIL.Image."""
        data = image.GetData()
        if 'phoenix' in wx.PlatformInfo:
            data = bytes(data)
        pil = Image.new('RGB', (image.GetWidth(), image.GetHeight()))
        pil.frombytes(data)
        return pil


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL | wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = CTRL_Photo(panel, modeBase64=True)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(1))
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
