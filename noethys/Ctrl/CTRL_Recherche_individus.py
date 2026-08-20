#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ol import OL_Individus
from Utils import UTILS_Config
from Utils import UTILS_Interface

ID_CREER_FAMILLE = wx.Window.NewControlId()
ID_MODIFIER_FAMILLE = wx.Window.NewControlId()
ID_SUPPRIMER_FAMILLE = wx.Window.NewControlId()
ID_OUVRIR_GRILLE = 60
ID_OUVRIR_FICHE_IND = 70
ID_PARAMETRES = wx.Window.NewControlId()
ID_OUTILS = wx.Window.NewControlId()


class ToolBar(wx.ToolBar):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TB_FLAT | wx.TB_TEXT | wx.TB_NODIVIDER
        wx.ToolBar.__init__(self, *args, **kwds)

        liste_boutons = [
            {"ID": ID_CREER_FAMILLE, "label": _(u"Ajouter"), "image": "Images/32x32/Famille_ajouter.png", "tooltip": _(u"Créer une nouvelle famille")},
            None,
            {"ID": ID_MODIFIER_FAMILLE, "label": _(u"Modifier"), "image": "Images/32x32/Famille_modifier.png", "tooltip": _(u"Modifier la fiche famille de l'individu sélectionné")},
            {"ID": ID_SUPPRIMER_FAMILLE, "label": _(u"Supprimer"), "image": "Images/32x32/Famille_supprimer.png", "tooltip": _(u"Supprimer ou détacher l'individu sélectionné")},
            None,
            {"ID": ID_OUVRIR_GRILLE, "label": _(u"Calendrier"), "image": "Images/32x32/Calendrier.png", "tooltip": _(u"Ouvrir la grille des consommations de l'individu sélectionné\n(ou double-clic sur la ligne + touche CTRL enfoncée)")},
            {"ID": ID_OUVRIR_FICHE_IND, "label": _(u"Fiche ind."), "image": "Images/32x32/Personnes.png", "tooltip": _(u"Ouvrir la fiche individuelle de l'individu sélectionné\n(ou double-clic sur la ligne + touche SHIFT enfoncée)")},
            None,
            {"ID": ID_PARAMETRES, "label": _(u"Paramètres"), "image": "Images/32x32/Configuration2.png", "tooltip": _(u"Sélectionner les paramètres d'affichage")},
            {"ID": ID_OUTILS, "label": _(u"Outils"), "image": "Images/32x32/Configuration.png", "tooltip": _(u"Outils")},
        ]
        for bouton in liste_boutons:
            if bouton is None:
                self.AddSeparator()
            else:
                bitmap = wx.Bitmap(Chemins.GetStaticPath(bouton["image"]), wx.BITMAP_TYPE_ANY)
                try:
                    self.AddTool(bouton["ID"], bouton["label"], bitmap, wx.NullBitmap, wx.ITEM_NORMAL, bouton["tooltip"], "")
                except Exception:
                    self.AddLabelTool(bouton["ID"], bouton["label"], bitmap, wx.NullBitmap, wx.ITEM_NORMAL, bouton["tooltip"], "")

        self.Bind(wx.EVT_TOOL, self.Ajouter_famille, id=ID_CREER_FAMILLE)
        self.Bind(wx.EVT_TOOL, self.Modifier_famille, id=ID_MODIFIER_FAMILLE)
        self.Bind(wx.EVT_TOOL, self.Supprimer_famille, id=ID_SUPPRIMER_FAMILLE)
        self.Bind(wx.EVT_TOOL, self.Ouvrir_grille, id=ID_OUVRIR_GRILLE)
        self.Bind(wx.EVT_TOOL, self.Ouvrir_fiche_ind, id=ID_OUVRIR_FICHE_IND)
        self.Bind(wx.EVT_TOOL, self.Parametres, id=ID_PARAMETRES)
        self.Bind(wx.EVT_TOOL, self.MenuOutils, id=ID_OUTILS)

        # Les bitmaps restent denses (desktop) mais vivent dans une barre native
        # suffisamment haute pour constituer une vraie cible d'action.
        self.SetToolBitmapSize((32, 32))
        hauteur_cible = int(round(40 * max(1.0, UTILS_Interface.GetEchelle() / 100.0)))
        self.SetMinSize((-1, max(40, min(56, hauteur_cible))))
        self.Realize()

    def Ajouter_famille(self, event):
        self.GetParent().ctrl_listview.Ajouter(None)

    def Modifier_famille(self, event):
        self.GetParent().ctrl_listview.Modifier(None)

    def Supprimer_famille(self, event):
        self.GetParent().ctrl_listview.Supprimer(None)

    def Ouvrir_grille(self, event):
        self.GetParent().ctrl_listview.Modifier(event)

    def Ouvrir_fiche_ind(self, event):
        self.GetParent().ctrl_listview.Modifier(event)

    def Parametres(self, event):
        parametres = UTILS_Config.GetParametre("liste_individus_parametres", defaut="")
        from Dlg import DLG_Selection_individus
        dlg = DLG_Selection_individus.Dialog(self)
        dlg.SetParametres(parametres)
        if dlg.ShowModal() == wx.ID_OK:
            UTILS_Config.SetParametre("liste_individus_parametres", dlg.GetParametres())
        dlg.Destroy()

        self.GetParent().ActualiseParametresAffichage()
        self.GetParent().MAJ()

    def MenuOutils(self, event):
        menuPop = UTILS_Adaptations.Menu()

        ID_ACTUALISER = wx.Window.NewControlId()
        ID_IMPRIMER = wx.Window.NewControlId()
        ID_APERCU = wx.Window.NewControlId()
        ID_EXPORT_EXCEL = wx.Window.NewControlId()
        ID_EXPORT_TEXTE = wx.Window.NewControlId()
        ID_AIDE = wx.Window.NewControlId()

        item = wx.MenuItem(menuPop, ID_APERCU, _(u"Aperçu avant impression"), _(u"Imprimer la liste des effectifs affichée"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Apercu.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=ID_APERCU)

        item = wx.MenuItem(menuPop, ID_IMPRIMER, _(u"Imprimer"), _(u"Imprimer la liste des effectifs affichée"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Imprimante.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=ID_IMPRIMER)

        menuPop.AppendSeparator()

        item = wx.MenuItem(menuPop, ID_EXPORT_TEXTE, _(u"Exporter au format Texte"), _(u"Exporter au format Texte"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Texte2.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.GetParent().ctrl_listview.ExportTexte, id=ID_EXPORT_TEXTE)

        item = wx.MenuItem(menuPop, ID_EXPORT_EXCEL, _(u"Exporter au format Excel"), _(u"Exporter au format Excel"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Excel.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.GetParent().ctrl_listview.ExportExcel, id=ID_EXPORT_EXCEL)

        menuPop.AppendSeparator()

        item = wx.MenuItem(menuPop, ID_ACTUALISER, _(u"Actualiser"), _(u"Actualiser l'affichage"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Actualiser2.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Actualiser, id=ID_ACTUALISER)

        menuPop.AppendSeparator()

        item = wx.MenuItem(menuPop, ID_AIDE, _(u"Aide"), _(u"Aide"))
        item.SetBitmap(wx.Bitmap(Chemins.GetStaticPath("Images/16x16/Aide.png"), wx.BITMAP_TYPE_PNG))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Aide, id=ID_AIDE)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Apercu(self, event):
        self.GetParent().ctrl_listview.Apercu(None)

    def Imprimer(self, event):
        self.GetParent().ctrl_listview.Imprimer(None)

    def Actualiser(self, event):
        self.GetParent().MAJ()

    def Aide(self, event):
        self.GetParent().Aide()


class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, name="recherche_individus", id=-1, style=wx.TAB_TRAVERSAL)

        self.toolBar = ToolBar(self)
        self.ctrl_listview = OL_Individus.ListView(
            self,
            id=-1,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES | wx.LC_VRULES,
        )
        self.ctrl_recherche = OL_Individus.BarreRecherche(self, historique=True)

        self.__set_properties()
        self.__do_layout()

        self.ActualiseParametresAffichage()

    def __set_properties(self):
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

    def __do_layout(self):
        # Le vieux FlexGridSizer n'apportait rien ici : trois éléments verticaux,
        # dont la liste doit absorber tout l'espace disponible.
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.toolBar, 0, wx.EXPAND)
        sizer.Add(self.ctrl_listview, 1, wx.EXPAND)
        sizer.Add(self.ctrl_recherche, 0, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()

    def _AppliqueListeModerne(self):
        """Retire la colonne d'avatars décoratifs du panneau d'accueil.

        La suppression du chargement des images est effectuée ensuite dans
        ``OL_Individus`` ; ici on garantit déjà qu'aucune largeur écran n'est
        gaspillée par cette colonne historique.
        """
        try:
            if self.ctrl_listview.GetColumnCount() > 0:
                self.ctrl_listview.SetColumnWidth(0, 0)
        except Exception:
            pass

    def MAJ(self):
        self.ctrl_listview.MAJ(forceActualisation=True)
        self._AppliqueListeModerne()

    def Aide(self):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Lalistedesindividus")

    def ActualiseParametresAffichage(self):
        parametres = UTILS_Config.GetParametre("liste_individus_parametres", defaut="")
        self.ctrl_listview.SetParametres(parametres)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.ALL | wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = Panel(panel)
        self.ctrl.MAJ()
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, 4)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(1000, 600))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
