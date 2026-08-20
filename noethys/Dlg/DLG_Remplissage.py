#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import datetime
import wx

from Utils.UTILS_Traduction import _
from Utils import UTILS_Adaptations
from Utils import UTILS_Aui
from Utils import UTILS_Config
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Ctrl import CTRL_Remplissage
from Ctrl import CTRL_Ticker_presents

AFFICHE_PRESENTS = 1
MAJ_AUTO_REMPLISSAGE = 0
MAJ_AUTO_EN_ATTENTE = None

ID_MODE_PLACES_INITIALES = wx.Window.NewControlId()
ID_MODE_PLACES_PRISES = wx.Window.NewControlId()
ID_MODE_PLACES_RESTANTES = wx.Window.NewControlId()
ID_MODE_PLACES_ATTENTE = wx.Window.NewControlId()
ID_LISTE_ATTENTE = wx.Window.NewControlId()
ID_PARAMETRES = wx.Window.NewControlId()
ID_OUTILS = wx.Window.NewControlId()


class ToolBar(wx.ToolBar):
    """Barre de commandes du tableau de bord.

    Sa géométrie ne dépend plus de ``32x32`` écrit en dur : icônes, padding et
    hauteur sont fournis par la couche commune. Les libellés restent présents,
    indispensables pour une application métier utilisée à distance d'écran.
    """

    def __init__(self, *args, **kwds):
        kwds["style"] = wx.TB_FLAT | wx.TB_TEXT | wx.TB_NODIVIDER
        wx.ToolBar.__init__(self, *args, **kwds)

        liste_boutons = [
            {"ID": ID_MODE_PLACES_INITIALES, "label": _(u"Places max."), "image": "Images/32x32/Places_max.png", "type": wx.ITEM_RADIO, "tooltip": _(u"Afficher le nombre de places maximal initial")},
            {"ID": ID_MODE_PLACES_PRISES, "label": _(u"Places prises"), "image": "Images/32x32/Places_prises.png", "type": wx.ITEM_RADIO, "tooltip": _(u"Afficher le nombre de places prises")},
            {"ID": ID_MODE_PLACES_RESTANTES, "label": _(u"Places dispo."), "image": "Images/32x32/Places_dispo.png", "type": wx.ITEM_RADIO, "tooltip": _(u"Afficher le nombre de places restantes")},
            {"ID": ID_MODE_PLACES_ATTENTE, "label": _(u"Places attente"), "image": "Images/32x32/Places_attente.png", "type": wx.ITEM_RADIO, "tooltip": _(u"Afficher le nombre de places en attente")},
            None,
            {"ID": ID_LISTE_ATTENTE, "label": _(u"Liste d'attente"), "image": "Images/32x32/Liste_attente.png", "type": wx.ITEM_NORMAL, "tooltip": _(u"Afficher la liste d'attente")},
            None,
            {"ID": ID_PARAMETRES, "label": _(u"Paramètres"), "image": "Images/32x32/Configuration2.png", "type": wx.ITEM_NORMAL, "tooltip": _(u"Sélectionner les paramètres d'affichage")},
            {"ID": ID_OUTILS, "label": _(u"Outils"), "image": "Images/32x32/Configuration.png", "type": wx.ITEM_NORMAL, "tooltip": _(u"Outils")},
        ]

        for bouton in liste_boutons:
            if bouton is None:
                self.AddSeparator()
                continue
            bitmap = UTILS_Aui.ChargerBitmapToolBar(bouton["image"], taille_base=24)
            try:
                self.AddTool(
                    bouton["ID"], bouton["label"], bitmap, wx.NullBitmap,
                    bouton["type"], bouton["tooltip"], "",
                )
            except Exception:
                self.AddLabelTool(
                    bouton["ID"], bouton["label"], bitmap, wx.NullBitmap,
                    bouton["type"], bouton["tooltip"], "",
                )

        self.Bind(wx.EVT_TOOL, self.Mode_places_initiales, id=ID_MODE_PLACES_INITIALES)
        self.Bind(wx.EVT_TOOL, self.Mode_places_prises, id=ID_MODE_PLACES_PRISES)
        self.Bind(wx.EVT_TOOL, self.Mode_places_restantes, id=ID_MODE_PLACES_RESTANTES)
        self.Bind(wx.EVT_TOOL, self.Mode_places_attente, id=ID_MODE_PLACES_ATTENTE)
        self.Bind(wx.EVT_TOOL, self.Liste_attente, id=ID_LISTE_ATTENTE)
        self.Bind(wx.EVT_TOOL, self.Parametres, id=ID_PARAMETRES)
        self.Bind(wx.EVT_TOOL, self.MenuOutils, id=ID_OUTILS)

        UTILS_Aui.ConfigurerToolBar(self, taille_base=24, fond_uni=True)

    def Mode_places_initiales(self, event):
        self.GetParent().dictDonnees["modeAffichage"] = "nbrePlacesInitial"
        self.GetParent().SetDictDonnees(self.GetParent().dictDonnees)
        self.GetParent().MAJ()

    def Mode_places_prises(self, event):
        self.GetParent().dictDonnees["modeAffichage"] = "nbrePlacesPrises"
        self.GetParent().SetDictDonnees(self.GetParent().dictDonnees)
        self.GetParent().MAJ()

    def Mode_places_restantes(self, event):
        self.GetParent().dictDonnees["modeAffichage"] = "nbrePlacesRestantes"
        self.GetParent().SetDictDonnees(self.GetParent().dictDonnees)
        self.GetParent().MAJ()

    def Mode_places_attente(self, event):
        self.GetParent().dictDonnees["modeAffichage"] = "nbreAttente"
        self.GetParent().SetDictDonnees(self.GetParent().dictDonnees)
        self.GetParent().MAJ()

    def Liste_attente(self, event):
        self.GetParent().OuvrirListeAttente()

    def Parametres(self, event):
        global AFFICHE_PRESENTS, MAJ_AUTO_REMPLISSAGE
        from Dlg import DLG_Parametres_remplissage
        dictDonnees = self.GetParent().dictDonnees
        if "modeAffichage" in dictDonnees:
            modeAffichage = dictDonnees["modeAffichage"]
        else:
            modeAffichage = "nbrePlacesPrises"
        abregeGroupes = self.GetParent().ctrl_remplissage.GetAbregeGroupes()
        totaux = self.GetParent().ctrl_remplissage.GetAfficheTotaux()
        affichePresents = AFFICHE_PRESENTS
        maj_auto_remplissage = MAJ_AUTO_REMPLISSAGE
        dlg = DLG_Parametres_remplissage.Dialog(
            None,
            dictDonnees,
            abregeGroupes=abregeGroupes,
            affichePresents=affichePresents,
            totaux=totaux,
            maj_auto_remplissage=maj_auto_remplissage,
        )
        if dlg.ShowModal() == wx.ID_OK:
            listeActivites = dlg.GetListeActivites()
            listePeriodes = dlg.GetListePeriodes()
            dictDonnees = dlg.GetDictDonnees()
            abregeGroupes = dlg.GetAbregeGroupes()
            afficheTotaux = dlg.GetAfficheTotaux()
            self.GetParent().ctrl_remplissage.SetListeActivites(listeActivites)
            self.GetParent().ctrl_remplissage.SetListePeriodes(listePeriodes)
            self.GetParent().ctrl_remplissage.SetAbregeGroupes(abregeGroupes)
            self.GetParent().ctrl_remplissage.SetAfficheTotaux(afficheTotaux)
            self.GetParent().ctrl_remplissage.MAJ()
            dictDonnees["modeAffichage"] = modeAffichage
            self.GetParent().SetDictDonnees(dictDonnees)
            AFFICHE_PRESENTS = dlg.GetAffichePresents()
            UTILS_Config.SetParametre("remplissage_affiche_presents", int(AFFICHE_PRESENTS))
            MAJ_AUTO_REMPLISSAGE = dlg.GetMAJautoRemplissage()
            UTILS_Config.SetParametre("remplissage_maj_auto", int(MAJ_AUTO_REMPLISSAGE))
            self.GetParent().MAJ()
        dlg.Destroy()

    def _BitmapMenu(self, image):
        return UTILS_Aui.ChargerBitmapToolBar(image, taille_base=16)

    def MenuOutils(self, event):
        menuPop = UTILS_Adaptations.Menu()

        ID_APERCU = wx.Window.NewControlId()
        item = wx.MenuItem(menuPop, ID_APERCU, _(u"Aperçu avant impression"), _(u"Imprimer la liste des effectifs affichée"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Apercu.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Apercu, id=ID_APERCU)

        ID_IMPRIMER = wx.Window.NewControlId()
        item = wx.MenuItem(menuPop, ID_IMPRIMER, _(u"Imprimer"), _(u"Imprimer la liste des effectifs affichée"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Imprimante.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Imprimer, id=ID_IMPRIMER)

        menuPop.AppendSeparator()

        ID_EXPORT_TEXTE = wx.Window.NewControlId()
        item = wx.MenuItem(menuPop, ID_EXPORT_TEXTE, _(u"Exporter au format Texte"), _(u"Exporter au format Texte"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Texte2.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.GetParent().ctrl_remplissage.ExportTexte, id=ID_EXPORT_TEXTE)

        ID_EXPORT_EXCEL = wx.Window.NewControlId()
        item = wx.MenuItem(menuPop, ID_EXPORT_EXCEL, _(u"Exporter au format Excel"), _(u"Exporter au format Excel"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Excel.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.GetParent().ctrl_remplissage.ExportExcel, id=ID_EXPORT_EXCEL)

        menuPop.AppendSeparator()

        ID_ACTUALISER = wx.Window.NewControlId()
        item = wx.MenuItem(menuPop, ID_ACTUALISER, _(u"Actualiser"), _(u"Actualiser l'affichage"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Actualiser2.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Actualiser, id=ID_ACTUALISER)

        menuPop.AppendSeparator()

        ID_AIDE = wx.Window.NewControlId()
        item = wx.MenuItem(menuPop, ID_AIDE, _(u"Aide"), _(u"Aide"))
        item.SetBitmap(self._BitmapMenu("Images/16x16/Aide.png"))
        menuPop.AppendItem(item)
        self.Bind(wx.EVT_MENU, self.Aide, id=ID_AIDE)

        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def Actualiser(self, event):
        self.GetParent().ctrl_remplissage.MAJ()

    def Imprimer(self, event):
        self.GetParent().Imprimer()

    def Apercu(self, event):
        self.GetParent().Apercu()

    def Aide(self, event):
        self.GetParent().Aide()


class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, name="panel_remplissage", id=-1, style=wx.TAB_TRAVERSAL)

        self.dictDonnees = self.GetParametres()
        self.toolBar = ToolBar(self)
        self.ctrl_remplissage = CTRL_Remplissage.CTRL(self, self.dictDonnees)
        self.ctrl_presents = CTRL_Ticker_presents.CTRL(self, delai=60, listeActivites=[15,])
        self.ctrl_presents.Show(False)

        global AFFICHE_PRESENTS, MAJ_AUTO_REMPLISSAGE
        AFFICHE_PRESENTS = UTILS_Config.GetParametre("remplissage_affiche_presents", 1)
        MAJ_AUTO_REMPLISSAGE = UTILS_Config.GetParametre("remplissage_maj_auto", 0)

        if "modeAffichage" in self.dictDonnees:
            if self.dictDonnees["modeAffichage"] == "nbrePlacesInitial":
                self.toolBar.ToggleTool(ID_MODE_PLACES_INITIALES, True)
            if self.dictDonnees["modeAffichage"] == "nbrePlacesPrises":
                self.toolBar.ToggleTool(ID_MODE_PLACES_PRISES, True)
            if self.dictDonnees["modeAffichage"] == "nbrePlacesRestantes":
                self.toolBar.ToggleTool(ID_MODE_PLACES_RESTANTES, True)
            if self.dictDonnees["modeAffichage"] == "nbreAttente":
                self.toolBar.ToggleTool(ID_MODE_PLACES_ATTENTE, True)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

    def __do_layout(self):
        # Un simple flux vertical remplace le FlexGridSizer historique : la
        # toolbar et le ticker gardent leur BestSize, la grille absorbe tout le
        # reste. Aucune ligne artificielle ne peut donc bloquer le redimensionnement.
        self.sizer_base = wx.BoxSizer(wx.VERTICAL)
        self.sizer_base.Add(self.toolBar, 0, wx.EXPAND)
        self.sizer_base.Add(self.ctrl_presents, 0, wx.EXPAND)
        self.sizer_base.Add(self.ctrl_remplissage, 1, wx.EXPAND)
        self.SetSizer(self.sizer_base)
        self.Layout()

    def GetParametres(self):
        defaut = {
            'listeActivites': [],
            'listeSelections': (),
            'listePeriodes': [],
            'modeAffichage': 'nbrePlacesPrises',
            'dateDebut': None,
            'dateFin': None,
            'annee': datetime.date.today().year,
            'page': 0,
        }
        return UTILS_Config.GetParametre("dict_selection_periodes_activites", defaut)

    def SetDictDonnees(self, dictDonnees={}):
        if len(dictDonnees) != 0:
            self.dictDonnees = dictDonnees
        self.ctrl_remplissage.SetDictDonnees(self.dictDonnees)
        UTILS_Config.SetParametre("dict_selection_periodes_activites", self.dictDonnees)

    def MAJ(self):
        global MAJ_AUTO_EN_ATTENTE
        self.ctrl_remplissage.MAJ()
        self.MAJpresents()
        if MAJ_AUTO_REMPLISSAGE:
            if MAJ_AUTO_EN_ATTENTE:
                MAJ_AUTO_EN_ATTENTE.Stop()
            MAJ_AUTO_EN_ATTENTE = wx.CallLater(MAJ_AUTO_REMPLISSAGE, self.MAJ)

    def MAJpresents(self):
        listeActivites = self.dictDonnees["listeActivites"]
        self.ctrl_presents.SetActivites(listeActivites)
        self.ctrl_presents.MAJ()

    def AffichePresents(self, etat=True):
        if AFFICHE_PRESENTS == 0:
            etat = 0
        self.ctrl_presents.Show(etat)
        self.Layout()

    def Imprimer(self):
        self.ctrl_remplissage.Imprimer()

    def Apercu(self):
        self.ctrl_remplissage.Apercu()

    def Aide(self):
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("Leseffectifs")

    def OuvrirListeAttente(self):
        self.ctrl_remplissage.MAJ()
        dictEtatPlaces = self.ctrl_remplissage.GetEtatPlaces()
        dictUnitesRemplissage = self.ctrl_remplissage.dictUnitesRemplissage
        from Dlg import DLG_Attente
        dlg = DLG_Attente.Dialog(
            self,
            dictDonnees=self.dictDonnees,
            dictEtatPlaces=dictEtatPlaces,
            dictUnitesRemplissage=dictUnitesRemplissage,
        )
        dlg.ShowModal()
        dlg.Destroy()

    def OuvrirListeRefus(self):
        self.ctrl_remplissage.MAJ()
        dictEtatPlaces = self.ctrl_remplissage.GetEtatPlaces()
        dictUnitesRemplissage = self.ctrl_remplissage.dictUnitesRemplissage
        from Dlg import DLG_Refus
        dlg = DLG_Refus.Dialog(
            self,
            dictDonnees=self.dictDonnees,
            dictEtatPlaces=dictEtatPlaces,
            dictUnitesRemplissage=dictUnitesRemplissage,
        )
        dlg.ShowModal()
        dlg.Destroy()


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
        sizer_2.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(1))
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
