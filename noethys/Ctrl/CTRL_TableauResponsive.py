# -*- coding: utf-8 -*-
"""Brique de tableau moderne et responsive pour les nouveaux écrans Noethys.

Objectif : fournir une base desktop dense, native et cohérente pour les futurs
rapports/tableaux sans recréer des largeurs fixes, des mini-boutons ou des
panneaux décoratifs à chaque écran.

Ce contrôle n'impose aucune logique métier. Les données sont des dictionnaires,
les actions sont des callbacks et chaque colonne déclare un minimum + un poids.
"""

import wx

from Utils import UTILS_ColonnesResponsive
from Utils import UTILS_FluentIcons
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics


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


def _police(delta=0, bold=False):
    police = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
    try:
        base = police.GetPointSize()
        facteur = (UTILS_Interface.GetEchelle() / 100.0) * (UTILS_Interface.GetTailleTexte() / 100.0)
        police.SetPointSize(max(7, int(round((base + delta) * facteur))))
    except Exception:
        pass
    if bold:
        try:
            police.SetWeight(wx.FONTWEIGHT_SEMIBOLD)
        except Exception:
            police.SetWeight(wx.FONTWEIGHT_BOLD)
    return police


class EnteteSection(wx.Panel):
    """Titre + sous-titre compact ; pas une carte mobile."""
    def __init__(self, parent, titre="", sous_titre=""):
        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL)
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container"))

        self.titre = wx.StaticText(self, label=titre)
        self.titre.SetFont(_police(delta=1, bold=True))
        self.titre.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))

        self.sous_titre = wx.StaticText(self, label=sous_titre)
        self.sous_titre.SetFont(_police(delta=0, bold=False))
        self.sous_titre.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface_variant"))
        self.sous_titre.Show(bool(sous_titre))

        texte = wx.BoxSizer(wx.VERTICAL)
        texte.Add(self.titre, 0, wx.BOTTOM if sous_titre else 0, UTILS_UIMetrics.spacing(1))
        texte.Add(self.sous_titre, 0)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(texte, 1, wx.ALIGN_CENTER_VERTICAL)
        marge_x = UTILS_UIMetrics.spacing(3)
        marge_y = UTILS_UIMetrics.spacing(2)
        self.SetSizer(sizer)
        sizer.SetMinSize((-1, UTILS_UIMetrics.px(48)))
        self.SetMinSize((-1, UTILS_UIMetrics.px(48)))
        self.SetSizerAndFit(sizer)
        self.SetMinSize((-1, max(self.GetMinSize().GetHeight(), marge_y * 2 + self.titre.GetBestSize().GetHeight())))

        # La marge est portée par le parent via GetPadding() pour rester simple
        # avec wxPython classique ; le header lui-même ne dessine aucune bordure.
        self._marge_x = marge_x
        self._marge_y = marge_y

    def SetTitre(self, titre, sous_titre=None):
        self.titre.SetLabel(titre or "")
        if sous_titre is not None:
            self.sous_titre.SetLabel(sous_titre or "")
            self.sous_titre.Show(bool(sous_titre))
        self.Layout()


class BarreActions(wx.Panel):
    """Commandes natives avec vraie cible de clic et pictogramme Fluent."""
    def __init__(self, parent, actions=None):
        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL)
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_low"))
        self._boutons = []

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        espace = UTILS_UIMetrics.spacing(1)
        taille_icone = UTILS_UIMetrics.icon_size("command")
        hauteur = UTILS_UIMetrics.action_target("standard")

        for action in actions or ():
            if action is None:
                sizer.AddSpacer(UTILS_UIMetrics.spacing(2))
                continue
            bouton = wx.Button(self, label=action.label, style=wx.BU_EXACTFIT)
            bouton.SetFont(_police())
            bouton.SetMinSize((-1, hauteur))
            if action.icone:
                bitmap = UTILS_FluentIcons.GetBitmap(action.icone, taille=taille_icone)
                if bitmap is not None:
                    try:
                        bouton.SetBitmap(bitmap)
                        bouton.SetBitmapMargins((espace, 0))
                    except Exception:
                        pass
            if action.tooltip:
                bouton.SetToolTip(action.tooltip)
            if action.callback:
                bouton.Bind(wx.EVT_BUTTON, action.callback)
            self._boutons.append(bouton)
            sizer.Add(bouton, 0, wx.RIGHT, espace)

        sizer.AddStretchSpacer(1)
        marge = UTILS_UIMetrics.spacing(2)
        self.SetSizer(sizer)
        self.SetMinSize((-1, hauteur + marge))


class ListeTableau(wx.ListCtrl):
    """Liste wx native à colonnes pondérées."""
    def __init__(self, parent, colonnes, style=0):
        style |= wx.LC_REPORT | wx.LC_HRULES | wx.LC_VRULES
        wx.ListCtrl.__init__(self, parent, style=style)
        self.colonnes = tuple(colonnes or ())
        self._donnees = []

        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
        self.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        self.SetFont(_police())

        for index, colonne in enumerate(self.colonnes):
            format_colonne = wx.LIST_FORMAT_LEFT
            if colonne.align == "right":
                format_colonne = wx.LIST_FORMAT_RIGHT
            elif colonne.align == "center":
                format_colonne = wx.LIST_FORMAT_CENTRE
            self.InsertColumn(index, colonne.label, format=format_colonne, width=colonne.minimum)

        UTILS_ColonnesResponsive.Installer(
            self,
            [(colonne.minimum, colonne.poids) for colonne in self.colonnes],
            marge=UTILS_UIMetrics.spacing(6),
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
        wx.Panel.__init__(self, parent, style=wx.TAB_TRAVERSAL)
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        self.entete = EnteteSection(self, titre=titre, sous_titre=sous_titre)
        self.actions = BarreActions(self, actions=actions) if actions else None
        self.tableau = ListeTableau(self, colonnes=colonnes)
        self.recherche = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER) if recherche else None
        self.etat = wx.StaticText(self, label="")
        self.etat.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface_variant"))
        self.etat.SetFont(_police())

        if self.recherche is not None:
            self.recherche.ShowSearchButton(True)
            self.recherche.ShowCancelButton(True)
            self.recherche.SetDescriptiveText("Rechercher…")
            self.recherche.Bind(wx.EVT_TEXT, self._OnRecherche)
            self._donnees_source = []
        else:
            self._donnees_source = None

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.entete, 0, wx.EXPAND)
        if self.actions is not None:
            sizer.Add(self.actions, 0, wx.EXPAND)
        sizer.Add(self.tableau, 1, wx.EXPAND)

        bas = wx.BoxSizer(wx.HORIZONTAL)
        marge = UTILS_UIMetrics.spacing(2)
        if self.recherche is not None:
            bas.Add(self.recherche, 1, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, marge)
        bas.Add(self.etat, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(bas, 0, wx.EXPAND | wx.ALL, marge)

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
