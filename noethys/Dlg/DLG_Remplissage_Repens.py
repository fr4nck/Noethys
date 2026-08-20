#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Panneau de fréquentation Repens Design.

Le métier et les boîtes de dialogue existantes restent inchangés. Le panneau
remplace explicitement la toolbar et la grille historiques par leurs variantes
Repens afin que toute la vue visible soit cohérente.
"""

import wx

from Dlg import DLG_Remplissage as Legacy
from Ctrl import CTRL_Remplissage_Repens
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

        self.AddStretchableSpace()
        self._AjouterOutil(Legacy.ID_PARAMETRES, _(u"Affichage"), "settings", taille, wx.ITEM_NORMAL, _(u"Paramètres d'affichage"))
        self._AjouterOutil(Legacy.ID_OUTILS, _(u"Plus"), "print", taille, wx.ITEM_NORMAL, _(u"Imprimer, exporter, actualiser ou obtenir de l'aide"))
        self.Bind(wx.EVT_TOOL, self.OnParametres, id=Legacy.ID_PARAMETRES)
        self.Bind(wx.EVT_TOOL, self.OnPlus, id=Legacy.ID_OUTILS)

        UTILS_Aui.ConfigurerToolBar(self, taille_base=20, fond_uni=True)
        self._SynchroniserMode()

    def _Bitmap(self, icone, taille):
        bitmap = None
        try:
            bitmap = UTILS_FluentIcons.GetBitmap(icone, taille=taille)
        except Exception:
            bitmap = None
        if bitmap is None or not bitmap.IsOk():
            bitmap = wx.NullBitmap
        return bitmap

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


class Panel(Legacy.Panel):
    """Conteneur compatible avec l'ancien panneau, sans ses contrôles visuels."""

    def __init__(self, parent):
        Legacy.Panel.__init__(self, parent)

        ancienne_toolbar = self.toolBar
        ancienne_grille = self.ctrl_remplissage
        try:
            self.sizer_base.Detach(ancienne_toolbar)
            self.sizer_base.Detach(ancienne_grille)
        except Exception:
            pass
        ancienne_toolbar.Destroy()
        ancienne_grille.Destroy()

        self.toolBar = ToolBar(self)
        self.ctrl_remplissage = CTRL_Remplissage_Repens.CTRL(self, self.dictDonnees)
        self.sizer_base.Insert(0, self.toolBar, 0, wx.EXPAND)
        self.sizer_base.Insert(2, self.ctrl_remplissage, 1, wx.EXPAND)
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))
        self.Layout()
