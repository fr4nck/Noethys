#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Barre d'outils Repens pour les ObjectListView Noethys.

Cette implémentation reprend volontairement le contrat public de
``CTRL_ObjectListView.CTRL_Outils`` afin de pouvoir migrer les écrans un par un
sans modifier leur logique métier : recherche, filtres avancés, cochage rapide
et regroupement restent disponibles, mais sans ``PlateButton`` ni images 16 px.
"""

import wx

from Ctrl import CTRL_ActionRepens
from Utils import UTILS_Adaptations
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


ID_FILTRES_GERER = 10
ID_FILTRES_EFFACER = 11
ID_COCHER_TOUT = 20
ID_DECOCHER_TOUT = 21


def _AppelerPremiere(objet, noms):
    """Appelle la première variante historique disponible."""
    if objet is None:
        return False
    for nom in noms:
        methode = getattr(objet, nom, None)
        if callable(methode):
            methode()
            return True
    return False


class BarreRecherche(wx.SearchCtrl):
    """Recherche différée, compatible avec le contrat historique."""

    def __init__(self, parent, listview, texteDefaut=u"Rechercher…"):
        wx.SearchCtrl.__init__(self, parent, style=wx.TE_PROCESS_ENTER)
        self.parent = parent
        self.listview = listview
        self.SetDescriptiveText(texteDefaut)
        self.ShowSearchButton(True)
        self.ShowCancelButton(False)
        Style.appliquer_saisie(self)

        try:
            self.listview.SetBarreRecherche(self)
        except Exception:
            pass

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.Recherche, self.timer)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnSearch)
        self.Bind(wx.EVT_TEXT, self.OnDoSearch)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def OnSearch(self, event=None):
        self.Recherche()

    def OnCancel(self, event=None):
        self.SetValue("")
        self.Recherche()

    def Cancel(self):
        self.OnCancel()

    def OnKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.OnCancel()
            return
        event.Skip()

    def OnDoSearch(self, event):
        if self.timer.IsRunning():
            self.timer.Stop()
        try:
            nbre = len(self.listview.GetObjects())
        except Exception:
            nbre = 0
        if nbre < 500:
            duree = 30
        elif nbre < 1000:
            duree = 180
        elif nbre < 5000:
            duree = 400
        else:
            duree = 800
        self.timer.Start(duree, oneShot=True)
        event.Skip()

    # Alias conservé pour les quelques appels introduits pendant la migration.
    OnTexte = OnDoSearch

    def Recherche(self, event=None):
        if self.timer.IsRunning():
            self.timer.Stop()
        texte = self.GetValue()
        self.ShowCancelButton(bool(texte))
        if self.listview is None:
            return
        try:
            self.listview.Filtrer(texte)
        except TypeError:
            self.listview.Filtrer()


class CTRL_Regroupement(wx.Choice):
    """Choix de regroupement compatible avec celui de CTRL_ObjectListView."""

    def __init__(self, parent):
        wx.Choice.__init__(self, parent, -1)
        self.parent = parent
        self.listview = None
        self.listeLabels = []
        self.dictDonnees = {}
        Style.appliquer_saisie(self)
        self.SetMinSize((Style.px(130), Style.cible_action("compact")))

    def MAJ(self, listview=None):
        if listview is not None:
            self.listview = listview
        if self.listview is None:
            return
        if not getattr(self, "_repens_bind_regroupement", False):
            self._repens_bind_regroupement = True
            self.Bind(wx.EVT_CHOICE, self.OnChoix)

        self.dictDonnees = {0: None}
        self.listeLabels = [_(u"Aucun")]
        for index_colonne, titre in enumerate(self.GetTitresColonnes(self.listview)):
            if titre not in ("ID", ""):
                self.dictDonnees[len(self.listeLabels)] = index_colonne
                self.listeLabels.append(titre)
        self.SetItems(self.listeLabels)

        selection = 0
        regroupement = getattr(self.listview, "regroupement", None)
        if regroupement is not None:
            for index, index_colonne in self.dictDonnees.items():
                if index_colonne == regroupement:
                    selection = index
                    break
        self.SetSelection(selection)

    def GetTitresColonnes(self, listview=None):
        listview = listview or self.listview
        if listview is None:
            return []
        titres = []
        try:
            colonnes = listview.columns
        except Exception:
            colonnes = []
        for colonne in colonnes:
            titres.append(getattr(colonne, "title", ""))
        if titres:
            return titres
        try:
            for index in range(listview.GetColumnCount()):
                titres.append(listview.GetColumn(index).GetText())
        except Exception:
            pass
        return titres

    def GetRegroupement(self):
        index = self.GetSelection()
        if index in (-1, 0):
            return None
        return self.dictDonnees.get(index)

    def OnChoix(self, event=None):
        if self.listview is None:
            return
        self.listview.regroupement = self.GetRegroupement()
        try:
            self.listview.MAJ()
        except Exception:
            try:
                self.listview.RepopulateList()
            except Exception:
                pass


class CTRL(wx.Panel):
    """Recherche, filtrage, cochage et regroupement dans une barre desktop."""

    def __init__(
        self,
        parent,
        listview=None,
        texteDefaut=u"Rechercher…",
        afficherCocher=False,
        afficherRegroupement=False,
        style=wx.NO_BORDER | wx.TAB_TRAVERSAL,
    ):
        wx.Panel.__init__(self, parent, id=-1, style=style)
        self.listview = listview
        self.afficherRegroupement = bool(afficherRegroupement)
        self.afficherCocher = bool(afficherCocher)
        Style.appliquer_fenetre(self, "surface")

        self.barreRecherche = BarreRecherche(self, listview=listview, texteDefaut=texteDefaut)
        self.bouton_filtrer = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Filtrer"),
            icone="filter",
            variante="ghost",
            tooltip=_(u"Gérer les filtres avancés de cette liste"),
        )
        self.Bind(wx.EVT_BUTTON, self.OnBoutonFiltrer, self.bouton_filtrer)

        self.bouton_cocher = None
        if self.afficherCocher:
            self.bouton_cocher = CTRL_ActionRepens.CTRL(
                self,
                label=_(u"Cocher"),
                variante="ghost",
                tooltip=_(u"Cocher ou décocher rapidement les éléments de la liste"),
            )
            self.Bind(wx.EVT_BUTTON, self.OnBoutonCocher, self.bouton_cocher)

        self.label_regroupement = None
        self.ctrl_regroupement = None
        if self.afficherRegroupement:
            self.label_regroupement = wx.StaticText(self, -1, _(u"Regrouper :"))
            Style.appliquer_texte(
                self.label_regroupement,
                role="label",
                role_texte="on_surface_variant",
                role_fond="surface",
            )
            self.ctrl_regroupement = CTRL_Regroupement(self)
            self.ctrl_regroupement.MAJ(listview=listview)
            try:
                listview.ctrl_regroupement = self.ctrl_regroupement
            except Exception:
                pass

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.barreRecherche, 1, wx.EXPAND | wx.RIGHT, Style.espace(1))
        sizer.Add(self.bouton_filtrer, 0, wx.ALIGN_CENTER_VERTICAL)
        if self.bouton_cocher is not None:
            sizer.Add(self.bouton_cocher, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, Style.espace(1))
        if self.ctrl_regroupement is not None:
            sizer.AddSpacer(Style.espace(2))
            sizer.Add(self.label_regroupement, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, Style.espace(1))
            sizer.Add(self.ctrl_regroupement, 0, wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(sizer)
        self.Layout()

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_MENU, self.OnMenu, id=ID_FILTRES_GERER)
        self.Bind(wx.EVT_MENU, self.OnMenu, id=ID_FILTRES_EFFACER)
        self.Bind(wx.EVT_MENU, self.OnMenu, id=ID_COCHER_TOUT)
        self.Bind(wx.EVT_MENU, self.OnMenu, id=ID_DECOCHER_TOUT)
        self.MAJ_ctrl_filtrer()

    def OnSize(self, event):
        event.Skip()

    def _MenuFiltres(self):
        menu = UTILS_Adaptations.Menu()
        menu.Append(ID_FILTRES_GERER, _(u"Gérer les filtres…"))
        menu.Append(ID_FILTRES_EFFACER, _(u"Supprimer tous les filtres"))
        return menu

    def _MenuCocher(self):
        menu = UTILS_Adaptations.Menu()
        menu.Append(ID_COCHER_TOUT, _(u"Tout cocher"))
        menu.Append(ID_DECOCHER_TOUT, _(u"Tout décocher"))
        return menu

    def MAJFiltre(self):
        self.MAJ_ctrl_filtrer()

    def MAJ_ctrl_filtrer(self):
        try:
            nbre = len(self.listview.listeFiltresColonnes)
        except Exception:
            nbre = 0
        label = _(u"Filtrer") if nbre == 0 else _(u"Filtrer (%d)") % nbre
        self.bouton_filtrer.SetLabel(label)
        if nbre:
            texte = _(u"%d filtre(s) avancé(s) actif(s)") % nbre
        else:
            texte = _(u"Gérer les filtres avancés de cette liste")
        self.bouton_filtrer.SetToolTip(wx.ToolTip(texte))
        self.Layout()

    def OnBoutonFiltrer(self, event=None):
        menu = self._MenuFiltres()
        try:
            position = self.bouton_filtrer.GetPosition() + wx.Point(0, self.bouton_filtrer.GetSize().GetHeight())
            self.PopupMenu(menu, position)
        except Exception:
            self.PopupMenu(menu)
        menu.Destroy()

    def OnBoutonCocher(self, event=None):
        if self.bouton_cocher is None:
            return
        menu = self._MenuCocher()
        try:
            position = self.bouton_cocher.GetPosition() + wx.Point(0, self.bouton_cocher.GetSize().GetHeight())
            self.PopupMenu(menu, position)
        except Exception:
            self.PopupMenu(menu)
        menu.Destroy()

    def _GererFiltres(self):
        from Dlg import DLG_Filtres_listes
        dlg = DLG_Filtres_listes.Dialog(self, ctrl_listview=self.listview)
        if dlg.ShowModal() == wx.ID_OK:
            listeFiltres = dlg.GetDonnees()
            self.listview.SetFiltresColonnes(listeFiltres)
            self.listview.Filtrer()
            self.MAJ_ctrl_filtrer()
        dlg.Destroy()

    def OnMenu(self, event):
        identifiant = event.GetId()
        if identifiant == ID_FILTRES_GERER:
            self._GererFiltres()
        elif identifiant == ID_FILTRES_EFFACER:
            self.SetFiltres([])
        elif identifiant == ID_COCHER_TOUT:
            _AppelerPremiere(self.listview, ("CocheListeTout", "CocheTout"))
        elif identifiant == ID_DECOCHER_TOUT:
            _AppelerPremiere(self.listview, ("CocheListeRien", "CocheRien"))

    def SetFiltres(self, listeFiltres=None):
        if self.listview is None:
            return
        self.listview.SetFiltresColonnes(listeFiltres or [])
        self.listview.Filtrer()
        self.MAJ_ctrl_filtrer()
