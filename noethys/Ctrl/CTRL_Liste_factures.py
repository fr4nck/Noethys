#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx

from Ctrl import CTRL_ActionRepens
from Ctrl import CTRL_OutilsListeRepens
from Dlg import DLG_Filtres_factures
from Ol import OL_Factures
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


class CTRL(wx.Panel):
    """Liste des factures avec barre d'actions desktop explicite."""

    def __init__(self, parent, filtres=[], codesColonnes=["IDfacture", "date", "numero", "famille", "prelevement", "email", "total", "solde", "solde_actuel", "date_echeance", "nom_lot"], checkColonne=True, triColonne="numero"):
        wx.Panel.__init__(self, parent, id=-1, name="CTRL_Liste_factures", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        Style.appliquer_fenetre(self, "surface")

        self.listviewAvecFooter = OL_Factures.ListviewAvecFooter(
            self,
            kwargs={"codesColonnes": codesColonnes, "checkColonne": checkColonne, "triColonne": triColonne},
        )
        self.ctrl_factures = self.listviewAvecFooter.GetListview()
        self.ctrl_filtres = DLG_Filtres_factures.CTRL_Filtres(self, filtres=filtres, ctrl_factures=self.ctrl_factures)

        self.bouton_apercu = self._CreerBouton(
            _(u"Aperçu facture"),
            _(u"Afficher un aperçu de la facture sélectionnée"),
        )
        self.bouton_email = self._CreerBouton(
            _(u"Envoyer"),
            _(u"Envoyer la facture sélectionnée par Email"),
            icone="mail",
        )
        self.bouton_supprimer = self._CreerBouton(
            _(u"Supprimer"),
            _(u"Supprimer la facture sélectionnée ou les factures cochées"),
            icone="delete",
            variante="danger",
        )
        self.bouton_liste_apercu = self._CreerBouton(
            _(u"Aperçu liste"),
            _(u"Afficher un aperçu avant impression de cette liste"),
        )
        self.bouton_liste_imprimer = self._CreerBouton(
            _(u"Imprimer"),
            _(u"Imprimer cette liste"),
        )
        self.bouton_liste_export_texte = self._CreerBouton(
            _(u"Texte"),
            _(u"Exporter cette liste au format Texte"),
            variante="ghost",
        )
        self.bouton_liste_export_excel = self._CreerBouton(
            _(u"Excel"),
            _(u"Exporter cette liste au format Excel"),
            variante="ghost",
        )

        self.ctrl_recherche = CTRL_OutilsListeRepens.BarreRecherche(self, listview=self.ctrl_factures)
        self.ctrl_afficher_annulations = wx.CheckBox(self, -1, _(u"Afficher les factures annulées"))
        self.ctrl_afficher_annulations.SetToolTip(wx.ToolTip(_(u"Afficher les factures annulées dans la liste")))
        Style.appliquer_texte(
            self.ctrl_afficher_annulations,
            role="body",
            role_texte="on_surface",
            role_fond="surface",
        )

        self.bouton_tout = self._CreerBouton(
            _(u"Tout cocher"),
            _(u"Cocher toutes les factures affichées"),
            variante="ghost",
        )
        self.bouton_rien = self._CreerBouton(
            _(u"Tout décocher"),
            _(u"Décocher toutes les factures affichées"),
            variante="ghost",
        )
        # Alias conservés pour les éventuels appels historiques externes.
        self.hyper_tout = self.bouton_tout
        self.hyper_rien = self.bouton_rien

        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonApercu, self.bouton_apercu)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonEmail, self.bouton_email)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeApercu, self.bouton_liste_apercu)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeImprimer, self.bouton_liste_imprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeExportTexte, self.bouton_liste_export_texte)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeExportExcel, self.bouton_liste_export_excel)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonTout, self.bouton_tout)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonRien, self.bouton_rien)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckAnnulations, self.ctrl_afficher_annulations)

    def _CreerBouton(self, texte, tooltip, icone=None, variante="secondaire"):
        return CTRL_ActionRepens.CTRL(
            self,
            label=texte,
            icone=icone,
            variante=variante,
            tooltip=tooltip,
            compact=True,
        )

    def __do_layout(self):
        marge = Style.espace(2)
        espace = Style.espace(1)
        separation = Style.espace(3)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        for bouton in (self.bouton_apercu, self.bouton_email, self.bouton_supprimer):
            actions.Add(bouton, 0, wx.RIGHT, espace)
        actions.AddSpacer(separation)
        for bouton in (
            self.bouton_liste_apercu,
            self.bouton_liste_imprimer,
            self.bouton_liste_export_texte,
            self.bouton_liste_export_excel,
        ):
            actions.Add(bouton, 0, wx.RIGHT, espace)
        actions.AddStretchSpacer(1)

        outils = wx.BoxSizer(wx.HORIZONTAL)
        outils.Add(self.ctrl_recherche, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, separation)
        outils.Add(self.ctrl_afficher_annulations, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, separation)
        outils.Add(self.bouton_tout, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, espace)
        outils.Add(self.bouton_rien, 0, wx.ALIGN_CENTER_VERTICAL)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(self.ctrl_filtres, 0, wx.EXPAND | wx.BOTTOM, marge)
        principal.Add(actions, 0, wx.EXPAND | wx.BOTTOM, marge)
        principal.Add(self.listviewAvecFooter, 1, wx.EXPAND)
        principal.Add(outils, 0, wx.EXPAND | wx.TOP, marge)
        self.SetSizer(principal)
        self.SetMinSize((Style.px(620), Style.px(300)))
        self.Layout()

    def OnBoutonApercu(self, event):
        self.ctrl_factures.Reedition(None)

    def OnBoutonEmail(self, event):
        self.ctrl_factures.EnvoyerEmail(None)

    def OnBoutonSupprimer(self, event):
        self.ctrl_factures.Supprimer(None)

    def OnBoutonListeApercu(self, event):
        self.ctrl_factures.Apercu(None)

    def OnBoutonListeImprimer(self, event):
        self.ctrl_factures.Imprimer(None)

    def OnBoutonListeExportTexte(self, event):
        self.ctrl_factures.ExportTexte(None)

    def OnBoutonListeExportExcel(self, event):
        self.ctrl_factures.ExportExcel(None)

    def OnBoutonTout(self, event=None):
        self.ctrl_factures.CocheListeTout()

    def OnBoutonRien(self, event=None):
        self.ctrl_factures.CocheListeRien()

    def GetTracksCoches(self):
        return self.ctrl_factures.GetTracksCoches()

    def GetTracksTous(self):
        return self.ctrl_factures.GetTracksTous()

    def MAJ(self):
        self.ctrl_factures.MAJ()

    def SetFiltres(self, filtres=[]):
        self.ctrl_factures.SetFiltres(filtres)

    def OnCheckAnnulations(self, event=None):
        self.ctrl_factures.afficherAnnulations = self.ctrl_afficher_annulations.GetValue()
        self.MAJ()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(panel, "surface")
        self.ctrl = CTRL(panel)
        self.ctrl.MAJ()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, Style.espace(2))
        panel.SetSizer(sizer)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(panel, 1, wx.EXPAND)
        self.SetSizer(principal)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, _(u"TEST"), size=(1000, 600))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
