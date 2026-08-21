#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:          Licence GNU GPL
#-----------------------------------------------------------

from Utils.UTILS_Traduction import _
from Utils import UTILS_IconesRepens
from Utils import UTILS_StyleRepens as Style
import wx
from Ctrl import CTRL_Bouton_image
import GestionDB


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
    """Recherche de facture compacte, thémée et compatible DPI."""

    def __init__(self, parent, size=wx.DefaultSize, IDfamille=None):
        _ConfigurerBarreShell(parent)
        wx.SearchCtrl.__init__(self, parent, size=size, style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.IDfamille = IDfamille
        self.IDutilisateurActif = None
        self.SetDescriptiveText(_(u"N° de facture"))
        Style.appliquer_saisie(self)

        self.ShowSearchButton(True)
        self.ShowCancelButton(False)
        try:
            bitmap = UTILS_IconesRepens.GetBitmap(
                "search",
                taille=Style.taille_icone("inline"),
                role="on_surface_variant",
            )
            if bitmap is not None and bitmap.IsOk():
                self.SetSearchBitmap(bitmap)
        except Exception:
            pass

        try:
            largeur_min = max(Style.px(120), self.GetMinSize().GetWidth())
            self.SetMinSize((largeur_min, Style.cible_action("compact")))
        except Exception:
            pass

        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.Recherche)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.Recherche)
        self.Bind(wx.EVT_TEXT, self.OnText)

    def OnCancel(self, evt):
        self.SetValue("")

    def OnText(self, event):
        txtSearch = self.GetValue()
        self.ShowCancelButton(bool(txtSearch))
        if len(txtSearch) > 6 and txtSearch.startswith("F") and "-" not in txtSearch:
            numFacture = txtSearch[1:]
            self.ReglerFacture(numFacture)
            self.SetValue("")

    def Recherche(self, event):
        self.ReglerFacture(self.GetValue())

    def ReglerFacture(self, numFacture=None):
        if self.IDfamille is not None:
            texteSupp = _(u"pour cette famille ")
            conditionFamille = " AND comptes_payeurs.IDfamille=%d" % self.IDfamille
        else:
            texteSupp = u""
            conditionFamille = ""

        try:
            if "-" in numFacture:
                prefixe, numero = numFacture.split("-")
                numero = int(numero)
                conditionNumero = u"WHERE factures_prefixes.prefixe='%s' AND factures.numero=%d" % (prefixe, numero)
            else:
                numero = int(numFacture)
                conditionNumero = u"WHERE factures.numero=%d" % numero
        except Exception:
            conditionNumero = None

        if conditionNumero is None:
            dlg = wx.MessageDialog(self, _(u"Ce numéro de facture ne semble pas valide !"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        DB = GestionDB.DB()
        req = u"""
        SELECT
        factures.IDfacture, factures.total, factures.regle, factures.solde,
        SUM(ventilation.montant), etat,
        comptes_payeurs.IDfamille
        FROM factures
        LEFT JOIN prestations ON prestations.IDfacture = factures.IDfacture
        LEFT JOIN ventilation ON prestations.IDprestation = ventilation.IDprestation
        LEFT JOIN comptes_payeurs ON comptes_payeurs.IDcompte_payeur = factures.IDcompte_payeur
        LEFT JOIN factures_prefixes ON factures_prefixes.IDprefixe = factures.IDprefixe
        %s %s
        GROUP BY factures.IDfacture
        ;""" % (conditionNumero, conditionFamille)
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        DB.Close()

        if len(listeDonnees) == 0:
            dlg = wx.MessageDialog(self, _(u"Ce numéro ne correspond à aucune facture existante %s!") % texteSupp, _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        IDfacture, totalInitial, regleInitial, soldeInitial, regleActuel, etat, IDfamille = listeDonnees[0]
        if etat == "annulation":
            dlg = wx.MessageDialog(self, _(u"La facture n°%s a été annulée !") % numFacture, _(u"Facture annulée"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        DB = GestionDB.DB()
        req = """SELECT IDfacture, SUM(montant)
        FROM prestations
        WHERE IDfacture=%d
        GROUP BY IDfacture
        ;""" % IDfacture
        DB.ExecuterReq(req)
        listeDonnees = DB.ResultatReq()
        totalActuel = listeDonnees[0][1] if listeDonnees else 0.0
        DB.Close()

        if totalActuel is None:
            totalActuel = 0.0
        if regleActuel is None:
            regleActuel = 0.0
        if totalActuel - regleActuel == 0.0:
            dlg = wx.MessageDialog(self, _(u"La facture n°%s a déjà été réglée en intégralité !") % numFacture, _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        if self.IDfamille is not None:
            self.GetGrandParent().ReglerFacture()
        else:
            from Dlg import DLG_Famille
            dlg = DLG_Famille.Dialog(self, IDfamille=IDfamille, AfficherMessagesOuverture=False)
            dlg.ReglerFacture(IDfacture)
            dlg.ShowModal()
            dlg.Destroy()

        self.SetValue("")
        if self.GetParent().GetName() == "DLG_Regler_facture":
            self.GetParent().Destroy()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(self, "surface")
        Style.appliquer_fenetre(panel, "surface")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer_1)
        self.myOlv = CTRL(panel)
        self.myOlv2 = wx.TextCtrl(panel, -1, "test")
        Style.appliquer_saisie(self.myOlv2)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.myOlv, 0, wx.ALL | wx.EXPAND, Style.espace(2))
        sizer_2.Add(self.myOlv2, 0, wx.ALL | wx.EXPAND, Style.espace(2))
        panel.SetSizer(sizer_2)
        self.SetSize((500, 150))
        self.Layout()
        self.CenterOnScreen()


class Dialog(wx.Dialog):
    """Saisie d'un numéro de facture sans grille/spacer historique."""

    def __init__(self, parent, id=-1, title=_(u"Régler une facture"), IDfamille=None):
        wx.Dialog.__init__(self, parent, id, title, name="DLG_Regler_facture", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.parent = parent
        self.IDfamille = IDfamille
        Style.appliquer_fenetre(self, "surface")

        self.label = wx.StaticText(self, -1, _(u"Saisissez le numéro de la facture à régler ou scannez directement son code-barres."))
        Style.appliquer_texte(self.label, role="body", role_texte="on_surface", role_fond="surface")
        self.ctrl_mdp = CTRL(self, IDfamille=self.IDfamille)
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_(u"Annuler"), iconeFluent="dismiss")

        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Annuler")))
        self.__do_layout()

    def __do_layout(self):
        marge = Style.espace(4)
        espace = Style.espace(3)

        contenu = wx.BoxSizer(wx.VERTICAL)
        contenu.Add(self.label, 0, wx.EXPAND | wx.BOTTOM, espace)
        contenu.Add(self.ctrl_mdp, 0, wx.EXPAND)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_annuler, 0)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(contenu, 1, wx.EXPAND | wx.ALL, marge)
        principal.Add(actions, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, marge)
        self.SetSizer(principal)

        self.SetMinSize((Style.px(360), -1))
        self.Fit()
        hauteur = max(self.GetSize().GetHeight(), Style.px(150))
        ecran = wx.GetClientDisplayRect()
        largeur = max(Style.px(420), min(Style.px(620), int(ecran.GetWidth() * 0.42)))
        self.SetSize((largeur, hauteur))
        self.Layout()
        if parent_valide(self.GetParent()):
            self.CentreOnParent()
        else:
            self.CentreOnScreen()
        wx.CallAfter(self.ctrl_mdp.SetFocus)


def parent_valide(parent):
    try:
        return parent is not None and bool(parent)
    except Exception:
        return False


if __name__ == '__main__':
    app = wx.App(0)
    dlg = Dialog(None)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()
