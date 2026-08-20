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
from Utils import UTILS_Aui
from Utils import UTILS_ColonnesResponsive
from Utils import UTILS_Config
from Utils import UTILS_FluentIcons
from Utils import UTILS_Interface
from Utils import UTILS_Responsive
from Utils import UTILS_UIMetrics

ID_CREER_FAMILLE = wx.Window.NewControlId()
ID_MODIFIER_FAMILLE = wx.Window.NewControlId()
ID_SUPPRIMER_FAMILLE = wx.Window.NewControlId()
ID_OUVRIR_GRILLE = 60
ID_OUVRIR_FICHE_IND = 70
ID_PARAMETRES = wx.Window.NewControlId()
ID_OUTILS = wx.Window.NewControlId()


class ListeIndividusAccueil(OL_Individus.ListView):
    """Vue d'accueil dense sans la colonne d'avatars historique.

    La logique métier reste dans :class:`OL_Individus.ListView` (requêtes,
    filtres, actions, sélection). La présentation de cette vue est déclarée
    explicitement ici et ses colonnes passent par le moteur responsive commun.
    """

    SPECS_COLONNES = (
        (120, 1.4),  # Nom
        (105, 1.0),  # Prénom
        (82, 0.0),   # Date naissance
        (55, 0.0),   # Age
        (150, 2.2),  # Rue
        (58, 0.0),   # CP
        (110, 1.2),  # Ville
        (105, 0.2),  # Tel domicile
        (105, 0.2),  # Tel mobile
        (170, 2.4),  # Email
        (72, 0.0),   # Etat
    )

    def __init__(self, *args, **kwds):
        OL_Individus.ListView.__init__(self, *args, **kwds)
        UTILS_ColonnesResponsive.Installer(self, self.SPECS_COLONNES)

    def InitObjectListView(self):
        def FormateDate(date):
            return OL_Individus.UTILS_Dates.DateDDEnFr(date)

        def FormateAge(age):
            if age is None:
                return ""
            return _(u"%d ans") % age

        def FormateEtat(etat):
            if etat == "archive":
                return _(u"Archivé")
            if etat == "efface":
                return _(u"Effacé")
            return ""

        self.oddRowsBackColor = UTILS_Interface.GetCouleurRole("surface_container_lowest")
        self.evenRowsBackColor = UTILS_Interface.GetCouleurRole("surface")
        self.useExpansionColumn = False

        # Pas de colonne d'icône : les civilités restent une donnée métier mais
        # n'ont aucune raison de consommer une colonne et des bitmaps à l'accueil.
        colonnes = [
            OL_Individus.ColumnDefn(_(u"Nom"), "left", 120, "nom", typeDonnee="texte"),
            OL_Individus.ColumnDefn(_(u"Prénom"), "left", 105, "prenom", typeDonnee="texte"),
            OL_Individus.ColumnDefn(_(u"Date naiss."), "left", 82, "date_naiss", typeDonnee="date", stringConverter=FormateDate),
            OL_Individus.ColumnDefn(_(u"Age"), "left", 55, "age", typeDonnee="entier", stringConverter=FormateAge),
            OL_Individus.ColumnDefn(_(u"Rue"), "left", 150, "rue_resid", typeDonnee="texte"),
            OL_Individus.ColumnDefn(_(u"C.P."), "left", 58, "cp_resid", typeDonnee="texte"),
            OL_Individus.ColumnDefn(_(u"Ville"), "left", 110, "ville_resid", typeDonnee="texte"),
            OL_Individus.ColumnDefn(_(u"Tél. domicile"), "left", 105, "tel_domicile", typeDonnee="texte"),
            OL_Individus.ColumnDefn(_(u"Tél. mobile"), "left", 105, "tel_mobile", typeDonnee="texte"),
            OL_Individus.ColumnDefn(_(u"Email"), "left", 170, "mail", typeDonnee="texte"),
            OL_Individus.ColumnDefn(_(u"État"), "left", 72, "etat", typeDonnee="texte", stringConverter=FormateEtat),
            OL_Individus.ColumnDefn(_(u"Recherche"), "left", 0, "champ_recherche", typeDonnee="texte"),
        ]

        self.SetColumns(colonnes)
        self.SetSortColumn(self.columns[0])
        self.SetObjects(self.donnees)
        wx.CallAfter(UTILS_ColonnesResponsive.Ajuster, self)


