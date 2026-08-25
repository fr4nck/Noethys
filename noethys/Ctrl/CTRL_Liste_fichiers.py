#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------


from Utils.UTILS_Traduction import _
from Utils import UTILS_StyleRepens as Style
import wx
if wx.VERSION < (2, 9, 0, 0):
    from Outils import ultimatelistctrl as ULC
else:
    from wx.lib.agw import ultimatelistctrl as ULC

import os
import six
import datetime
import sqlite3
import GestionDB
from Utils import UTILS_Utilisateurs
from Utils import UTILS_Fichiers


def _taille_image():
    taille = Style.taille_icone("hero")
    return (taille, taille)


def FormatFileSize(size):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0:
            return "%3.2f %s" % (size, x)
        size /= 1024.0


def RecadreImg(img=None):
    tailleImage = _taille_image()
    tailleMaxi = max(tailleImage)
    largeur, hauteur = img.GetSize()
    if max(largeur, hauteur) > tailleMaxi:
        if largeur > hauteur:
            hauteur = int(round(hauteur * tailleMaxi / float(largeur)))
            largeur = tailleMaxi
        else:
            largeur = int(round(largeur * tailleMaxi / float(hauteur)))
            hauteur = tailleMaxi
    img.Rescale(width=int(largeur), height=int(hauteur), quality=wx.IMAGE_QUALITY_HIGH)
    position = (
        int(round((tailleImage[0] / 2.0) - (largeur / 2.0))),
        int(round((tailleImage[1] / 2.0) - (hauteur / 2.0))),
    )
    img.Resize(tailleImage, position, 255, 255, 255)
    return img


class FirstColumnRenderer(object):
    def __init__(self, parent, titre=u"", image=None, description=u""):
        self.parent = parent

        self.normalFont = Style.police("body_emphasis")
        self.smallerFont = Style.police("body_small")
        self.secondaryColour = Style.couleur("on_surface_variant")
        self.primaryColour = Style.couleur("on_surface")

        self.text = titre
        self.icon = image
        self.description = description

    def DrawSubItem(self, dc, rect, line, highlighted, enabled):
        """Dessine le nom et la description d'un fichier."""
        marge = Style.espace(1)
        decalageTexte = Style.espace(2)
        if self.icon is not None:
            bmpWidth, bmpHeight = self.icon.GetWidth(), self.icon.GetHeight()
            dc.DrawBitmap(self.icon, int(rect.x + marge), int(rect.y + (rect.height - bmpHeight) / 2))
        else:
            bmpWidth, bmpHeight = _taille_image()

        dc.SetFont(self.normalFont)
        textWidth, textHeight = dc.GetTextExtent(self.text)
        dc.SetTextForeground(self.primaryColour)
        dc.DrawText(self.text, int(rect.x + bmpWidth + decalageTexte), int(rect.y + (rect.height - textHeight) / 4))

        if not self.description:
            return

        dc.SetFont(self.smallerFont)
        textWidth, textHeight = dc.GetTextExtent(self.description)
        dc.SetTextForeground(self.secondaryColour)
        dc.DrawText(self.description, int(rect.x + bmpWidth + decalageTexte), int(rect.y + 3 * (rect.height - textHeight) / 4))

    def GetLineHeight(self):
        dc = wx.MemoryDC()
        largeurBitmap = Style.px(100)
        hauteurBitmap = Style.px(20)
        if 'phoenix' in wx.PlatformInfo:
            dc.SelectObject(wx.Bitmap(largeurBitmap, hauteurBitmap))
        else:
            dc.SelectObject(wx.EmptyBitmap(largeurBitmap, hauteurBitmap))

        if self.icon is not None:
            bmpWidth, bmpHeight = self.icon.GetWidth(), self.icon.GetHeight()
        else:
            bmpWidth, bmpHeight = _taille_image()

        dc.SetFont(self.normalFont)
        textWidth, textHeight = dc.GetTextExtent(self.text)

        dc.SetFont(self.smallerFont)
        textWidth, textHeight = dc.GetTextExtent(self.description)

        dc.SelectObject(wx.NullBitmap)
        return max(2 * textHeight, bmpHeight) + Style.espace(5)

    def GetSubItemWidth(self):
        return Style.px(250)


