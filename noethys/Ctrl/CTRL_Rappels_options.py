#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import os

import wx

from Ctrl import CTRL_ActionRepens
from Ctrl import CTRL_Choix_modele
from Utils import UTILS_Config
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _


class CTRL(wx.Panel):
    """Options d'édition des rappels, sans grille ni largeur historique figée."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        self.parent = parent
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        self.label_modele = wx.StaticText(self, -1, _(u"Modèle"))
        self.ctrl_modele = CTRL_Choix_modele.CTRL_Choice(self, categorie="rappel")
        self.bouton_modele = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Gérer"),
            icone="settings",
            variante="ghost",
            tooltip=_(u"Gérer les modèles de lettres de rappel"),
        )

        self.checkbox_coupon = wx.CheckBox(self, -1, _(u"Insérer le coupon-réponse"))
        self.checkbox_codeBarre = wx.CheckBox(self, -1, _(u"Insérer les codes-barres"))

        self.label_repertoire = wx.StaticText(self, -1, _(u"Copie PDF"))
        self.checkbox_repertoire = wx.CheckBox(
            self,
            -1,
            _(u"Enregistrer une copie unique dans un répertoire"),
        )
        self.ctrl_repertoire = wx.TextCtrl(self, -1, u"")
        self.ctrl_repertoire.SetMinSize((-1, UTILS_UIMetrics.action_target("compact")))
        try:
            self.ctrl_repertoire.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
            self.ctrl_repertoire.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        except Exception:
            pass
        self.bouton_repertoire = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Parcourir…"),
            icone="more",
            variante="ghost",
            tooltip=_(u"Sélectionner le répertoire de destination"),
        )

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonModele, self.bouton_modele)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckRepertoire, self.checkbox_repertoire)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonRepertoire, self.bouton_repertoire)

        self.checkbox_coupon.SetValue(UTILS_Config.GetParametre("impression_rappels_coupon", defaut=1))
        self.checkbox_codeBarre.SetValue(UTILS_Config.GetParametre("impression_rappels_codeBarre", defaut=1))
        param = UTILS_Config.GetParametre("impression_rappels_repertoire", defaut="")
        if param != "":
            self.checkbox_repertoire.SetValue(True)
            self.ctrl_repertoire.SetValue(param)
        self.OnCheckRepertoire(None)

    def __set_properties(self):
        secondaire = UTILS_Interface.GetCouleurRole("on_surface_variant")
        for label in (self.label_modele, self.label_repertoire):
            label.SetForegroundColour(secondaire)
            try:
                police = wx.Font(label.GetFont())
                police.SetWeight(wx.FONTWEIGHT_SEMIBOLD)
                label.SetFont(police)
            except Exception:
                pass

        self.ctrl_modele.SetToolTip(wx.ToolTip(_(u"Sélectionnez le modèle")))
        self.checkbox_coupon.SetToolTip(wx.ToolTip(_(u"Insérer un coupon à découper")))
        self.checkbox_codeBarre.SetToolTip(wx.ToolTip(_(u"Insérer un code-barres pour le numéro de lettre")))
        self.checkbox_repertoire.SetToolTip(
            wx.ToolTip(_(u"Enregistrer un exemplaire de chaque lettre de rappel au format PDF"))
        )

    def __do_layout(self):
        espace = UTILS_UIMetrics.spacing(1)
        section = UTILS_UIMetrics.spacing(2)

        ligne_modele = wx.BoxSizer(wx.HORIZONTAL)
        ligne_modele.Add(self.ctrl_modele, 1, wx.EXPAND | wx.RIGHT, espace)
        ligne_modele.Add(self.bouton_modele, 0, wx.ALIGN_CENTER_VERTICAL)

        options_document = wx.BoxSizer(wx.HORIZONTAL)
        options_document.Add(self.checkbox_coupon, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, section)
        options_document.Add(self.checkbox_codeBarre, 0, wx.ALIGN_CENTER_VERTICAL)
        options_document.AddStretchSpacer(1)

        ligne_repertoire = wx.BoxSizer(wx.HORIZONTAL)
        ligne_repertoire.Add(self.ctrl_repertoire, 1, wx.EXPAND | wx.RIGHT, espace)
        ligne_repertoire.Add(self.bouton_repertoire, 0, wx.ALIGN_CENTER_VERTICAL)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(self.label_modele, 0, wx.BOTTOM, espace)
        principal.Add(ligne_modele, 0, wx.EXPAND | wx.BOTTOM, section)
        principal.Add(options_document, 0, wx.EXPAND | wx.BOTTOM, section)
        principal.Add(self.label_repertoire, 0, wx.BOTTOM, espace)
        principal.Add(self.checkbox_repertoire, 0, wx.BOTTOM, espace)
        principal.Add(ligne_repertoire, 0, wx.EXPAND)
        self.SetSizer(principal)
        self.Layout()

    def OnBoutonModele(self, event):
        from Dlg import DLG_Modeles_docs
        dlg = DLG_Modeles_docs.Dialog(self, categorie="rappel")
        dlg.ShowModal()
        dlg.Destroy()
        self.ctrl_modele.MAJ()

    def OnCheckRepertoire(self, event):
        etat = self.checkbox_repertoire.GetValue()
        self.ctrl_repertoire.Enable(etat)
        self.bouton_repertoire.Enable(etat)

    def OnBoutonRepertoire(self, event):
        cheminDefaut = self.ctrl_repertoire.GetValue()
        if not cheminDefaut or not os.path.isdir(cheminDefaut):
            cheminDefaut = ""
        dlg = wx.DirDialog(
            self,
            _(u"Veuillez sélectionner un répertoire de destination :"),
            defaultPath=cheminDefaut,
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
        )
        try:
            if dlg.ShowModal() == wx.ID_OK:
                self.ctrl_repertoire.SetValue(dlg.GetPath())
        finally:
            dlg.Destroy()

    def MemoriserParametres(self):
        UTILS_Config.SetParametre("impression_rappels_coupon", int(self.checkbox_coupon.GetValue()))
        UTILS_Config.SetParametre("impression_rappels_codeBarre", int(self.checkbox_codeBarre.GetValue()))
        if self.checkbox_repertoire.GetValue() is True:
            UTILS_Config.SetParametre("impression_rappels_repertoire", self.ctrl_repertoire.GetValue())
        else:
            UTILS_Config.SetParametre("impression_rappels_repertoire", "")

    def GetOptions(self):
        if self.checkbox_repertoire.GetValue() is True:
            repertoire = self.ctrl_repertoire.GetValue()
            if repertoire == "":
                dlg = wx.MessageDialog(
                    self,
                    _(u"Vous devez obligatoirement sélectionner un répertoire de destination !"),
                    _(u"Erreur"),
                    wx.OK | wx.ICON_EXCLAMATION,
                )
                dlg.ShowModal()
                dlg.Destroy()
                self.ctrl_repertoire.SetFocus()
                return False
            if not os.path.isdir(repertoire):
                dlg = wx.MessageDialog(
                    self,
                    _(u"Le répertoire de destination que vous avez saisi n'existe pas !"),
                    _(u"Erreur"),
                    wx.OK | wx.ICON_EXCLAMATION,
                )
                dlg.ShowModal()
                dlg.Destroy()
                self.ctrl_repertoire.SetFocus()
                return False
        else:
            repertoire = None

        IDmodele = self.ctrl_modele.GetID()
        if IDmodele is None:
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez obligatoirement sélectionner un modèle !"),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_EXCLAMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False

        return {
            "codeBarre": self.checkbox_codeBarre.GetValue(),
            "coupon": self.checkbox_coupon.GetValue(),
            "IDmodele": IDmodele,
            "repertoire": repertoire,
        }


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        self.ctrl = CTRL(panel)
        self.boutonTest = wx.Button(panel, -1, _(u"Bouton de test"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(2))
        sizer.Add(self.boutonTest, 0, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(2))
        panel.SetSizer(sizer)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(panel, 1, wx.EXPAND)
        self.SetSizer(principal)
        self.Layout()
        self.CentreOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnBoutonTest, self.boutonTest)

    def OnBoutonTest(self, event):
        print(self.ctrl.GetOptions())


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, _(u"TEST"), size=(700, 500))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