class ToolBar(wx.ToolBar):
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TB_FLAT | wx.TB_TEXT | wx.TB_NODIVIDER
        wx.ToolBar.__init__(self, *args, **kwds)

        # Les nouveaux contrôles demandent explicitement un rôle Fluent. Aucun
        # mapping global de chemins historiques n'est nécessaire ici.
        liste_boutons = [
            {"ID": ID_CREER_FAMILLE, "label": _(u"Ajouter"), "icone": "add", "tooltip": _(u"Créer une nouvelle famille")},
            None,
            {"ID": ID_MODIFIER_FAMILLE, "label": _(u"Modifier"), "icone": "edit", "tooltip": _(u"Modifier la fiche famille de l'individu sélectionné")},
            {"ID": ID_SUPPRIMER_FAMILLE, "label": _(u"Supprimer"), "icone": "delete", "tooltip": _(u"Supprimer ou détacher l'individu sélectionné")},
            None,
            {"ID": ID_OUVRIR_GRILLE, "label": _(u"Calendrier"), "icone": "calendar", "tooltip": _(u"Ouvrir la grille des consommations de l'individu sélectionné\n(ou double-clic sur la ligne + touche CTRL enfoncée)")},
            {"ID": ID_OUVRIR_FICHE_IND, "label": _(u"Fiche ind."), "icone": "people", "tooltip": _(u"Ouvrir la fiche individuelle de l'individu sélectionné\n(ou double-clic sur la ligne + touche SHIFT enfoncée)")},
            None,
            {"ID": ID_PARAMETRES, "label": _(u"Paramètres"), "icone": "settings", "tooltip": _(u"Sélectionner les paramètres d'affichage")},
            {"ID": ID_OUTILS, "label": _(u"Outils"), "icone": "settings", "tooltip": _(u"Outils")},
        ]

        taille_bitmap = UTILS_Responsive.GetTailleIcone(24)
        for bouton in liste_boutons:
            if bouton is None:
                self.AddSeparator()
            else:
                bitmap = UTILS_FluentIcons.GetBitmap(bouton["icone"], taille=taille_bitmap)
                if bitmap is None:
                    bitmap = wx.NullBitmap
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

        UTILS_Aui.ConfigurerToolBar(self, taille_base=24, fond_uni=True)
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_low"))
        self.SetMinSize((-1, UTILS_UIMetrics.toolbar_height(avec_libelle=True, icon_px=taille_bitmap)))
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

    def _BitmapMenu(self, image):
        taille = UTILS_Responsive.GetTailleIcone(16)
        return wx.Bitmap(Chemins.GetStaticIconPath(image, taille=taille), wx.BITMAP_TYPE_PNG)

    def MenuOutils(self, event):
        menuPop = UTILS_Adaptations.Menu()

        ID_ACTUALISER = wx.Window.NewControlId()
        ID_IMPRIMER = wx.Window.NewControlId()
        ID_APERCU = wx.Window.NewControlId()
        ID_EXPORT_EXCEL = wx.Window.NewControlId()
        ID_EXPORT_TEXTE = wx.Window.NewControlId()
        ID_AIDE = wx.Window.NewControlId()

        item = wx.MenuItem(menuPop, ID_APERCU, _(u"Aperçu avant impression"), _(u"Imprimer la liste des effectifs affichée"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Apercu.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=ID_APERCU)

        item = wx.MenuItem(menuPop, ID_IMPRIMER, _(u"Imprimer"), _(u"Imprimer la liste des effectifs affichée"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Imprimante.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=ID_IMPRIMER)

        menuPop.AppendSeparator()

        item = wx.MenuItem(menuPop, ID_EXPORT_TEXTE, _(u"Exporter au format Texte"), _(u"Exporter au format Texte"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Texte2.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.GetParent().ctrl_listview.ExportTexte, id=ID_EXPORT_TEXTE)

        item = wx.MenuItem(menuPop, ID_EXPORT_EXCEL, _(u"Exporter au format Excel"), _(u"Exporter au format Excel"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Excel.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.GetParent().ctrl_listview.ExportExcel, id=ID_EXPORT_EXCEL)

        menuPop.AppendSeparator()

        item = wx.MenuItem(menuPop, ID_ACTUALISER, _(u"Actualiser"), _(u"Actualiser l'affichage"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Actualiser2.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Actualiser, id=ID_ACTUALISER)

        menuPop.AppendSeparator()

        item = wx.MenuItem(menuPop, ID_AIDE, _(u"Aide"), _(u"Aide"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Aide.png"))
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
        self.ctrl_listview = ListeIndividusAccueil(
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
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.toolBar, 0, wx.EXPAND)
        sizer.Add(self.ctrl_listview, 1, wx.EXPAND)
        sizer.Add(self.ctrl_recherche, 0, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()

    def MAJ(self):
        self.ctrl_listview.MAJ(forceActualisation=True)

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
