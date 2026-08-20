#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Rendu Repens Design du tableau de fréquentation.

Le moteur métier, les requêtes et les interactions restent dans
``CTRL_Remplissage``. Cette classe remplace explicitement les renderers wx.Grid
après la construction des lignes : aucune couleur historique ni aucun effet 3D
n'est conservé dans la vue d'accueil modernisée.
"""

import datetime

import wx
import wx.lib.mixins.gridlabelrenderer as glr

from Ctrl import CTRL_Remplissage as Legacy
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics

if "phoenix" in wx.PlatformInfo:
    from wx.grid import GridCellRenderer
else:
    from wx.grid import PyGridCellRenderer as GridCellRenderer


def _couleur(role):
    return UTILS_Interface.GetCouleurRole(role)


def _etat_case(case):
    """Traduit l'état métier en rôle Repens, sans dépendre d'un ancien RGB."""
    if getattr(case, "estTotal", False):
        return "info"
    if not getattr(case, "ouvert", False):
        return "disabled"

    infos = getattr(case, "dictInfosPlaces", {}) or {}
    mode = getattr(getattr(case, "ligne", None), "modeAffichage", "")
    if mode == "nbreAttente" and (infos.get("nbreAttente") or 0) > 0:
        return "warning"

    places_initiales = infos.get("nbrePlacesInitial")
    restantes = infos.get("nbrePlacesRestantes")
    seuil = infos.get("seuil_alerte")
    if places_initiales is None or restantes is None:
        return "neutral"
    if seuil is None:
        seuil = 0
    if restantes <= 0:
        return "danger"
    if restantes <= seuil:
        return "warning"
    return "success"


def _etat_evenement(evenement):
    try:
        places = evenement.GetPlacesEvenement()
    except Exception:
        places = {}
    capacite = places.get("nbrePlacesInitial")
    restantes = places.get("nbrePlacesRestantes")
    attente = places.get("nbreAttente") or 0
    if attente > 0:
        return "warning"
    if capacite is None or restantes is None:
        return "neutral"
    if restantes <= 0:
        return "danger"
    return "success"


def _palette_etat(etat, selection=False):
    roles = {
        "neutral": ("surface_container_low", "on_surface", "outline_variant"),
        "disabled": ("disabled", "disabled_text", "outline_variant"),
        "success": ("success", "success_text", "success_text"),
        "warning": ("warning", "warning_text", "warning_text"),
        "danger": ("danger", "danger_text", "danger_text"),
        "info": ("info", "info_text", "info_text"),
        "activity": ("primary_container", "on_primary_container", "primary"),
    }
    fond, texte, contour = roles.get(etat, roles["neutral"])
    if selection:
        contour = "focus"
    return _couleur(fond), _couleur(texte), _couleur(contour)


def _rect_interieur(rect, marge=None):
    if marge is None:
        marge = UTILS_UIMetrics.px(3)
    largeur = max(1, rect.width - marge * 2)
    hauteur = max(1, rect.height - marge * 2)
    return wx.Rect(rect.x + marge, rect.y + marge, largeur, hauteur)


def _dessiner_fond(dc, rect):
    dc.SetPen(wx.TRANSPARENT_PEN)
    dc.SetBrush(wx.Brush(_couleur("surface_container_lowest")))
    dc.DrawRectangle(rect)


def _dessiner_pastille(dc, rect, etat, selection=False, rayon=None):
    fond, texte, contour = _palette_etat(etat, selection)
    if rayon is None:
        rayon = UTILS_UIMetrics.px(6)
    epaisseur = max(1, UTILS_UIMetrics.px(1))
    dc.SetBrush(wx.Brush(fond))
    dc.SetPen(wx.Pen(contour, epaisseur))
    dc.DrawRoundedRectangle(rect.x, rect.y, rect.width, rect.height, rayon)
    return texte


class RendererCase(GridCellRenderer):
    """Cellule de capacité dense, arrondie et sans relief wx historique."""

    def __init__(self, case):
        GridCellRenderer.__init__(self)
        self.case = case

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        _dessiner_fond(dc, rect)
        interieur = _rect_interieur(rect)
        etat = _etat_case(self.case)
        couleur_texte = _dessiner_pastille(dc, interieur, etat, isSelected)

        texte = grid.GetCellValue(row, col)
        font = attr.GetFont()
        if getattr(self.case, "estTotal", False):
            try:
                font.SetWeight(wx.FONTWEIGHT_SEMIBOLD)
            except Exception:
                font.SetWeight(wx.FONTWEIGHT_BOLD)
        dc.SetFont(font)
        dc.SetTextForeground(couleur_texte)
        dc.SetBackgroundMode(wx.TRANSPARENT)
        largeur, hauteur = dc.GetTextExtent(texte)
        x = interieur.x + max(0, int((interieur.width - largeur) / 2))
        y = interieur.y + max(0, int((interieur.height - hauteur) / 2))
        dc.DrawText(texte, x, y)

    def GetBestSize(self, grid, attr, dc, row, col):
        dc.SetFont(attr.GetFont())
        w, h = dc.GetTextExtent(grid.GetCellValue(row, col))
        return wx.Size(w + UTILS_UIMetrics.spacing(2), h + UTILS_UIMetrics.spacing(2))

    def Clone(self):
        return RendererCase(self.case)


class RendererCaseActivite(GridCellRenderer):
    """Séparateur d'activité discret : prune/vert du thème, plus de bande mauve brute."""

    def __init__(self, case):
        GridCellRenderer.__init__(self)
        self.case = case

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        _dessiner_fond(dc, rect)
        interieur = _rect_interieur(rect, UTILS_UIMetrics.px(2))
        couleur_texte = _dessiner_pastille(dc, interieur, "activity", isSelected, UTILS_UIMetrics.px(5))
        if row != 0:
            return
        texte = grid.GetCellValue(row, col)
        dc.SetFont(attr.GetFont())
        dc.SetTextForeground(couleur_texte)
        dc.SetBackgroundMode(wx.TRANSPARENT)
        largeur, _ = dc.GetTextExtent(texte)
        dc.DrawRotatedText(texte, interieur.x + UTILS_UIMetrics.px(2), interieur.y + largeur + UTILS_UIMetrics.px(4), 90)

    def GetBestSize(self, grid, attr, dc, row, col):
        return wx.Size(UTILS_UIMetrics.px(20), UTILS_UIMetrics.row_height("comfortable"))

    def Clone(self):
        return RendererCaseActivite(self.case)


