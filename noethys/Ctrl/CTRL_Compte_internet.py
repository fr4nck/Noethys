#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-18 Ivan LUCAS
# Licence:          Licence GNU GPL
#-----------------------------------------------------------

import wx

from Utils import UTILS_Internet
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


class CTRL(wx.Panel):
    """Résumé natif du compte internet, consommateur du CSS Repens."""

    def __init__(self, parent, IDfamille=None, IDutilisateur=None, couleurFond=None):
        wx.Panel.__init__(self, parent, -1, style=wx.BORDER_NONE | wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDfamille = IDfamille
        self.IDutilisateur = IDutilisateur
        self.couleurFond = couleurFond or Style.couleur("surface_container_lowest")
        self.dictDonnees = {}

        self.indicateur_statut = wx.StaticText(self, -1, u"●")
        self.label_statut = wx.StaticText(self, -1, "")
        self.label_identifiant = wx.StaticText(self, -1, _(u"Identifiant"))
        self.valeur_identifiant = wx.StaticText(self, -1, "")
        self.label_mdp = wx.StaticText(self, -1, _(u"Mot de passe"))
        self.valeur_mdp = wx.StaticText(self, -1, "")
        self.note_mdp = wx.StaticText(self, -1, _(u"Mot de passe personnalisé"))

        self._ConfigurerStyle()
        self._ConstruireLayout()
        self.SetMinSize((Style.px(220), Style.px(104)))
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def _ConfigurerStyle(self):
        self.SetBackgroundColour(self.couleurFond)
        self.SetForegroundColour(Style.couleur("on_surface"))
        self.SetFont(Style.police("body"))

        for controle in (self.label_identifiant, self.label_mdp, self.note_mdp):
            Style.appliquer_texte(
                controle,
                role="body",
                role_texte="on_surface_variant",
                role_fond="surface_container_lowest",
            )
        for controle in (self.valeur_identifiant, self.valeur_mdp):
            Style.appliquer_texte(
                controle,
                role="body",
                role_texte="on_surface",
                role_fond="surface_container_lowest",
            )
        for controle in (self.label_statut, self.indicateur_statut):
            controle.SetFont(Style.police("body_emphasis"))
            controle.SetBackgroundColour(self.couleurFond)
        self.note_mdp.Hide()

    def _ConstruireLayout(self):
        espace = Style.espace(1)
        marge = Style.espace(2)

        statut = wx.BoxSizer(wx.HORIZONTAL)
        statut.Add(self.indicateur_statut, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, espace)
        statut.Add(self.label_statut, 1, wx.ALIGN_CENTER_VERTICAL)

        infos = wx.BoxSizer(wx.VERTICAL)
        infos.Add(self.label_identifiant, 0, wx.TOP, espace)
        infos.Add(self.valeur_identifiant, 0, wx.EXPAND | wx.BOTTOM, espace)
        infos.Add(self.label_mdp, 0, wx.TOP, espace)
        infos.Add(self.valeur_mdp, 0, wx.EXPAND)
        infos.Add(self.note_mdp, 0, wx.TOP, espace)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(statut, 0, wx.EXPAND | wx.ALL, marge)
        principal.Add(infos, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, marge)
        self.SetSizer(principal)
        self.Layout()

    def _WrapValeurs(self):
        try:
            largeur = max(Style.px(120), self.GetClientSize().GetWidth() - Style.espace(4))
        except Exception:
            return
        for controle in (self.label_statut, self.valeur_identifiant, self.valeur_mdp, self.note_mdp):
            try:
                controle.Wrap(largeur)
            except Exception:
                pass

    def OnSize(self, event):
        event.Skip()
        wx.CallAfter(self._WrapValeurs)

    def SetDonnees(self, dictDonnees=None):
        self.dictDonnees = dictDonnees or {}
        self.MAJ()

    def GetDonnees(self):
        return self.dictDonnees

    def _LireMdp(self):
        mdp = self.dictDonnees.get("internet_mdp") or ""
        if mdp.startswith("#@#"):
            mdp = UTILS_Internet.DecrypteMDP(mdp)
        personnalise = mdp.startswith("custom")
        return (_(u"********") if personnalise else mdp), personnalise

    def MAJ(self):
        if not self.dictDonnees:
            self.label_statut.SetLabel("")
            self.valeur_identifiant.SetLabel("")
            self.valeur_mdp.SetLabel("")
            self.note_mdp.Hide()
            self.indicateur_statut.Hide()
            self.Layout()
            return

        actif = self.dictDonnees.get("internet_actif") == 1
        if actif:
            activation = _(u"Compte internet activé")
            role_statut = "success_text"
        else:
            activation = _(u"Compte internet désactivé")
            role_statut = "danger_text"

        identifiant = self.dictDonnees.get("internet_identifiant") or ""
        mdp, personnalise = self._LireMdp()

        couleur_statut = Style.couleur(role_statut)
        self.indicateur_statut.SetForegroundColour(couleur_statut)
        self.label_statut.SetForegroundColour(couleur_statut)
        self.indicateur_statut.Show()
        self.label_statut.SetLabel(str(activation))
        self.valeur_identifiant.SetLabel(str(identifiant))
        self.valeur_mdp.SetLabel(str(mdp))
        self.note_mdp.Show(bool(personnalise))
        self._WrapValeurs()
        self.Layout()
        self.Refresh()

    def GetIdentifiant(self):
        return self.dictDonnees.get("internet_identifiant")

    def GetMdp(self):
        internet_mdp = self.dictDonnees.get("internet_mdp") or ""
        if internet_mdp.startswith("custom"):
            internet_mdp = "********"
        if internet_mdp.startswith("#@#"):
            internet_mdp = UTILS_Internet.DecrypteMDP(internet_mdp)
        return internet_mdp

    def Modifier(self, event):
        from Dlg import DLG_Compte_internet
        dlg = DLG_Compte_internet.Dialog(self, IDfamille=self.IDfamille, IDutilisateur=self.IDutilisateur)
        if self.IDutilisateur is not None:
            dlg.SetDonnees(self.dictDonnees)
        if dlg.ShowModal() == wx.ID_OK:
            self.SetDonnees(dlg.GetDonnees())
        dlg.Destroy()

    def Envoyer_pressepapiers(self, event):
        codes = _(u"Identifiant : %s / Mot de passe : %s") % (self.GetIdentifiant(), self.GetMdp())
        clipdata = wx.TextDataObject()
        clipdata.SetText(codes)
        if wx.TheClipboard.Open():
            try:
                wx.TheClipboard.SetData(clipdata)
            finally:
                wx.TheClipboard.Close()

        dlg = wx.MessageDialog(
            self,
            _(u"Les codes ont été copiés dans le presse-papiers."),
            _(u"Presse-papiers"),
            wx.OK | wx.ICON_INFORMATION,
        )
        dlg.ShowModal()
        dlg.Destroy()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        Style.appliquer_fenetre(panel)
        self.ctrl = CTRL(panel, IDfamille=14)
        self.ctrl.SetDonnees({"internet_actif": 1, "internet_identifiant": "test1", "internet_mdp": "test2"})
        contenu = wx.BoxSizer(wx.VERTICAL)
        contenu.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, Style.espace(2))
        panel.SetSizer(contenu)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(panel, 1, wx.EXPAND)
        self.SetSizer(principal)
        self.Layout()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "COMPTE INTERNET")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
