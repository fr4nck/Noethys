#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Panneau de fréquentation Repens Design.

Le moteur métier reste dans ``CTRL_Remplissage`` via la sous-classe Repens,
mais aucun widget historique n'est instancié puis remplacé. Toolbar, ticker et
grille sont construits directement dans la structure responsive moderne.
"""

import datetime
import wx

from Dlg import DLG_Remplissage as Legacy
from Ctrl import CTRL_Remplissage_Repens
from Ctrl import CTRL_Ticker_presents
from Utils import UTILS_Adaptations
from Utils import UTILS_Aui
from Utils import UTILS_FluentIcons
from Utils import UTILS_Interface
from Utils import UTILS_Responsive
from Utils import UTILS_UIMetrics
from Utils import UTILS_Config
from Utils.UTILS_Traduction import _


class ToolBar(wx.ToolBar):
    MODES = (
        (Legacy.ID_MODE_PLACES_INITIALES, u"Capacité", "people", "nbrePlacesInitial", _(u"Afficher la capacité maximale")),
        (Legacy.ID_MODE_PLACES_PRISES, u"Occupé", "calendar_day", "nbrePlacesPrises", _(u"Afficher le nombre de places prises")),
        (Legacy.ID_MODE_PLACES_RESTANTES, u"Disponible", "add", "nbrePlacesRestantes", _(u"Afficher le nombre de places disponibles")),
        (Legacy.ID_MODE_PLACES_ATTENTE, u"Attente", "calendar", "nbreAttente", _(u"Afficher le nombre de places en attente")),
    )

    def __init__(self, parent):
        wx.ToolBar.__init__(self, parent, style=wx.TB_FLAT | wx.TB_TEXT | wx.TB_NODIVIDER)
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_low"))
        taille = UTILS_Responsive.GetTailleIcone(20)

        for identifiant, label, icone, mode, tooltip in self.MODES:
            self._AjouterOutil(identifiant, label, icone, taille, wx.ITEM_RADIO, tooltip)
            self.Bind(wx.EVT_TOOL, lambda evt, valeur=mode: self._ChangerMode(valeur), id=identifiant)

        self.AddSeparator()
        self._AjouterOutil(Legacy.ID_LISTE_ATTENTE, _(u"Liste d'attente"), "people", taille, wx.ITEM_NORMAL, _(u"Afficher la liste d'attente"))
        self.Bind(wx.EVT_TOOL, self.OnListeAttente, id=Legacy.ID_LISTE_ATTENTE)

        try:
            self.AddStretchableSpace()
        except Exception:
            self.AddSeparator()
        self._AjouterOutil(Legacy.ID_PARAMETRES, _(u"Affichage"), "settings", taille, wx.ITEM_NORMAL, _(u"Paramètres d'affichage"))
        self._AjouterOutil(Legacy.ID_OUTILS, _(u"Plus"), "print", taille, wx.ITEM_NORMAL, _(u"Imprimer, exporter, actualiser ou obtenir de l'aide"))
        self.Bind(wx.EVT_TOOL, self.OnParametres, id=Legacy.ID_PARAMETRES)
        self.Bind(wx.EVT_TOOL, self.OnPlus, id=Legacy.ID_OUTILS)

        UTILS_Aui.ConfigurerToolBar(self, taille_base=20, fond_uni=True)
        self._SynchroniserMode()

    def _Bitmap(self, icone, taille):
        try:
            bitmap = UTILS_FluentIcons.GetBitmap(icone, taille=taille)
            if bitmap is not None and bitmap.IsOk():
                return bitmap
        except Exception:
            pass
        return wx.NullBitmap

    def _AjouterOutil(self, identifiant, label, icone, taille, kind, tooltip):
        bitmap = self._Bitmap(icone, taille)
        try:
            self.AddTool(identifiant, label, bitmap, wx.NullBitmap, kind, tooltip, "")
        except Exception:
            self.AddLabelTool(identifiant, label, bitmap, wx.NullBitmap, kind, tooltip, "")

    def _ChangerMode(self, mode):
        parent = self.GetParent()
        parent.dictDonnees["modeAffichage"] = mode
        parent.SetDictDonnees(parent.dictDonnees)
        parent.MAJ()
        self._SynchroniserMode()

    def _SynchroniserMode(self):
        mode = self.GetParent().dictDonnees.get("modeAffichage", "nbrePlacesPrises")
        for identifiant, label, icone, valeur, tooltip in self.MODES:
            try:
                self.ToggleTool(identifiant, valeur == mode)
            except Exception:
                pass

    def OnListeAttente(self, event=None):
        self.GetParent().OuvrirListeAttente()

    def OnParametres(self, event=None):
        from Dlg import DLG_Parametres_remplissage

        parent = self.GetParent()
        dict_donnees = parent.dictDonnees
        mode = dict_donnees.get("modeAffichage", "nbrePlacesPrises")
        dlg = DLG_Parametres_remplissage.Dialog(
            None,
            dict_donnees,
            abregeGroupes=parent.ctrl_remplissage.GetAbregeGroupes(),
            affichePresents=Legacy.AFFICHE_PRESENTS,
            totaux=parent.ctrl_remplissage.GetAfficheTotaux(),
            maj_auto_remplissage=Legacy.MAJ_AUTO_REMPLISSAGE,
        )
        if dlg.ShowModal() == wx.ID_OK:
            parent.ctrl_remplissage.SetListeActivites(dlg.GetListeActivites())
            parent.ctrl_remplissage.SetListePeriodes(dlg.GetListePeriodes())
            parent.ctrl_remplissage.SetAbregeGroupes(dlg.GetAbregeGroupes())
            parent.ctrl_remplissage.SetAfficheTotaux(dlg.GetAfficheTotaux())
            parent.ctrl_remplissage.MAJ()
            dict_donnees = dlg.GetDictDonnees()
            dict_donnees["modeAffichage"] = mode
            parent.SetDictDonnees(dict_donnees)
            Legacy.AFFICHE_PRESENTS = dlg.GetAffichePresents()
            UTILS_Config.SetParametre("remplissage_affiche_presents", int(Legacy.AFFICHE_PRESENTS))
            Legacy.MAJ_AUTO_REMPLISSAGE = dlg.GetMAJautoRemplissage()
            UTILS_Config.SetParametre("remplissage_maj_auto", int(Legacy.MAJ_AUTO_REMPLISSAGE))
            parent.MAJ()
        dlg.Destroy()
        self._SynchroniserMode()

    def OnPlus(self, event=None):
        menu = UTILS_Adaptations.Menu()
        actions = (
            (_(u"Aperçu avant impression"), lambda evt=None: self.GetParent().Apercu()),
            (_(u"Imprimer"), lambda evt=None: self.GetParent().Imprimer()),
            None,
            (_(u"Exporter au format Texte"), lambda evt=None: self.GetParent().ctrl_remplissage.ExportTexte(None)),
            (_(u"Exporter au format Excel"), lambda evt=None: self.GetParent().ctrl_remplissage.ExportExcel(None)),
            None,
            (_(u"Actualiser"), lambda evt=None: self.GetParent().MAJ()),
            (_(u"Aide"), lambda evt=None: self.GetParent().Aide()),
        )
        for action in actions:
            if action is None:
                menu.AppendSeparator()
                continue
            label, callback = action
            identifiant = wx.Window.NewControlId()
            menu.Append(identifiant, label)
            self.Bind(wx.EVT_MENU, callback, id=identifiant)
        self.PopupMenu(menu)
        menu.Destroy()


class Panel(wx.Panel):
    """Conteneur Repens construit directement, sans sizer ou widget historique."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, name="panel_remplissage", id=-1, style=wx.TAB_TRAVERSAL)
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        self.dictDonnees = self.GetParametres()
        Legacy.AFFICHE_PRESENTS = UTILS_Config.GetParametre("remplissage_affiche_presents", 1)
        Legacy.MAJ_AUTO_REMPLISSAGE = UTILS_Config.GetParametre("remplissage_maj_auto", 0)

        self.toolBar = ToolBar(self)
        self.ctrl_presents = CTRL_Ticker_presents.CTRL(self, delai=60, listeActivites=[15,])
        self.ctrl_presents.Show(False)
        self.ctrl_remplissage = CTRL_Remplissage_Repens.CTRL(self, self.dictDonnees)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.toolBar, 0, wx.EXPAND)
        sizer.Add(self.ctrl_presents, 0, wx.EXPAND)
        sizer.Add(self.ctrl_remplissage, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.sizer_base = sizer
        self.Layout()
        self.toolBar._SynchroniserMode()

    def GetParametres(self):
        defaut = {
            "listeActivites": [],
            "listeSelections": (),
            "listePeriodes": [],
            "modeAffichage": "nbrePlacesPrises",
            "dateDebut": None,
            "dateFin": None,
            "annee": datetime.date.today().year,
            "page": 0,
        }
        return UTILS_Config.GetParametre("dict_selection_periodes_activites", defaut)

    def SetDictDonnees(self, dictDonnees=None):
        if dictDonnees:
            self.dictDonnees = dictDonnees
        self.ctrl_remplissage.SetDictDonnees(self.dictDonnees)
        UTILS_Config.SetParametre("dict_selection_periodes_activites", self.dictDonnees)

    def MAJ(self):
        self.ctrl_remplissage.MAJ()
        self.MAJpresents()
        if Legacy.MAJ_AUTO_REMPLISSAGE:
            if Legacy.MAJ_AUTO_EN_ATTENTE:
                Legacy.MAJ_AUTO_EN_ATTENTE.Stop()
            Legacy.MAJ_AUTO_EN_ATTENTE = wx.CallLater(Legacy.MAJ_AUTO_REMPLISSAGE, self.MAJ)

    def MAJpresents(self):
        listeActivites = self.dictDonnees.get("listeActivites", [])
        self.ctrl_presents.SetActivites(listeActivites)
        self.ctrl_presents.MAJ()

    def AffichePresents(self, etat=True):
        if Legacy.AFFICHE_PRESENTS == 0:
            etat = False
        self.ctrl_presents.Show(bool(etat))
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
        dict_etat_places = self.ctrl_remplissage.GetEtatPlaces()
        dict_unites = self.ctrl_remplissage.dictUnitesRemplissage
        from Dlg import DLG_Attente
        dlg = DLG_Attente.Dialog(
            self,
            dictDonnees=self.dictDonnees,
            dictEtatPlaces=dict_etat_places,
            dictUnitesRemplissage=dict_unites,
        )
        dlg.ShowModal()
        dlg.Destroy()

    def OuvrirListeRefus(self):
        self.ctrl_remplissage.MAJ()
        dict_etat_places = self.ctrl_remplissage.GetEtatPlaces()
        dict_unites = self.ctrl_remplissage.dictUnitesRemplissage
        from Dlg import DLG_Refus
        dlg = DLG_Refus.Dialog(
            self,
            dictDonnees=self.dictDonnees,
            dictEtatPlaces=dict_etat_places,
            dictUnitesRemplissage=dict_unites,
        )
        dlg.ShowModal()
        dlg.Destroy()
