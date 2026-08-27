#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
from Utils import UTILS_Interventions
import wx
import GestionDB
from Ctrl import CTRL_Bouton_image
from Ctrl import CTRL_Bandeau
from Ol import OL_Ecoles


class ListViewEcoles(OL_Ecoles.ListView):
    """Liste historique enrichie du garde d'intégrité Noe-062B."""

    def Supprimer(self, event):
        selection = self.Selection()
        if len(selection) > 0:
            IDecole = selection[0].IDecole
            DB = GestionDB.DB()
            try:
                nbre_seances = UTILS_Interventions.CompterInterventionsEcoleHistorique(DB, IDecole)
            except Exception as err:
                dlg = wx.MessageDialog(
                    self,
                    _(u"Impossible de vérifier les séances rattachées à cette école.\nLa suppression est bloquée par sécurité.\n\n%s") % str(err),
                    _(u"Avertissement"),
                    wx.OK | wx.ICON_EXCLAMATION,
                )
                dlg.ShowModal()
                dlg.Destroy()
                return
            finally:
                DB.Close()

            if nbre_seances > 0:
                dlg = wx.MessageDialog(
                    self,
                    _(u"Cette école possède déjà %d séance(s) de sport enregistrée(s).\nVous ne pouvez donc la supprimer : son historique doit rester rattaché à la même dénomination.") % nbre_seances,
                    _(u"Avertissement"),
                    wx.OK | wx.ICON_EXCLAMATION,
                )
                dlg.ShowModal()
                dlg.Destroy()
                return

        return OL_Ecoles.ListView.Supprimer(self, event)


class Dialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, name="DLG_Ecoles", style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        
        intro = _(u"Vous pouvez ici saisir, modifier ou supprimer des écoles. Vous pouvez renseigner les coordonnées de l'établissement ainsi que les secteurs géographiques rattachés. Vous pourrez ensuite inscrire les individus dans ces écoles depuis les fiches individuelles.")
        titre = _(u"Gestion des écoles")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Ecole.png")
        self.ctrl_listview = ListViewEcoles(self, id=-1, style=wx.LC_REPORT|wx.SUNKEN_BORDER|wx.LC_SINGLE_SEL|wx.LC_HRULES|wx.LC_VRULES)
        self.ctrl_listview.SetMinSize((50, 50))
        self.ctrl_listview.MAJ()
        self.ctrl_recherche = OL_Ecoles.CTRL_Outils(self, listview=self.ctrl_listview)
        
        self.bouton_ajouter = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Ajouter.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_modifier = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Modifier.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_supprimer = wx.BitmapButton(self, -1, wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Supprimer.png"), wx.BITMAP_TYPE_ANY))
        self.bouton_seances_sport = wx.Button(self, -1, _(u"Séances sport"))
        
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_(u"Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_fermer = CTRL_Bouton_image.CTRL(self, id=wx.ID_CANCEL, texte=_(u"Fermer"), cheminImage="Images/32x32/Fermer.png")
            
        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_BUTTON, self.Ajouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.Modifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.Supprimer, self.bouton_supprimer)
        self.Bind(wx.EVT_BUTTON, self.SeancesSport, self.bouton_seances_sport)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)


    def __set_properties(self):
        self.bouton_ajouter.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour ajouter une école")))
        self.bouton_modifier.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour modifier l'école sélectionnée dans la liste")))
        self.bouton_supprimer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour supprimer l'école sélectionnée dans la liste")))
        self.bouton_seances_sport.SetToolTip(wx.ToolTip(_(u"Enregistrer les séances de sport de l'école sélectionnée")))
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour obtenir de l'aide")))
        self.bouton_fermer.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour fermer")))
        self.SetMinSize((750, 600))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_contenu = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=5)
        grid_sizer_droit = wx.FlexGridSizer(rows=5, cols=1, vgap=5, hgap=5)
        grid_sizer_gauche = wx.FlexGridSizer(rows=3, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
        grid_sizer_gauche.Add(self.ctrl_listview, 0, wx.EXPAND, 0)
        grid_sizer_gauche.Add(self.ctrl_recherche, 0, wx.EXPAND, 0)
        grid_sizer_gauche.AddGrowableRow(0)
        grid_sizer_gauche.AddGrowableCol(0)
        grid_sizer_contenu.Add(grid_sizer_gauche, 1, wx.EXPAND, 0)
        grid_sizer_droit.Add(self.bouton_ajouter, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_modifier, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_supprimer, 0, 0, 0)
        grid_sizer_droit.Add(self.bouton_seances_sport, 0, wx.TOP, 10)
        grid_sizer_contenu.Add(grid_sizer_droit, 1, wx.EXPAND, 0)
        grid_sizer_contenu.AddGrowableRow(0)
        grid_sizer_contenu.AddGrowableCol(0)
        grid_sizer_base.Add(grid_sizer_contenu, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_fermer, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen()

    def Ajouter(self, event):
        self.ctrl_listview.Ajouter(None)
        
    def Modifier(self, event):
        self.ctrl_listview.Modifier(None)

    def Supprimer(self, event):
        self.ctrl_listview.Supprimer(None)

    def SeancesSport(self, event):
        selection = self.ctrl_listview.Selection()
        if len(selection) == 0:
            dlg = wx.MessageDialog(
                self,
                _(u"Sélectionnez d'abord une école pour enregistrer ses séances de sport."),
                _(u"Séances sport"),
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return
        ecole = selection[0]
        from Dlg import DLG_Seances_sport_ecoles
        dlg = DLG_Seances_sport_ecoles.Dialog(self, IDecole=ecole.IDecole, nom_ecole=ecole.nom)
        dlg.ShowModal()
        dlg.Destroy()
            
    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Ecoles")


if __name__ == "__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dialog_1 = Dialog(None)
    app.SetTopWindow(dialog_1)
    dialog_1.ShowModal()
    app.MainLoop()