class SecondColumnRenderer(object):
    def __init__(self, parent, dateModif=None, taille=None):
        self.parent = parent
        self.date = dateModif
        self.size = taille

        self.smallerFont = Style.police("body_small")
        self.secondaryColour = Style.couleur("on_surface_variant")
        self.primaryColour = Style.couleur("on_surface")

    def DrawSubItem(self, dc, rect, line, highlighted, enabled):
        """Dessine les métadonnées du fichier."""
        dc.SetFont(self.smallerFont)
        marge = Style.espace(1)

        if self.date is not None:
            dummy1, dummy2 = dc.GetTextExtent(_(u"Date modif.: "))
            textWidth, textHeight = dc.GetTextExtent(self.date)
            dc.SetTextForeground(self.secondaryColour)
            dc.DrawText(_(u"Date modif.: "), int(rect.x + marge), int(rect.y + (rect.height - textHeight) / 4))
            dc.SetTextForeground(self.primaryColour)
            dc.DrawText(self.date, int(rect.x + dummy1 + marge), int(rect.y + (rect.height - textHeight) / 4))
        else:
            textWidth, textHeight = 0, 0

        if self.size:
            dummy1, dummy2 = dc.GetTextExtent(_(u"Taille: "))
            dc.SetTextForeground(self.secondaryColour)
            dc.DrawText(_(u"Taille: "), int(rect.x + marge), int(rect.y + 3 * (rect.height - textHeight) / 4))
            dc.SetTextForeground(self.primaryColour)
            dc.DrawText(self.size, int(rect.x + dummy1 + marge), int(rect.y + 3 * (rect.height - textHeight) / 4))

    def GetLineHeight(self):
        dc = wx.MemoryDC()
        largeurBitmap = Style.px(100)
        hauteurBitmap = Style.px(20)
        if 'phoenix' in wx.PlatformInfo:
            dc.SelectObject(wx.Bitmap(largeurBitmap, hauteurBitmap))
        else:
            dc.SelectObject(wx.EmptyBitmap(largeurBitmap, hauteurBitmap))
        textWidth, textHeight, d1, d2 = dc.GetFullTextExtent("xx", self.smallerFont)
        dc.SelectObject(wx.NullBitmap)
        return 2 * textHeight + Style.espace(5)

    def GetSubItemWidth(self):
        dc = wx.MemoryDC()
        largeurBitmap = Style.px(100)
        hauteurBitmap = Style.px(20)
        if 'phoenix' in wx.PlatformInfo:
            dc.SelectObject(wx.Bitmap(largeurBitmap, hauteurBitmap))
        else:
            dc.SelectObject(wx.EmptyBitmap(largeurBitmap, hauteurBitmap))

        if self.date is not None:
            texte = _(u"Date modif.:") + self.date
        else:
            texte = _(u"Taille : 888.88 MB")
        textWidth, textHeight, d1, d2 = dc.GetFullTextExtent(texte, self.smallerFont)
        dc.SelectObject(wx.NullBitmap)
        return textWidth + Style.espace(2)