class RendererCaseEvenement(GridCellRenderer):
    """Événements dessinés comme plusieurs blocs opérationnels dans la cellule."""

    def __init__(self, case):
        GridCellRenderer.__init__(self)
        self.case = case

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        _dessiner_fond(dc, rect)
        evenements = list(getattr(self.case, "liste_evenements", ()) or ())
        if not evenements:
            return RendererCase(self.case).Draw(grid, attr, dc, rect, row, col, isSelected)

        marge = UTILS_UIMetrics.px(3)
        espace = UTILS_UIMetrics.px(3)
        largeur_disponible = max(1, rect.width - marge * 2 - espace * (len(evenements) - 1))
        largeur_bloc = max(1, int(largeur_disponible / len(evenements)))
        hauteur_bloc = max(1, rect.height - marge * 2)

        for index, evenement in enumerate(evenements):
            x = rect.x + marge + index * (largeur_bloc + espace)
            bloc = wx.Rect(x, rect.y + marge, largeur_bloc, hauteur_bloc)
            couleur_texte = _dessiner_pastille(dc, bloc, _etat_evenement(evenement), isSelected, UTILS_UIMetrics.px(5))

            nom = getattr(evenement, "nom", "") or ""
            valeur = evenement.GetValeur() or ""
            texte = nom
            if valeur:
                texte = u"%s · %s" % (nom, valeur) if nom else valeur

            font = attr.GetFont()
            dc.SetFont(font)
            dc.SetTextForeground(couleur_texte)
            dc.SetBackgroundMode(wx.TRANSPARENT)
            limite = max(1, bloc.width - UTILS_UIMetrics.spacing(2))
            while texte and dc.GetTextExtent(texte)[0] > limite and len(texte) > 2:
                texte = texte[:-2].rstrip() + u"…"
            largeur, hauteur = dc.GetTextExtent(texte)
            dc.DrawText(
                texte,
                bloc.x + UTILS_UIMetrics.px(5),
                bloc.y + max(0, int((bloc.height - hauteur) / 2)),
            )

    def GetBestSize(self, grid, attr, dc, row, col):
        return wx.Size(UTILS_UIMetrics.px(72), UTILS_UIMetrics.px(40))

    def Clone(self):
        return RendererCaseEvenement(self.case)


class RowLabelRenderer(glr.GridLabelRenderer):
    def __init__(self, date, vacances=False):
        self.date = date
        self.vacances = vacances

    def Draw(self, grid, dc, rect, row):
        role_fond = "warning" if self.vacances else "surface_container_low"
        role_texte = "warning_text" if self.vacances else "on_surface_variant"
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush(_couleur(role_fond)))
        dc.DrawRectangle(rect)

        if self.date == datetime.date.today():
            largeur = UTILS_UIMetrics.px(4)
            dc.SetBrush(wx.Brush(_couleur("primary")))
            dc.DrawRectangle(rect.x, rect.y, largeur, rect.height)

        dc.SetTextForeground(_couleur(role_texte))
        dc.SetFont(grid.GetLabelFont())
        h_align, v_align = grid.GetRowLabelAlignment()
        self.DrawText(grid, dc, rect, grid.GetRowLabelValue(row), h_align, v_align)


