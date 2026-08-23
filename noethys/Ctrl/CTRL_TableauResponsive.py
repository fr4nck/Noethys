# -*- coding: utf-8 -*-
"""Brique de tableau moderne et responsive pour les nouveaux écrans Noethys.

Objectif : fournir une base desktop dense, native et cohérente pour les futurs
rapports/tableaux sans recréer des largeurs fixes, des mini-boutons ou des
panneaux décoratifs à chaque écran.

Ce contrôle n'impose aucune logique métier. Les données sont des dictionnaires,
les actions sont des callbacks et chaque colonne déclare un minimum + un poids.
"""

import wx

from Ctrl import CTRL_ActionRepens
from Utils import UTILS_ColonnesResponsive
from Utils import UTILS_StyleRepens as Style


class Colonne(object):
    def __init__(self, cle, label, minimum=100, poids=0, align="left", formatter=None):
        self.cle = cle
        self.label = label
        self.minimum = max(0, int(minimum))
        self.poids = max(0.0, float(poids))
        self.align = align
        self.formatter = formatter


class Action(object):
    def __init__(self, label, callback, icone=None, tooltip="", principal=False):
        self.label = label
        self.callback = callback
        self.icone = icone
        self.tooltip = tooltip
        self.principal = bool(principal)


class EnteteSection(wx.Panel):
    """Titre + sous-titre compact ; pas une carte mobile."""

    def __init__(self, parent, titre="", sous_titre=""):
        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        Style.appliquer_fenetre(self, "surface_container")

        self.titre = wx.StaticText(self, label=titre)
        Style.appliquer_texte(
            self.titre,
            role="h3",
            role_texte="on_surface",
            role_fond="surface_container",
        )

        self.sous_titre = wx.StaticText(self, label=sous_titre)
        Style.appliquer_texte(
            self.sous_titre,
            role="body_small",
            role_texte="on_surface_variant",
            role_fond="surface_container",
        )
        self.sous_titre.Show(bool(sous_titre))

        texte = wx.BoxSizer(wx.VERTICAL)
        texte.Add(self.titre, 0)
        if sous_titre:
            texte.Add(self.sous_titre, 0, wx.TOP, Style.espace(1))
        else:
            texte.Add(self.sous_titre, 0)

        principal = wx.BoxSizer(wx.HORIZONTAL)
        principal.Add(texte, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, Style.espace(2))
        self.SetSizer(principal)

    def SetTitre(self, titre, sous_titre=None):
        self.titre.SetLabel(titre or "")
        if sous_titre is not None:
            self.sous_titre.SetLabel(sous_titre or "")
            self.sous_titre.Show(bool(sous_titre))
        self.Layout()
        try:
            self.GetParent().Layout()
        except Exception:
            pass


class BarreActions(wx.Panel):
    """Commandes Repens regroupées dans une barre desktop compacte."""

    def __init__(self, parent, actions=None):
        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        Style.appliquer_fenetre(self, "surface_container_low")
        self._boutons = []

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        marge = Style.espace(1)
        sizer.AddSpacer(marge)

        for action in actions or ():
            if action is None:
                sizer.AddSpacer(Style.espace(2))
                continue
            bouton = CTRL_ActionRepens.CTRL(
                self,
                label=action.label,
                icone=action.icone,
                variante="primaire" if action.principal else "secondaire",
                tooltip=action.tooltip or None,
                compact=True,
            )
            if action.callback:
                bouton.Bind(wx.EVT_BUTTON, action.callback)
            self._boutons.append(bouton)
            sizer.Add(bouton, 0, wx.RIGHT | wx.TOP | wx.BOTTOM, marge)

        sizer.AddStretchSpacer(1)
        self.SetSizer(sizer)