class CTRL(ULC.UltimateListCtrl):
    def __init__(self, parent, prefixe=None, details=True, mode="local", codesReseau=None):
        ULC.UltimateListCtrl.__init__(self, parent, -1, style=wx.BORDER_THEME, agwStyle=wx.LC_REPORT | wx.LC_NO_HEADER | wx.LC_HRULES | ULC.ULC_HAS_VARIABLE_ROW_HEIGHT)
        Style.appliquer_liste(self)
        self.prefixe = prefixe
        self.details = details
        self.mode = mode
        self.codesReseau = codesReseau

        self.EnableSelectionVista()
        self.Remplissage()

    def SetMode(self, mode="local", codesReseau=None):
        self.mode = mode
        self.codesReseau = codesReseau
        self.Remplissage()

    def Remplissage(self):
        """ Remplissage du contrôle """
        wx.BeginBusyCursor()
        self.Freeze()

        self.ClearAll()
        if self.mode == "local":
            self.listeFichiers = self.GetListeFichiersLocal()
        else:
            self.listeFichiers = self.GetListeFichiersReseau()

        self.InsertColumn(0, "Column 1")
        self.InsertColumn(1, "Column 2")

        for dictFichier in self.listeFichiers:
            index = self.InsertStringItem(six.MAXSIZE, "")

            klass = FirstColumnRenderer(self, titre=dictFichier["titre"], image=dictFichier["image"], description=dictFichier["description"])
            self.SetItemCustomRenderer(index, 0, klass)

            if self.details == True and self.mode != "reseau":
                self.SetStringItem(index, 1, "")
                klass = SecondColumnRenderer(self, dateModif=dictFichier["dateModif"], taille=dictFichier["taille"])
                self.SetItemCustomRenderer(index, 1, klass)

            self.SetItemPyData(index, dictFichier)

        self.SetColumnWidth(0, ULC.ULC_AUTOSIZE_FILL)
        self.SetColumnWidth(1, wx.LIST_AUTOSIZE)

        self.Thaw()
        self.SendSizeEvent()
        wx.EndBusyCursor()

    def GetListeFichiersLocal(self):
        """ Récupère la liste des fichiers locaux à afficher """
        # Lit le répertoire
        chemin = UTILS_Fichiers.GetRepData()
        fichiers = os.listdir(chemin)
        fichiers.sort()

        listeFichiers = []
        for fichier in fichiers:
            nomFichier = os.path.split(fichier)[1]
            titre = nomFichier[:-9]
            cheminFichier = chemin + "/" + fichier

            if (self.prefixe == None and nomFichier.endswith("_DATA.dat")) or (self.prefixe != None and nomFichier.endswith("_DATA.dat") and nomFichier.startswith(self.prefixe)):

                # Taille des 3 bases de données
                taille = 0
                for suffixe in ("DATA", "DOCUMENTS", "PHOTOS"):
                    fichierTemp = u"%s/%s_%s.dat" % (chemin, titre, suffixe)
                    if os.path.isfile(fichierTemp):
                        taille += os.path.getsize(fichierTemp)
                taille = FormatFileSize(taille)

                # Date dernière modification
                t = os.path.getmtime(cheminFichier)
                date = datetime.datetime.fromtimestamp(t)
                dateModif = date.strftime("%d/%m/%Y %H:%M")

                # Ouverture de la base de données pour Récupèrer les infos sur le fichier
                logo = None
                description = u""
                try:
                    connexion = sqlite3.connect(cheminFichier.encode('utf-8'))
                    cursor = connexion.cursor()
                    req = "SELECT nom, logo FROM organisateur WHERE IDorganisateur=1;"
                    cursor.execute(req)
                    description, logo = cursor.fetchone()
                    connexion.close()
                except Exception:
                    pass

                if logo != None:
                    try:
                        io = six.BytesIO(logo)
                        if 'phoenix' in wx.PlatformInfo:
                            img = wx.Image(io, wx.BITMAP_TYPE_ANY)
                        else:
                            img = wx.ImageFromStream(io, wx.BITMAP_TYPE_ANY)
                        img = RecadreImg(img)
                        image = img.ConvertToBitmap()
                    except Exception:
                        image = None
                else:
                    image = None

                # mémorisation
                listeFichiers.append({"titre": titre, "image": image, "description": description, "taille": taille, "dateModif": dateModif})

        return listeFichiers

    def TestConnexionReseau(self):
        hote = self.codesReseau["hote"]
        utilisateur = self.codesReseau["utilisateur"]
        motdepasse = self.codesReseau["motdepasse"]
        port = self.codesReseau["port"]

        DB = GestionDB.DB(nomFichier=u"%s;%s;%s;%s[RESEAU]" % (port, hote, utilisateur, motdepasse), pooling=False)
        if DB.echec == 1:
            DB.Close()
            return DB.erreur
        DB.Close()
        return True

    def GetListeFichiersReseau(self):
        """ Récupère la liste des fichiers réseau à afficher """
        listeFichiers = []

        # Connexion au réseau MySQL
        hote = self.codesReseau["hote"]
        utilisateur = self.codesReseau["utilisateur"]
        motdepasse = self.codesReseau["motdepasse"]
        port = self.codesReseau["port"]

        if hote == "" or utilisateur == "":
            return listeFichiers

        DB = GestionDB.DB(nomFichier=u"%s;%s;%s;%s[RESEAU]" % (port, hote, utilisateur, motdepasse), pooling=False)
        if DB.echec == 1:
            DB.Close()
            return listeFichiers

        # Test de connexion à une base de données
        listeDatabases = []
        DB.ExecuterReq("SHOW DATABASES;")
        listeValeurs = DB.ResultatReq()
        for valeurs in listeValeurs:
            listeDatabases.append(valeurs[0])

        # Récupération des infos
        for nomFichier in listeDatabases:
            if (self.prefixe == None and nomFichier.endswith("_data")) or (self.prefixe != None and nomFichier.endswith("_data") and nomFichier.startswith(self.prefixe)):

                titre = nomFichier[:-5]

                # Taille des 3 bases de données
                taille = 0
