#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-14 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx

from Ctrl import CTRL_Bouton_image
from Dlg import DLG_Filtres_cotisations
from Ol import OL_Liste_cotisations
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _


class CTRL(wx.Panel):
    """Liste des cotisations avec commandes explicites et layout responsive."""

    def __init__(self, parent, filtres=[], codesColonnes=["IDcotisation", "date_debut", "date_fin", "beneficiaires", "rue", "cp", "ville", "nom", "type_cotisation", "unite_cotisation", "numero", "montant", "solde", "date_creation_carte", "depot_nom", "activites", "observations"], checkColonne=True, triColonne="date_debut"):
        wx.Panel.__init__(self, parent, id=-1, name="CTRL_Liste_cotisations", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        self.listviewAvecFooter = OL_Liste_cotisations.ListviewAvecFooter(
            self,
            kwargs={"codesColonnes": codesColonnes, "checkColonne": checkColonne, "triColonne": triColonne},
        )
        self.ctrl_cotisations = self.listviewAvecFooter.GetListview()
        self.ctrl_filtres = DLG_Filtres_cotisations.CTRL_Filtres(self, filtres=filtres, ctrl_cotisations=self.ctrl_cotisations)

        self.bouton_apercu = self._CreerBouton(_(u"Aperçu cotisation"), "Images/16x16/Apercu.png", _(u"Afficher un aperçu de la cotisation sélectionnée"))
        self.bouton_email = self._CreerBouton(_(u"Envoyer"), "Images/16x16/Emails_exp.png", _(u"Envoyer la cotisation sélectionnée par Email"))
        self.bouton_supprimer = self._CreerBouton(_(u"Supprimer"), "Images/16x16/Supprimer.png", _(u"Supprimer la cotisation sélectionnée ou les cotisations cochées"))
        self.bouton_liste_apercu = self._CreerBouton(_(u"Aperçu liste"), "Images/16x16/Apercu.png", _(u"Afficher un aperçu avant impression de cette liste"))
        self.bouton_liste_imprimer = self._CreerBouton(_(u"Imprimer"), "Images/16x16/Imprimante.png", _(u"Imprimer cette liste"))
        self.bouton_liste_export_texte = self._CreerBouton(_(u"Texte"), "Images/16x16/Texte2.png", _(u"Exporter cette liste au format Texte"))
        self.bouton_liste_export_excel = self._CreerBouton(_(u"Excel"), "Images/16x16/Excel.png", _(u"Exporter cette liste au format Excel"))
        self.bouton_configuration = self._CreerBouton(_(u"Configurer"), "Images/16x16/Mecanisme.png", _(u"Configurer les colonnes et l'affichage de la liste"))

        self.ctrl_recherche = OL_Liste_cotisations.CTRL_Outils(self, listview=self.ctrl_cotisations, afficherCocher=True)
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnBoutonApercu, self.bouton_apercu)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonEmail, self.bouton_email)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeApercu, self.bouton_liste_apercu)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeImprimer, self.bouton_liste_imprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeExportTexte, self.bouton_liste_export_texte)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeExportExcel, self.bouton_liste_export_excel)
        self.Bind(wx.EVT_BUTTON, self.ctrl_cotisations.MenuConfigurerListe, self.bouton_configuration)

    def _CreerBouton(self, texte, image, tooltip):
        bouton = CTRL_Bouton_image.CTRL(self, texte=texte, cheminImage=image, tailleImage=(20, 20))
        bouton.SetToolTip(wx.ToolTip(tooltip))
        return bouton

    def __do_layout(self):
        marge = UTILS_UIMetrics.spacing(2)
        espace = UTILS_UIMetrics.spacing(1)
        separation = UTILS_UIMetrics.spacing(3)

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
        actions.Add(self.bouton_configuration, 0)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(self.ctrl_filtres, 0, wx.EXPAND | wx.BOTTOM, marge)
        principal.Add(actions, 0, wx.EXPAND | wx.BOTTOM, marge)
        principal.Add(self.listviewAvecFooter, 1, wx.EXPAND)
        principal.Add(self.ctrl_recherche, 0, wx.EXPAND | wx.TOP, marge)
        self.SetSizer(principal)
        self.SetMinSize((UTILS_UIMetrics.px(620), UTILS_UIMetrics.px(300)))
        self.Layout()

    def OnBoutonApercu(self, event):
        self.ctrl_cotisations.Reedition(None)

    def OnBoutonEmail(self, event):
        self.ctrl_cotisations.EnvoyerEmail(None)

    def OnBoutonSupprimer(self, event):
        self.ctrl_cotisations.Supprimer(None)

    def OnBoutonListeApercu(self, event):
        self.ctrl_cotisations.Apercu(None)

    def OnBoutonListeImprimer(self, event):
        self.ctrl_cotisations.Imprimer(None)

    def OnBoutonListeExportTexte(self, event):
        self.ctrl_cotisations.ExportTexte(None)

    def OnBoutonListeExportExcel(self, event):
        self.ctrl_cotisations.ExportExcel(None)

    def GetTracksCoches(self):
        return self.ctrl_cotisations.GetTracksCoches()

    def GetTracksTous(self):
        return self.ctrl_cotisations.GetTracksTous()

    def MAJ(self):
        self.ctrl_cotisations.MAJ()

    def SetFiltres(self, filtres=[]):
        self.ctrl_cotisations.SetFiltres(filtres)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        self.ctrl = CTRL(panel)
        self.ctrl.MAJ()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(2))
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
