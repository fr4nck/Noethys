#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-18 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import html as html_std

import wx
import wx.html as wxhtml

import Chemins
from Utils import UTILS_Internet
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _


def _CouleurHtml(couleur):
    try:
        return "#%02X%02X%02X" % (couleur.Red(), couleur.Green(), couleur.Blue())
    except Exception:
        return "#202020"


class CTRL(wxhtml.HtmlWindow):
    """Résumé compact du compte internet, compatible thèmes et grosse police."""

    def __init__(self, parent, IDfamille=None, IDutilisateur=None, couleurFond=None):
        wxhtml.HtmlWindow.__init__(
            self,
            parent,
            -1,
            style=wx.BORDER_THEME | wxhtml.HW_NO_SELECTION | wx.NO_FULL_REPAINT_ON_RESIZE,
        )
        self.parent = parent
        self.IDfamille = IDfamille
        self.IDutilisateur = IDutilisateur
        self.couleurFond = couleurFond or UTILS_Interface.GetCouleurRole("surface_container_lowest")
        self.dictDonnees = {}

        try:
            police = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
            facteur = UTILS_Interface.GetTailleTexte() / 100.0
            taille = max(8, int(round(police.GetPointSize() * facteur)))
            self.SetStandardFonts(taille, police.GetFaceName(), police.GetFaceName())
        except Exception:
            if "gtk2" in wx.PlatformInfo:
                self.SetStandardFonts()

        self.SetBackgroundColour(self.couleurFond)
        self.SetMinSize((UTILS_UIMetrics.px(220), UTILS_UIMetrics.panel_min_height("dashboard")))
        self.SetBorders(UTILS_UIMetrics.spacing(2))

    def SetDonnees(self, dictDonnees={}):
        self.dictDonnees = dictDonnees
        self.MAJ()

    def GetDonnees(self):
        return self.dictDonnees

    def MAJ(self):
        if not self.dictDonnees:
            self.SetPage("")
            return

        actif = self.dictDonnees.get("internet_actif") == 1
        if actif:
            activation = _(u"Compte internet activé")
            image = "Ok.png"
            role_statut = "success"
        else:
            activation = _(u"Compte internet désactivé")
            image = "Interdit.png"
            role_statut = "danger"

        identifiant = self.dictDonnees.get("internet_identifiant") or ""
        mdp = self.dictDonnees.get("internet_mdp") or ""
        if mdp.startswith("#@#"):
            mdp = UTILS_Internet.DecrypteMDP(mdp)

        mdp_personnalise = mdp.startswith("custom")
        if mdp_personnalise:
            mdp = _(u"********")

        identifiant_html = html_std.escape(str(identifiant))
        mdp_html = html_std.escape(str(mdp))
        activation_html = html_std.escape(str(activation))
        note_mdp = ""
        if mdp_personnalise:
            note_mdp = u"<BR><FONT COLOR=\"%s\">%s</FONT>" % (
                _CouleurHtml(UTILS_Interface.GetCouleurRole("on_surface_variant")),
                html_std.escape(_(u"Mot de passe personnalisé")),
            )

        taille_icone = UTILS_UIMetrics.icon_size("inline")
        chemin_icone = Chemins.GetStaticIconPath("Images/16x16/%s" % image, taille=taille_icone)
        couleur_texte = _CouleurHtml(UTILS_Interface.GetCouleurRole("on_surface"))
        couleur_secondaire = _CouleurHtml(UTILS_Interface.GetCouleurRole("on_surface_variant"))
        couleur_statut = _CouleurHtml(UTILS_Interface.GetCouleurRole(role_statut))

        self.SetPage(u"""
        <CENTER>
        <IMG SRC="%s"><BR>
        <B><FONT COLOR="%s">%s</FONT></B>
        <BR><BR>
        <FONT COLOR="%s"><B>%s</B></FONT><BR>
        <FONT COLOR="%s">%s</FONT>
        <BR><BR>
        <FONT COLOR="%s"><B>%s</B></FONT><BR>
        <FONT COLOR="%s">%s</FONT>%s
        </CENTER>
        """ % (
            chemin_icone,
            couleur_statut,
            activation_html,
            couleur_secondaire,
            html_std.escape(_(u"Identifiant")),
            couleur_texte,
            identifiant_html,
            couleur_secondaire,
            html_std.escape(_(u"Mot de passe")),
            couleur_texte,
            mdp_html,
            note_mdp,
        ))
        self.SetBackgroundColour(self.couleurFond)

    def GetIdentifiant(self):
        return self.dictDonnees["internet_identifiant"]

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
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
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
        self.ctrl = CTRL(panel, IDfamille=14)
        self.ctrl.SetDonnees({"internet_actif": 1, "internet_identifiant": "test1", "internet_mdp": "test2"})
        contenu = wx.BoxSizer(wx.VERTICAL)
        contenu.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(2))
        panel.SetSizer(contenu)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(panel, 1, wx.EXPAND)
        self.SetSizer(principal)
        self.Layout()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
