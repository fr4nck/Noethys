#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-14 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import os

import wx

from Ctrl import CTRL_ActionRepens
from Ctrl import CTRL_Choix_modele
from Utils import UTILS_Config
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


class CTRL(wx.Panel):
    """Options d'édition des cotisations, compactes et pilotées par Repens."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        self.parent = parent
        Style.appliquer_fenetre(self, "surface")

        self.label_modele = wx.StaticText(self, -1, _(u"Modèle :"))
        self.ctrl_modele = CTRL_Choix_modele.CTRL_Choice(self, categorie="cotisation")
        self.bouton_modele = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Gérer"),
            icone="settings",
            variante="ghost",
            tooltip=_(u"Accéder à la gestion des modèles"),
            compact=True,
        )

        self.label_repertoire = wx.StaticText(self, -1, _(u"Copie :"))
        self.checkbox_repertoire = wx.CheckBox(self, -1, _(u"Enregistrer une copie PDF dans"))
        self.ctrl_repertoire = wx.TextCtrl(self, -1, u"")
        self.bouton_repertoire = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Parcourir…"),
            icone="more",
            variante="ghost",
            tooltip=_(u"Sélectionner un répertoire de destination"),
            compact=True,
        )

        self._AppliquerStyle()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonModele, self.bouton_modele)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckRepertoire, self.checkbox_repertoire)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonRepertoire, self.bouton_repertoire)

        param = UTILS_Config.GetParametre("impression_cotisations_repertoire", defaut="")
        if param != "":
            self.checkbox_repertoire.SetValue(True)
            self.ctrl_repertoire.SetValue(param)
        self.OnCheckRepertoire(None)

    def _AppliquerStyle(self):
        self.ctrl_modele.SetToolTip(wx.ToolTip(_(u"Sélectionnez le modèle")))
        self.checkbox_repertoire.SetToolTip(wx.ToolTip(_(u"Enregistrer un exemplaire de chaque cotisation au format PDF dans le répertoire indiqué")))
        self.ctrl_repertoire.SetToolTip(wx.ToolTip(_(u"Répertoire où enregistrer la copie PDF")))

        for label in (self.label_modele, self.label_repertoire):
            Style.appliquer_texte(label, role="label", role_texte="on_surface_variant", role_fond="surface")
        Style.appliquer_texte(self.checkbox_repertoire, role="body", role_texte="on_surface", role_fond="surface")
        Style.appliquer_saisie(self.ctrl_modele)
        Style.appliquer_saisie(self.ctrl_repertoire)

        hauteur = Style.cible_action("compact")
        self.ctrl_modele.SetMinSize((Style.px(180), hauteur))
        self.ctrl_repertoire.SetMinSize((Style.px(260), hauteur))

    def _Ligne(self, label, contenu):
        ligne = wx.BoxSizer(wx.HORIZONTAL)
        label.SetMinSize((Style.px(72), -1))
        ligne.Add(label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, Style.espace(2))
        ligne.Add(contenu, 1, wx.EXPAND)
        return ligne

    def __do_layout(self):
        espace = Style.espace(2)

        modele = wx.BoxSizer(wx.HORIZONTAL)
        modele.Add(self.ctrl_modele, 1, wx.EXPAND | wx.RIGHT, espace)
        modele.Add(self.bouton_modele, 0, wx.ALIGN_CENTER_VERTICAL)

        repertoire = wx.BoxSizer(wx.HORIZONTAL)
        repertoire.Add(self.checkbox_repertoire, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, espace)
        repertoire.Add(self.ctrl_repertoire, 1, wx.EXPAND | wx.RIGHT, espace)
        repertoire.Add(self.bouton_repertoire, 0, wx.ALIGN_CENTER_VERTICAL)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(self._Ligne(self.label_modele, modele), 0, wx.EXPAND | wx.BOTTOM, espace)
        principal.Add(self._Ligne(self.label_repertoire, repertoire), 0, wx.EXPAND)
        self.SetSizer(principal)
        self.SetMinSize((Style.px(560), -1))
        self.Layout()

    def OnBoutonModele(self, event):
        from Dlg import DLG_Modeles_docs
        dlg = DLG_Modeles_docs.Dialog(self, categorie="cotisation")
        dlg.ShowModal()
        dlg.Destroy()
        self.ctrl_modele.MAJ()

    def OnCheckRepertoire(self, event):
        etat = self.checkbox_repertoire.GetValue()
        self.ctrl_repertoire.Enable(etat)
        self.bouton_repertoire.Enable(etat)

    def OnBoutonRepertoire(self, event):
        cheminDefaut = self.ctrl_repertoire.GetValue().strip()
        if not os.path.isdir(cheminDefaut):
            cheminDefaut = ""
        dlg = wx.DirDialog(
            self,
            _(u"Veuillez sélectionner un répertoire de destination :"),
            defaultPath=cheminDefaut,
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self.ctrl_repertoire.SetValue(dlg.GetPath())
        dlg.Destroy()

    def MemoriserParametres(self):
        if self.checkbox_repertoire.GetValue() is True:
            UTILS_Config.SetParametre("impression_cotisations_repertoire", self.ctrl_repertoire.GetValue())
        else:
            UTILS_Config.SetParametre("impression_cotisations_repertoire", "")

    def GetOptions(self):
        if self.checkbox_repertoire.GetValue() is True:
            repertoire = self.ctrl_repertoire.GetValue().strip()
            if repertoire == "":
                dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement sélectionner un répertoire de destination !"), _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                self.ctrl_repertoire.SetFocus()
                return False
            if os.path.isdir(repertoire) is False:
                dlg = wx.MessageDialog(self, _(u"Le répertoire de destination que vous avez saisi n'existe pas !"), _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                self.ctrl_repertoire.SetFocus()
                return False
        else:
            repertoire = None

        IDmodele = self.ctrl_modele.GetID()
        if IDmodele is None:
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement sélectionner un modèle !"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        return {"IDmodele": IDmodele, "repertoire": repertoire}


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(panel, "surface")
        self.ctrl = CTRL(panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 0, wx.ALL | wx.EXPAND, Style.espace(2))
        panel.SetSizer(sizer)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(panel, 1, wx.EXPAND)
        self.SetSizer(principal)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, _(u"TEST"), size=(800, 300))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