class ListeTableau(wx.ListCtrl):
    """Liste wx native à colonnes pondérées et métriques DPI-aware."""

    def __init__(self, parent, colonnes, style=0):
        style |= wx.LC_REPORT | wx.LC_HRULES | wx.BORDER_NONE
        wx.ListCtrl.__init__(self, parent, style=style)
        self.colonnes = tuple(colonnes or ())
        self._donnees = []
        Style.appliquer_liste(self)

        specs = []
        for index, colonne in enumerate(self.colonnes):
            format_colonne = wx.LIST_FORMAT_LEFT
            if colonne.align == "right":
                format_colonne = wx.LIST_FORMAT_RIGHT
            elif colonne.align == "center":
                format_colonne = wx.LIST_FORMAT_CENTRE
            minimum = Style.px(colonne.minimum, minimum=0)
            self.InsertColumn(index, colonne.label, format=format_colonne, width=minimum)
            specs.append((minimum, colonne.poids))

        UTILS_ColonnesResponsive.Installer(
            self,
            specs,
            marge=Style.espace(6),
        )

    def _texte(self, colonne, valeur, ligne):
        if colonne.formatter:
            try:
                return str(colonne.formatter(valeur, ligne))
            except TypeError:
                return str(colonne.formatter(valeur))
            except Exception:
                return ""
        if valeur is None:
            return ""
        return str(valeur)

    def _StyliserLigne(self, item, index):
        """Alterne deux surfaces discrètes sans ajouter de renderer maison."""
        role = "surface_container_lowest" if index % 2 == 0 else "surface_container_low"
        try:
            self.SetItemBackgroundColour(item, Style.couleur(role))
            self.SetItemTextColour(item, Style.couleur("on_surface"))
        except Exception:
            pass

    def SetDonnees(self, donnees):
        self.Freeze()
        try:
            self.DeleteAllItems()
            self._donnees = list(donnees or ())
            for index_ligne, ligne in enumerate(self._donnees):
                if not isinstance(ligne, dict):
                    try:
                        ligne = dict(ligne)
                    except Exception:
                        ligne = {}
                if not self.colonnes:
                    continue
                premiere = self._texte(self.colonnes[0], ligne.get(self.colonnes[0].cle), ligne)
                item = self.InsertItem(self.GetItemCount(), premiere)
                for index_colonne, colonne in enumerate(self.colonnes[1:], start=1):
                    texte = self._texte(colonne, ligne.get(colonne.cle), ligne)
                    self.SetItem(item, index_colonne, texte)
                self._StyliserLigne(item, index_ligne)
        finally:
            self.Thaw()
        UTILS_ColonnesResponsive.Ajuster(self)

    def GetDonneeSelectionnee(self):
        index = self.GetFirstSelected()
        if index == -1 or index >= len(self._donnees):
            return None
        return self._donnees[index]


class PanneauTableau(wx.Panel):
    """Conteneur prêt à l'emploi pour les futurs tableaux Noethys."""

    def __init__(self, parent, titre, colonnes, actions=None, sous_titre="", recherche=True):
        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        Style.appliquer_fenetre(self, "surface")

        self.entete = EnteteSection(self, titre=titre, sous_titre=sous_titre)
        self.actions = BarreActions(self, actions=actions) if actions else None
        self.tableau = ListeTableau(self, colonnes=colonnes)
        self.barre_donnees = wx.Panel(self, style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        Style.appliquer_fenetre(self.barre_donnees, "surface_container_low")

        self.recherche = wx.SearchCtrl(self.barre_donnees, style=wx.TE_PROCESS_ENTER) if recherche else None
        self.etat = wx.StaticText(self.barre_donnees, label="")
        Style.appliquer_texte(
            self.etat,
            role="body_small",
            role_texte="on_surface_variant",
            role_fond="surface_container_low",
        )

        if self.recherche is not None:
            Style.appliquer_saisie(self.recherche)
            self.recherche.SetMinSize((Style.px(180), Style.cible_action("compact")))
            self.recherche.SetMaxSize((Style.px(360), -1))
            self.recherche.ShowSearchButton(True)
            self.recherche.ShowCancelButton(True)
            self.recherche.SetDescriptiveText("Rechercher…")
            self.recherche.Bind(wx.EVT_TEXT, self._OnRecherche)
            self._donnees_source = []
        else:
            self._donnees_source = None

        outils = wx.BoxSizer(wx.HORIZONTAL)
        marge = Style.espace(2)
        if self.recherche is not None:
            outils.Add(self.recherche, 0, wx.ALIGN_CENTER_VERTICAL)
            outils.AddSpacer(marge)
        outils.AddStretchSpacer(1)
        outils.Add(self.etat, 0, wx.ALIGN_CENTER_VERTICAL)
        self.barre_donnees.SetSizer(outils)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.entete, 0, wx.EXPAND)
        if self.actions is not None:
            sizer.Add(self.actions, 0, wx.EXPAND)
        sizer.Add(self.barre_donnees, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, marge)
        sizer.Add(self.tableau, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def SetDonnees(self, donnees):
        donnees = list(donnees or ())
        if self._donnees_source is not None:
            self._donnees_source = donnees
        self.tableau.SetDonnees(donnees)
        self.etat.SetLabel("%d élément%s" % (len(donnees), "s" if len(donnees) != 1 else ""))

    def _OnRecherche(self, event):
        if self._donnees_source is None:
            event.Skip()
            return
        terme = self.recherche.GetValue().strip().lower()
        if not terme:
            filtrees = self._donnees_source
        else:
            filtrees = []
            for ligne in self._donnees_source:
                texte = " ".join(str(valeur) for valeur in ligne.values() if valeur is not None).lower()
                if terme in texte:
                    filtrees.append(ligne)
        self.tableau.SetDonnees(filtrees)
        self.etat.SetLabel("%d / %d" % (len(filtrees), len(self._donnees_source)))
        event.Skip()
