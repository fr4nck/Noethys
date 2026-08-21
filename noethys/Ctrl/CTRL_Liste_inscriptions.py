#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-18 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx

from Ctrl import CTRL_ActionRepens
from Ctrl import CTRL_OutilsListeRepens
from Ol import OL_Liste_inscriptions
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


class CTRL(wx.Panel):
    """Liste des inscriptions avec commandes nommées et surface responsive."""

    def __init__(self, parent, filtres=[], nomListe="OL_Liste_inscriptions"):
        wx.Panel.__init__(self, parent, id=-1, name="CTRL_Liste_inscriptions", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        Style.appliquer_fenetre(self, "surface")

        self.listviewAvecFooter = OL_Liste_inscriptions.ListviewAvecFooter(
            self,
            kwargs={"checkColonne": True, "nomListe": nomListe},
        )
        self.ctrl_inscriptions = self.listviewAvecFooter.GetListview()

        self.bouton_apercu = self._CreerBouton(
            _(u"Aperçu inscription"),
            _(u"Afficher un aperçu de l'inscription sélectionnée"),
        )
        self.bouton_email = self._CreerBouton(
            _(u"Envoyer"),
            _(u"Envoyer l'inscription sélectionnée par Email"),
            icone="mail",
        )
        # L'action suppression reste volontairement non reliée comme dans le code historique.
        self.bouton_supprimer = self._CreerBouton(
            _(u"Supprimer"),
            _(u"Supprimer l'inscription sélectionnée"),
            icone="delete",
            variante="danger",
        )
        self.bouton_supprimer.Hide()
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

        self.ctrl_recherche = CTRL_OutilsListeRepens.CTRL(
            self,
            listview=self.ctrl_inscriptions,
            afficherCocher=True,
        )
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonApercu, self.bouton_apercu)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonEmail, self.bouton_email)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeApercu, self.bouton_liste_apercu)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeImprimer, self.bouton_liste_imprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeExportTexte, self.bouton_liste_export_texte)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeExportExcel, self.bouton_liste_export_excel)

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
        for bouton in (self.bouton_apercu, self.bouton_email):
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

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(actions, 0, wx.EXPAND | wx.BOTTOM, marge)
        principal.Add(self.listviewAvecFooter, 1, wx.EXPAND)
        principal.Add(self.ctrl_recherche, 0, wx.EXPAND | wx.TOP, marge)
        self.SetSizer(principal)
        self.SetMinSize((Style.px(600), Style.px(300)))
        self.Layout()

    def OnBoutonApercu(self, event):
        self.ctrl_inscriptions.ImprimerPDF(None)

    def OnBoutonEmail(self, event):
        self.ctrl_inscriptions.EnvoyerEmail(None)

    def OnBoutonSupprimer(self, event):
        self.ctrl_inscriptions.Supprimer(None)

    def OnBoutonListeApercu(self, event):
        self.ctrl_inscriptions.Apercu(None)

    def OnBoutonListeImprimer(self, event):
        self.ctrl_inscriptions.Imprimer(None)

    def OnBoutonListeExportTexte(self, event):
        self.ctrl_inscriptions.ExportTexte(None)

    def OnBoutonListeExportExcel(self, event):
        self.ctrl_inscriptions.ExportExcel(None)

    def GetTracksCoches(self):
        return self.ctrl_inscriptions.GetTracksCoches()

    def GetTracksTous(self):
        return self.ctrl_inscriptions.GetTracksTous()

    def MAJ(self):
        self.ctrl_inscriptions.MAJ(IDactivite=0, listeGroupes=None, listeCategories=None)

    def SetFiltres(self, filtres=[]):
        self.ctrl_inscriptions.SetFiltres(filtres)


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
