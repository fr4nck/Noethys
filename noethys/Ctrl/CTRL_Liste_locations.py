#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-17 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx

from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_OutilsListeRepens
from Ol import OL_Locations
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _


class CTRL(wx.Panel):
    """Liste des locations avec commandes nommées et outils regroupés."""

    def __init__(self, parent, filtres=[]):
        wx.Panel.__init__(self, parent, id=-1, name="CTRL_Liste_locations", style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        self.listviewAvecFooter = OL_Locations.ListviewAvecFooter(self, kwargs={"checkColonne": True})
        self.ctrl_locations = self.listviewAvecFooter.GetListview()

        self.bouton_apercu = self._CreerBouton(_(u"Aperçu location"), "Images/16x16/Apercu.png", _(u"Afficher un aperçu de la location sélectionnée"))
        self.bouton_email = self._CreerBouton(_(u"Envoyer"), "Images/16x16/Emails_exp.png", _(u"Envoyer la location sélectionnée par Email"))
        self.bouton_supprimer = self._CreerBouton(_(u"Supprimer"), "Images/16x16/Supprimer.png", _(u"Supprimer la location sélectionnée ou les locations cochées"))
        self.bouton_liste_apercu = self._CreerBouton(_(u"Aperçu liste"), "Images/16x16/Apercu.png", _(u"Afficher un aperçu avant impression de cette liste"))
        self.bouton_liste_imprimer = self._CreerBouton(_(u"Imprimer"), "Images/16x16/Imprimante.png", _(u"Imprimer cette liste"))
        self.bouton_liste_export_texte = self._CreerBouton(_(u"Texte"), "Images/16x16/Texte2.png", _(u"Exporter cette liste au format Texte"))
        self.bouton_liste_export_excel = self._CreerBouton(_(u"Excel"), "Images/16x16/Excel.png", _(u"Exporter cette liste au format Excel"))

        self.ctrl_recherche = CTRL_OutilsListeRepens.CTRL(
            self,
            listview=self.ctrl_locations,
            afficherCocher=True,
        )
        self.check_locations_actives = wx.CheckBox(self, -1, _(u"Locations en cours uniquement"))
        self.check_locations_actives.SetValue(True)
        self.check_locations_actives.SetToolTip(wx.ToolTip(_(u"Afficher uniquement les locations actives")))
        try:
            police = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
            facteur = UTILS_Interface.GetTailleTexte() / 100.0
            police.SetPointSize(max(8, int(round(police.GetPointSize() * facteur))))
            self.check_locations_actives.SetFont(police)
        except Exception:
            pass

        self.__do_layout()

        self.Bind(wx.EVT_CHECKBOX, self.OnCheckActives, self.check_locations_actives)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonApercu, self.bouton_apercu)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonEmail, self.bouton_email)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonSupprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeApercu, self.bouton_liste_apercu)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeImprimer, self.bouton_liste_imprimer)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeExportTexte, self.bouton_liste_export_texte)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonListeExportExcel, self.bouton_liste_export_excel)

        self.ctrl_locations.afficher_uniquement_actives = self.check_locations_actives.GetValue()

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

        outils = wx.BoxSizer(wx.HORIZONTAL)
        outils.Add(self.ctrl_recherche, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, separation)
        outils.Add(self.check_locations_actives, 0, wx.ALIGN_CENTER_VERTICAL)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(actions, 0, wx.EXPAND | wx.BOTTOM, marge)
        principal.Add(self.listviewAvecFooter, 1, wx.EXPAND)
        principal.Add(outils, 0, wx.EXPAND | wx.TOP, marge)
        self.SetSizer(principal)
        self.SetMinSize((UTILS_UIMetrics.px(600), UTILS_UIMetrics.px(300)))
        self.Layout()

    def OnCheckActives(self, event):
        self.ctrl_locations.afficher_uniquement_actives = self.check_locations_actives.GetValue()
        self.ctrl_locations.MAJ()

    def OnBoutonApercu(self, event):
        self.ctrl_locations.Reedition(None)

    def OnBoutonEmail(self, event):
        self.ctrl_locations.EnvoyerEmail(None)

    def OnBoutonSupprimer(self, event):
        self.ctrl_locations.Supprimer(None)

    def OnBoutonListeApercu(self, event):
        self.ctrl_locations.Apercu(None)

    def OnBoutonListeImprimer(self, event):
        self.ctrl_locations.Imprimer(None)

    def OnBoutonListeExportTexte(self, event):
        self.ctrl_locations.ExportTexte(None)

    def OnBoutonListeExportExcel(self, event):
        self.ctrl_locations.ExportExcel(None)

    def GetTracksCoches(self):
        return self.ctrl_locations.GetTracksCoches()

    def GetTracksTous(self):
        return self.ctrl_locations.GetTracksTous()

    def MAJ(self):
        self.ctrl_locations.MAJ()

    def SetFiltres(self, filtres=[]):
        self.ctrl_locations.SetFiltres(filtres)


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