##                for suffixe in ("data", "documents", "photos") :
##                    base = u"%s_%s" % (titre, suffixe)
##                    try :
##                        cursor.execute("""SELECT table_schema, sum( data_length + index_length) /1024 FROM information_schema.TABLES WHERE table_schema = "%s";""" % base)
##                        nom, tailleBase = cursor.fetchone()
##                        taille += tailleBase
##                    except :
##                        pass
                taille = FormatFileSize(float(taille))

                # Date de dernière modification
                dateModif = None

                # Ouverture de la base de données pour Récupèrer les infos sur le fichier
                nom = u""
                logo = None
                description = u""
                try:
                    DB.ExecuterReq("""USE %s_data;""" % titre)
                    DB.ExecuterReq("""SELECT nom, logo FROM organisateur WHERE IDorganisateur=1;""")
                    description, logo = DB.ResultatReq()[0]
                except Exception:
                    pass

                if logo != None:
                    try:
                        io = six.BytesIO(logo)
                        if 'phoenix' in wx.PlatformInfo:
                            img = wx.Image(io, wx.BITMAP_TYPE_ANY)
                        else:
                            img = wx.ImageFromStream(io, wx.BITMAP_TYPE_ANY)
                        img = RecadreImg(img)
                        image = img.ConvertToBitmap()
                    except Exception:
                        image = None
                else:
                    image = None

                # mémorisation
                listeFichiers.append({"titre": titre, "image": None, "image": image, "description": description, "taille": taille, "dateModif": dateModif})

        # Fermeture connexion
        DB.Close()

        return listeFichiers

    def ModifierFichier(self, titre=""):
        """ Modifier un fichier """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("fichier_fichier", "modifier") == False:
            return

        if self.mode == "reseau":
            dlg = wx.MessageDialog(self, _(u"Il est impossible de modifier le nom d'un fichier réseau !"), _(u"Désolé"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # Demande de confirmation 1
        dlg = wx.MessageDialog(None, _(u"Souhaitez-vous vraiment modifier le nom du fichier '%s' ?") % titre, _(u"Modifier un fichier"), wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)
        reponse = dlg.ShowModal()
        dlg.Destroy()
        if reponse != wx.ID_YES:
            return

        # Demande le nouveau nom du fichier
        dlg = wx.TextEntryDialog(self, _(u"Saisissez un nouveau nom pour le fichier '%s' :") % titre, _(u"Modifier le nom"), titre)
        if dlg.ShowModal() == wx.ID_OK:
            nouveauTitre = dlg.GetValue()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return

        if nouveauTitre == "":
            dlg = wx.MessageDialog(self, _(u"Le nom que vous avez saisi ne semble pas valide !"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # Demande de confirmation 2
        dlg = wx.MessageDialog(None, _(u"Vous êtes vraiment sûr de vouloir changer le nom du fichier '%s' en '%s' ?") % (titre, nouveauTitre), _(u"Modifier un fichier"), wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_EXCLAMATION)
        reponse = dlg.ShowModal()
        dlg.Destroy()
        if reponse != wx.ID_YES:
            return

        # Modifier un fichier local
        for suffixe in ("DATA", "DOCUMENTS", "PHOTOS"):
            try:
                source = UTILS_Fichiers.GetRepData(u"%s_%s.dat" % (titre, suffixe))
                destination = UTILS_Fichiers.GetRepData(u"%s_%s.dat" % (nouveauTitre, suffixe))
                os.rename(source, destination)
            except Exception as err:
                print(suffixe, "Erreur dans le renommage de fichier : ", err)
        self.Remplissage()

    def SupprimerFichier(self, titre=""):
        """ Supprimer un fichier """
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("fichier_fichier", "supprimer") == False:
            return

        # Demande de confirmation
        dlg = wx.MessageDialog(None, _(u"Souhaitez-vous vraiment supprimer le fichier '%s' ?") % titre, _(u"Supprimer un fichier"), wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_QUESTION)
        reponse = dlg.ShowModal()
        dlg.Destroy()
        if reponse != wx.ID_YES:
            return

        dlg = wx.MessageDialog(None, _(u"Attention, la suppression est irreversible !!! \n\n Vous êtes vraiment sûr de vouloir supprimer le fichier '%s' ?") % titre, _(u"Supprimer un fichier"), wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_EXCLAMATION)
        reponse = dlg.ShowModal()
        dlg.Destroy()
        if reponse != wx.ID_YES:
            return

        # Supprimer un fichier local
        if self.mode == "local":
            for suffixe in ("DATA", "DOCUMENTS", "PHOTOS"):
                try:
                    os.remove(UTILS_Fichiers.GetRepData(u"%s_%s.dat" % (titre, suffixe)))
                except Exception as err:
                    pass

        # Supprime un fichier réseau
        if self.mode == "reseau":
            hote = self.codesReseau["hote"]
            utilisateur = self.codesReseau["utilisateur"]
            motdepasse = self.codesReseau["motdepasse"]
            port = self.codesReseau["port"]

            DB = GestionDB.DB(nomFichier=u"%s;%s;%s;%s[RESEAU]" % (port, hote, utilisateur, motdepasse))
            if DB.echec == 1:
                dlg = wx.MessageDialog(self, _(u"Erreur de connexion MySQL !\n\n%s") % DB.erreur, _(u"Erreur de connexion"), wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return

            for suffixe in ("data", "documents", "photos"):
                DB.ExecuterReq("""DROP DATABASE IF EXISTS %s_%s;""" % (titre, suffixe))

            DB.Close()
        self.Remplissage()


# ----------------------------------------------------------------------------------------------------------------------

class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        Style.appliquer_fenetre(self, "surface")
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(panel, "surface")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL | wx.EXPAND, Style.espace(2))
        self.SetSizer(sizer_1)

        self.ctrl = CTRL(panel, prefixe="", details=True, mode="local", codesReseau={})  # Test mode local
##        self.ctrl = CTRL(panel, prefixe="", details=True, mode="reseau", codesReseau={"port":3306, "hote" : "locahost", "utilisateur" : "root", "motdepasse" : "XXXX"}) # Test mode réseau
        self.Bind(ULC.EVT_LIST_ITEM_ACTIVATED, self.OnSelection, self.ctrl)

        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, Style.espace(1))
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()

    def OnSelection(self, event):
        index = self.ctrl.GetFirstSelected()
        print(self.ctrl.GetItemPyData(index))


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(Style.px(600), Style.px(600)))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