class ColLabelRenderer(glr.GridLabelRenderer):
    def Draw(self, grid, dc, rect, col):
        total = grid.GetColLabelValue(col).lower().startswith("total")
        role_fond = "info" if total else "surface_container_high"
        role_texte = "info_text" if total else "on_surface"
        dc.SetPen(wx.Pen(_couleur("outline_variant"), 1))
        dc.SetBrush(wx.Brush(_couleur(role_fond)))
        dc.DrawRectangle(rect)
        dc.SetTextForeground(_couleur(role_texte))
        dc.SetFont(grid.GetLabelFont())
        h_align, v_align = grid.GetColLabelAlignment()
        self.DrawText(grid, dc, rect, grid.GetColLabelValue(col), h_align, v_align)


class CTRL(Legacy.CTRL):
    """Même grille métier, renderer et métriques entièrement Repens."""

    def __init__(self, parent, dictDonnees=None):
        Legacy.CTRL.__init__(self, parent, dictDonnees)
        self.SetBackgroundColour(_couleur("surface_container_lowest"))
        self.SetDefaultCellBackgroundColour(_couleur("surface_container_lowest"))
        self.SetDefaultCellTextColour(_couleur("on_surface"))
        self.SetLabelBackgroundColour(_couleur("surface_container_high"))
        self.SetLabelTextColour(_couleur("on_surface"))
        self.EnableGridLines(False)
        try:
            self.SetSelectionBackground(_couleur("selection"))
            self.SetSelectionForeground(_couleur("selection_text"))
        except Exception:
            pass

    def InitGrid(self):
        Legacy.CTRL.InitGrid(self)
        self._AppliquerRepens()

    def _AppliquerRepens(self):
        self.EnableGridLines(False)
        self.SetBackgroundColour(_couleur("surface_container_lowest"))
        self.SetDefaultCellBackgroundColour(_couleur("surface_container_lowest"))
        self.SetDefaultCellTextColour(_couleur("on_surface"))
        self.SetLabelBackgroundColour(_couleur("surface_container_high"))
        self.SetLabelTextColour(_couleur("on_surface"))
        self.SetRowLabelSize(max(UTILS_UIMetrics.px(150), UTILS_UIMetrics.px(132)))
        self.SetColLabelSize(max(UTILS_UIMetrics.px(46), self.GetColLabelSize()))

        for col in range(self.GetNumberCols()):
            self.SetColLabelRenderer(col, ColLabelRenderer())

        for row, ligne in list(self.dictLignes.items()):
            try:
                vacances = bool(ligne.EstEnVacances(ligne.date))
                self.SetRowLabelRenderer(row, RowLabelRenderer(ligne.date, vacances))
            except Exception:
                pass

            hauteur = UTILS_UIMetrics.row_height("comfortable")
            try:
                if any(getattr(case, "liste_evenements", None) for case in ligne.dictCases.values()):
                    hauteur = max(hauteur, UTILS_UIMetrics.px(40))
            except Exception:
                pass
            self.SetRowSize(row, hauteur)

            for col, case in list(getattr(ligne, "dictCases", {}).items()):
                if getattr(case, "typeCase", None) == "activite":
                    renderer = RendererCaseActivite(case)
                elif getattr(case, "liste_evenements", None):
                    renderer = RendererCaseEvenement(case)
                else:
                    renderer = RendererCase(case)
                self.SetCellRenderer(row, col, renderer)

        try:
            self.ForceRefresh()
        except Exception:
            self.Refresh()


class Panel(object):
    """Construit à la demande par :func:`CreerPanel` pour éviter les imports circulaires."""


def CreerPanel(parent):
    """Retourne le panneau historique avec sa grille remplacée explicitement.

    Le conteneur et ses commandes restent compatibles. La vieille grille n'est
    pas conservée dans le sizer : elle est détruite et remplacée par ``CTRL``.
    """
    from Dlg import DLG_Remplissage as LegacyPanel

    class _PanelRepens(LegacyPanel.Panel):
        def __init__(self, parent):
            LegacyPanel.Panel.__init__(self, parent)
            ancienne = self.ctrl_remplissage
            try:
                self.sizer_base.Detach(ancienne)
            except Exception:
                pass
            ancienne.Destroy()
            self.ctrl_remplissage = CTRL(self, self.dictDonnees)
            self.sizer_base.Insert(2, self.ctrl_remplissage, 1, wx.EXPAND)
            self.SetBackgroundColour(_couleur("surface"))
            self.Layout()

    return _PanelRepens(parent)
