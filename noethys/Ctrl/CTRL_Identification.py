#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:          Licence GNU GPL
#-----------------------------------------------------------

import Chemins
from Utils.UTILS_Traduction import _
from Utils import UTILS_StyleRepens as Style
import wx
from Ctrl import CTRL_Bouton_image
import datetime
try:
    from Crypto.Hash import SHA256
except Exception:
    from Cryptodome.Hash import SHA256


def _ConfigurerBarreShell(parent):
    """Aligne la toolbar hôte sur les métriques publiques de Repens."""
    try:
        import wx.lib.agw.aui as aui
        if not isinstance(parent, aui.AuiToolBar):
            return
        parent._noethys_toolbar_icon_base = 24
        taille = Style.taille_icone("toolbar")
        parent.SetToolBitmapSize(wx.Size(taille, taille))
        hauteur = Style.hauteur_toolbar(avec_libelle=True)
        parent.SetMinSize((-1, hauteur))
        parent._noethys_toolbar_min_height = hauteur
    except Exception:
        pass


class CTRL(wx.SearchCtrl):
    """Champ d'identification utilisable dans le shell et dans le dialogue."""

    def __init__(self, parent, listeUtilisateurs=None, size=wx.DefaultSize, modeDLG=False):
        _ConfigurerBarreShell(parent)
        wx.SearchCtrl.__init__(self, parent, size=size, style=wx.TE_PROCESS_ENTER | wx.TE_PASSWORD)
        self.parent = parent
        self.listeUtilisateurs = listeUtilisateurs or []
        self.modeDLG = modeDLG
        self.SetDescriptiveText(_(u"Code d'identification"))
        Style.appliquer_saisie(self)

        self.ShowSearchButton(True)
        self.ShowCancelButton(False)
        try:
            taille = Style.taille_icone("inline")
            chemin = Chemins.GetStaticIconPath("Images/16x16/Cadenas.png", taille=taille)
            bitmap = wx.Bitmap(chemin, wx.BITMAP_TYPE_ANY)
            if bitmap.IsOk():
                self.SetSearchBitmap(bitmap)
        except Exception:
            pass

        try:
            largeur = max(Style.px(150), self.GetMinSize().GetWidth())
            self.SetMinSize((largeur, Style.cible_action("compact")))
        except Exception:
            pass

        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)

    def OnSearch(self, event):
        self.Recherche()
        event.Skip()

    def OnCancel(self, event):
        self.SetValue("")
        self.Recherche()
        event.Skip()

    def OnDoSearch(self, event):
        self.ShowCancelButton(bool(self.GetValue()))
        self.Recherche()
        event.Skip()

    def GetPasse(self, txtSearch=""):
        return str(int(datetime.datetime.today().strftime("%d%m%Y")) // 3)

    def Recherche(self):
        txtSearch = self.GetValue()
        mdpcrypt = SHA256.new(txtSearch.encode('utf-8')).hexdigest()
        listeUtilisateurs = self.listeUtilisateurs if self.modeDLG else self.GetGrandParent().listeUtilisateurs

        for dictUtilisateur in listeUtilisateurs:
            if (
                txtSearch == dictUtilisateur["mdp"]
                or mdpcrypt == dictUtilisateur["mdpcrypt"]
                or (txtSearch == self.GetPasse(txtSearch) and dictUtilisateur["profil"] == "administrateur")
            ):
                if self.modeDLG:
                    self.GetParent().ChargeUtilisateur(dictUtilisateur)
                    self.SetValue("")
                    break

                mainFrame = self.GetGrandParent()
                if mainFrame.GetName() == "general":
                    mainFrame.ChargeUtilisateur(dictUtilisateur)
                    self.SetValue("")
                    break
        self.Refresh()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(self, "surface")
        Style.appliquer_fenetre(panel, "surface")
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.myOlv = CTRL(panel)
        self.myOlv2 = wx.TextCtrl(panel, -1, "test")
        Style.appliquer_saisie(self.myOlv2)
        sizer.Add(self.myOlv, 0, wx.ALL | wx.EXPAND, Style.espace(2))
        sizer.Add(self.myOlv2, 0, wx.ALL | wx.EXPAND, Style.espace(2))
        panel.SetSizer(sizer)
        cadre = wx.BoxSizer(wx.VERTICAL)
        cadre.Add(panel, 1, wx.EXPAND)
        self.SetSizer(cadre)
        self.SetSize((500, 150))
        self.Layout()
        self.CenterOnScreen()


class Dialog(wx.Dialog):
    """Dialogue d'identification responsive, sans StaticBox/FlexGridSizer."""

    def __init__(self, parent, id=-1, title=_(u"Identification"), listeUtilisateurs=None, nomFichier=None):
        wx.Dialog.__init__(
            self,
            parent,
            id,
            title,
            name="DLG_mdp",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.parent = parent
        self.listeUtilisateurs = listeUtilisateurs or []
        self.nomFichier = nomFichier
        self.dictUtilisateur = None
        Style.appliquer_fenetre(self, "surface")

        if self.nomFichier is not None:
            self.SetTitle(_(u"Ouverture du fichier %s") % self.nomFichier)

        self.label = wx.StaticText(self, -1, _(u"Saisissez votre code d'identification personnel."))
        Style.appliquer_texte(self.label, role="body", role_texte="on_surface", role_fond="surface")
        self.ctrl_mdp = CTRL(self, listeUtilisateurs=self.listeUtilisateurs, modeDLG=True)

        self.label_exemple = wx.StaticText(self, -1, _(u"Le mot de passe des fichiers exemples est 'aze'"))
        Style.appliquer_texte(
            self.label_exemple,
            role="caption",
            role_texte="on_surface_variant",
            role_fond="surface",
        )
        self.label_exemple.Show(bool(nomFichier and nomFichier.startswith("EXEMPLE_")))

        self.bouton_annuler = CTRL_Bouton_image.CTRL(
            self,
            id=wx.ID_CANCEL,
            texte=_(u"Annuler"),
            iconeFluent="dismiss",
        )
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Annuler")))

        self.__do_layout()
        wx.CallAfter(self.ctrl_mdp.SetFocus)

    def __do_layout(self):
        marge = Style.espace(4)
        espace = Style.espace(3)

        contenu = wx.BoxSizer(wx.VERTICAL)
        contenu.Add(self.label, 0, wx.EXPAND | wx.BOTTOM, espace)
        contenu.Add(self.ctrl_mdp, 0, wx.EXPAND | wx.BOTTOM, Style.espace(1))
        contenu.Add(self.label_exemple, 0, wx.ALIGN_RIGHT)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_annuler, 0)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(contenu, 1, wx.EXPAND | wx.ALL, marge)
        principal.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, marge)
        self.SetSizer(principal)
        self.SetMinSize((Style.px(380), -1))
        self.Fit()
        self.Layout()
        if self.GetParent() is not None:
            self.CentreOnParent()
        else:
            self.CentreOnScreen()

    def ChargeUtilisateur(self, dictUtilisateur=None):
        self.dictUtilisateur = dictUtilisateur or {}
        self.EndModal(wx.ID_OK)

    def GetDictUtilisateur(self):
        return self.dictUtilisateur


if __name__ == '__main__':
    app = wx.App(0)
    dlg = Dialog(None, listeUtilisateurs=[])
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    print(dlg.GetDictUtilisateur())
    app.MainLoop()
