#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-17 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import os

import wx

from Ctrl import CTRL_ActionRepens
from Ctrl import CTRL_Choix_modele
from Utils import UTILS_Config
from Utils import UTILS_Questionnaires
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


class CTRL_Question(wx.Choice):
    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1)
        self.parent = parent
        Style.appliquer_saisie(self)
        self.SetListe()

    def SetListe(self):
        self.UtilsQuestionnaires = UTILS_Questionnaires.Questionnaires()
        self.liste_questions = self.UtilsQuestionnaires.GetQuestions(type="location", avec_filtre=False)
        self.Clear()
        self.dictDonnees = {}
        index = 0
        for dictQuestion in self.liste_questions:
            if dictQuestion["controle"] == "documents":
                self.Append(dictQuestion["label"])
                self.dictDonnees[index] = dictQuestion["IDquestion"]
                index += 1
        if self.GetCount():
            self.SetSelection(0)

    def SetID(self, ID=None):
        for indexTemp, IDtemp in self.dictDonnees.items():
            if IDtemp == ID:
                self.SetSelection(indexTemp)
                return

    def GetID(self):
        index = self.GetSelection()
        if index == -1:
            return None
        return self.dictDonnees[index]


class CTRL(wx.Panel):
    """Options d'édition des locations, sans géométrie locale historique."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        self.parent = parent
        Style.appliquer_fenetre(self, "surface")

        self.label_modele = wx.StaticText(self, -1, _(u"Modèle :"))
        self.ctrl_modele = CTRL_Choix_modele.CTRL_Choice(self, categorie="location")
        self.bouton_modele = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Gérer"),
            icone="settings",
            variante="ghost",
            tooltip=_(u"Accéder à la gestion des modèles"),
            compact=True,
        )

        self.label_repertoire = wx.StaticText(self, -1, _(u"Copie :"))
        self.checkbox_repertoire = wx.CheckBox(self, -1, _(u"Enregistrer une copie unique dans le répertoire"))
        self.ctrl_repertoire = wx.TextCtrl(self, -1, u"")
        self.bouton_repertoire = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Parcourir…"),
            icone="more",
            variante="ghost",
            tooltip=_(u"Sélectionner un répertoire de destination"),
            compact=True,
        )

        self.label_questionnaire = wx.StaticText(self, -1, _(u"Stockage :"))
        self.checkbox_questionnaire = wx.CheckBox(self, -1, _(u"Enregistrer une copie unique dans un porte-documents"))
        self.ctrl_questionnaire = CTRL_Question(self)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonModele, self.bouton_modele)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckRepertoire, self.checkbox_repertoire)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckQuestionnaire, self.checkbox_questionnaire)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonRepertoire, self.bouton_repertoire)

        param = UTILS_Config.GetParametre("impression_locations_repertoire", defaut="")
        if param != "":
            self.checkbox_repertoire.SetValue(True)
            self.ctrl_repertoire.SetValue(param)

        param = UTILS_Config.GetParametre("impression_locations_questionnaire", defaut="")
        if param != "":
            self.checkbox_questionnaire.SetValue(True)
            self.ctrl_questionnaire.SetID(param)

        self.OnCheckRepertoire(None)
        self.OnCheckQuestionnaire(None)

    def __set_properties(self):
        for label in (self.label_modele, self.label_repertoire, self.label_questionnaire):
            Style.appliquer_texte(label, role="label", role_texte="on_surface_variant", role_fond="surface")
        for controle in (self.checkbox_repertoire, self.checkbox_questionnaire):
            Style.appliquer_texte(controle, role="body", role_texte="on_surface", role_fond="surface")
        Style.appliquer_saisie(self.ctrl_modele)
        Style.appliquer_saisie(self.ctrl_repertoire)
        Style.appliquer_saisie(self.ctrl_questionnaire)
        self.ctrl_repertoire.SetMinSize((Style.px(270), Style.cible_action("compact")))

        self.ctrl_modele.SetToolTip(wx.ToolTip(_(u"Sélectionnez le modèle")))
        self.checkbox_repertoire.SetToolTip(wx.ToolTip(_(u"Enregistrer un exemplaire de chaque location au format PDF dans le répertoire indiqué")))
        self.checkbox_questionnaire.SetToolTip(wx.ToolTip(_(u"Enregistrer un exemplaire de chaque document au format PDF dans un porte-document du questionnaire")))
        self.ctrl_questionnaire.SetToolTip(wx.ToolTip(_(u"Sélectionnez la question de type 'porte-document' dans laquelle sera stocké le document")))

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

        questionnaire = wx.BoxSizer(wx.HORIZONTAL)
        questionnaire.Add(self.checkbox_questionnaire, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, espace)
        questionnaire.Add(self.ctrl_questionnaire, 1, wx.EXPAND)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(self._Ligne(self.label_modele, modele), 0, wx.EXPAND | wx.BOTTOM, espace)
        principal.Add(self._Ligne(self.label_repertoire, repertoire), 0, wx.EXPAND | wx.BOTTOM, espace)
        principal.Add(self._Ligne(self.label_questionnaire, questionnaire), 0, wx.EXPAND)
        self.SetSizer(principal)
        self.Layout()

    def OnBoutonModele(self, event):
        from Dlg import DLG_Modeles_docs
        dlg = DLG_Modeles_docs.Dialog(self, categorie="location")
        dlg.ShowModal()
        dlg.Destroy()
        self.ctrl_modele.MAJ()

    def OnCheckRepertoire(self, event):
        etat = self.checkbox_repertoire.GetValue()
        self.ctrl_repertoire.Enable(etat)
        self.bouton_repertoire.Enable(etat)

    def OnCheckQuestionnaire(self, event):
        self.ctrl_questionnaire.Enable(self.checkbox_questionnaire.GetValue())

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
        try:
            if dlg.ShowModal() == wx.ID_OK:
                self.ctrl_repertoire.SetValue(dlg.GetPath())
        finally:
            dlg.Destroy()

    def MemoriserParametres(self):
        if self.checkbox_repertoire.GetValue() is True:
            UTILS_Config.SetParametre("impression_locations_repertoire", self.ctrl_repertoire.GetValue())
        else:
            UTILS_Config.SetParametre("impression_locations_repertoire", "")
        if self.checkbox_questionnaire.GetValue() is True:
            UTILS_Config.SetParametre("impression_locations_questionnaire", self.ctrl_questionnaire.GetID())
        else:
            UTILS_Config.SetParametre("impression_locations_questionnaire", "")

    def GetOptions(self):
        dictOptions = {}

        if self.checkbox_repertoire.GetValue() is True:
            repertoire = self.ctrl_repertoire.GetValue()
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

        if self.checkbox_questionnaire.GetValue() is True:
            questionnaire = self.ctrl_questionnaire.GetID()
            if questionnaire is None:
                dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement sélectionner une question !"), _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
                self.ctrl_questionnaire.SetFocus()
                return False
        else:
            questionnaire = None

        IDmodele = self.ctrl_modele.GetID()
        if IDmodele is None:
            dlg = wx.MessageDialog(self, _(u"Vous devez obligatoirement sélectionner un modèle !"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        dictOptions["IDmodele"] = IDmodele
        dictOptions["repertoire"] = repertoire
        dictOptions["nomModele"] = self.ctrl_modele.GetStringSelection()
        dictOptions["questionnaire"] = questionnaire
        return dictOptions


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(panel, "surface")
        self.ctrl = CTRL(panel)
        self.boutonTest = wx.Button(panel, -1, _(u"Bouton de test"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, Style.espace(2))
        sizer.Add(self.boutonTest, 0, wx.ALL | wx.EXPAND, Style.espace(2))
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
