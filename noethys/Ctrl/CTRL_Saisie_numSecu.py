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
import wx.lib.masked as masked

from Utils.UTILS_Traduction import _
from Utils import UTILS_StyleRepens as Style


class NumSecu(wx.Panel):
    """Saisie du NIR avec validation et indicateur sémantique scalable."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.ctrl_numsecu = masked.TextCtrl(
            self,
            -1,
            "",
            style=wx.TE_CENTRE,
            mask="# ## ## #N ### ### ##",
        )
        self.indicateur = wx.StaticText(self, -1, u"–", style=wx.ALIGN_CENTER)
        self.remplissageEnCours = False

        self.__set_properties()
        self.__do_layout()
        self.ctrl_numsecu.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

    def __set_properties(self):
        texteNumSecu = u"""
Attention, le numéro de sécurité sociale est considéré comme une donnée
sensible par la CNIL. Assurez-vous que vous êtes autorisé à saisir cette
information dans votre fichier de données.

Numéro de sécurité sociale : A BB CC DD EEE FFF GG

A : Sexe (1=homme | 2=femme)
BB : Année de naissance
CC : Mois de naissance
DD : Département de naissance (99 si né à l'étranger)
EEE : Code INSEE de la commune de naissance ou du pays si né à l'étranger
FFF : Numéro d'ordre INSEE
GG : Clé
        """
        self.ctrl_numsecu.SetToolTip(wx.ToolTip(texteNumSecu))

        Style.appliquer_fenetre(self, "surface")
        Style.appliquer_saisie(self.ctrl_numsecu)
        try:
            self.indicateur.SetFont(Style.police("h4"))
            self.indicateur.SetBackgroundColour(Style.couleur("surface"))
        except Exception:
            pass

        try:
            largeur = max(
                Style.px(196),
                self.ctrl_numsecu.GetTextExtent("1 99 99 99 999 999 99")[0] + Style.espace(4),
            )
            hauteur = Style.cible_action("compact")
            self.ctrl_numsecu.SetMinSize((largeur, hauteur))
            self.indicateur.SetMinSize((hauteur, hauteur))
        except Exception:
            pass

        self._AfficheEtat(None)

    def __do_layout(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.ctrl_numsecu, 1, wx.EXPAND)
        sizer.Add(self.indicateur, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, Style.espace(1))
        self.SetSizer(sizer)
        self.Fit()
        self.Layout()

    def _AfficheEtat(self, validation):
        try:
            if validation is True:
                self.indicateur.SetLabel(u"✓")
                self.indicateur.SetForegroundColour(Style.couleur("success"))
                self.indicateur.SetToolTip(wx.ToolTip(_(u"Numéro de sécurité sociale cohérent")))
            elif validation is False:
                self.indicateur.SetLabel(u"!")
                self.indicateur.SetForegroundColour(Style.couleur("danger"))
                self.indicateur.SetToolTip(wx.ToolTip(_(u"Numéro de sécurité sociale à vérifier")))
            else:
                self.indicateur.SetLabel(u"–")
                self.indicateur.SetForegroundColour(Style.couleur("on_surface_variant"))
                self.indicateur.SetToolTip(wx.ToolTip(_(u"Aucun numéro renseigné")))
            self.indicateur.Refresh()
            self.Layout()
        except Exception:
            pass

    def SetValue(self, numSecu=""):
        if numSecu is None:
            return
        self.remplissageEnCours = True
        try:
            self.ctrl_numsecu.SetValue(numSecu)
        except Exception:
            pass
        self.TestValidite(avecMessagesErreur=False)
        self.remplissageEnCours = False

    def GetValue(self):
        return self.ctrl_numsecu.GetValue()

    def OnKillFocus(self, event):
        self.TestValidite()
        if event is not None:
            event.Skip()

    def TestValidite(self, avecMessagesErreur=True):
        texte = self.ctrl_numsecu.GetValue()
        sexe = self.parent.ctrl_civilite.GetSexe()
        datenaiss = self.parent.ctrl_datenaiss.GetValue()
        cp_naiss = self.parent.ctrl_adressenaiss.GetValueCP()
        validation, message = self.ValideNumSecu(texte, sexe, datenaiss, cp_naiss)

        self._AfficheEtat(validation)
        if validation is False and self.remplissageEnCours is False and avecMessagesErreur is True:
            dlg = wx.MessageDialog(self, message, _(u"Numéro de sécurité sociale erroné"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()

    def ValideNumSecu(self, texte, sexe, date_naiss, cp_naiss):
        texteSansEsp = ""
        for lettre in texte:
            if lettre != " ":
                if lettre in "ABab":
                    lettre = "0"
                texteSansEsp += lettre

        nbreChiffres = len(texteSansEsp)
        if nbreChiffres == 0:
            return None, ""
        if nbreChiffres < 15:
            message = _(u"Il manque ") + str(15 - nbreChiffres) + _(u" chiffre(s) au numéro de sécurité sociale que vous venez de saisir. Veuillez le vérifier.")
            return False, message

        if nbreChiffres == 15:
            if sexe == "M" and int(texteSansEsp[0]) != 1:
                message = _(u"Le numéro de sécurité sociale ne correspond pas à la civilité de la personne (le premier chiffre devrait être 1).")
                return False, message
            if sexe == "F" and int(texteSansEsp[0]) != 2:
                message = _(u"Le numéro de sécurité sociale ne correspond pas à la civilité de la personne (le premier chiffre devrait être 2).")
                return False, message

            if date_naiss != u"  /  /    ":
                mois = str(date_naiss[3:5])
                annee = str(date_naiss[8:10])
                if annee != str(texteSansEsp[1:3]):
                    message = _(u"Le numéro de sécurité sociale ne correspond pas à l'année de naissance de la personne.")
                    return False, message
                if mois != str(texteSansEsp[3:5]):
                    message = _(u"Le numéro de sécurité sociale ne correspond pas au mois de naissance de la personne.")
                    return False, message

            if cp_naiss != u"     " and cp_naiss is not None:
                dep = cp_naiss[0:2]
                if str(dep) != str(texteSansEsp[5:7]):
                    message = _(u"Le numéro de sécurité sociale ne correspond pas au lieu de naissance de la personne.")
                    return False, message

            cle = int(texteSansEsp[13:15])
            cle_calculee = 97 - (int(texteSansEsp[:13]) % 97)
            if cle != cle_calculee:
                message = _(u"La clé du numéro de sécurité sociale ne semble pas cohérente. \nD'après mes calculs, la bonne clé devrait être %02d. \n\nVeuillez vérifier votre saisie...") % cle_calculee
                return False, message

            return True, ""


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(self, "surface")
        Style.appliquer_fenetre(panel, "surface")
        self.ctrl = NumSecu(panel)
        self.bouton = wx.Button(panel, -1, _(u"Test"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 0, wx.ALL | wx.EXPAND, Style.espace(2))
        sizer.Add(self.bouton, 0, wx.ALL, Style.espace(2))
        panel.SetSizer(sizer)
        cadre = wx.BoxSizer(wx.VERTICAL)
        cadre.Add(panel, 1, wx.EXPAND)
        self.SetSizer(cadre)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
