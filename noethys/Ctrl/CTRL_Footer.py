#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-14 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import datetime
import six

from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics

if 'phoenix' in wx.PlatformInfo:
    from wx import Control
else:
    from wx import PyControl as Control


class Footer(Control):
    """Pied de liste aligné sur les colonnes réellement affichées."""

    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.NO_BORDER, name="footer"):
        self.hauteur = UTILS_UIMetrics.row_height("table")
        self.afficherColonneDroite = True

        self.listview = None
        self.dictColonnes = {}
        self.dictTotaux = {}
        self.listeImpression = []
        Control.__init__(self, parent, id=id, pos=pos, size=size, style=style, name=name)
        self.SetInitialSize(size)
        self.SetMinSize((-1, self.hauteur))
        self.AppliquerTheme()

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnErase)
        self.Bind(wx.EVT_SIZE, self.MAJ_affichage)

    def AppliquerTheme(self):
        sombre = UTILS_Interface.EstSombre()
        fond = UTILS_Interface.GetCouleurRole("surface_container", sombre=sombre)
        texte = UTILS_Interface.GetCouleurRole("on_surface_variant", sombre=sombre)
        try:
            self.SetBackgroundColour(fond)
            self.SetForegroundColour(texte)
        except Exception:
            pass

    def _PoliceFooter(self):
        try:
            police = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
            facteur = UTILS_Interface.GetTailleTexte() / 100.0
            police.SetPointSize(max(7, int(round(police.GetPointSize() * facteur))))
            return police
        except Exception:
            return self.GetFont()

    def MAJ_affichage(self, event=None):
        self.hauteur = UTILS_UIMetrics.row_height("table")
        try:
            self.SetMinSize((-1, self.hauteur))
        except Exception:
            pass
        self.Refresh()
        if event is not None:
            event.Skip()

    def MAJ_totaux(self):
        self.dictTotaux = {}
        if self.listview is None:
            return
        for track in self.listview.innerList:
            for nomColonne, dictColonne in self.dictColonnes.items():
                if dictColonne["mode"] == "total" and hasattr(track, nomColonne):
                    total = getattr(track, nomColonne)
                    if nomColonne not in self.dictTotaux:
                        self.dictTotaux[nomColonne] = 0
                        if dictColonne.get("format") in ("temps", "duree"):
                            self.dictTotaux[nomColonne] = datetime.timedelta(0)
                    if total is not None:
                        self.dictTotaux[nomColonne] += total

    def MAJ(self):
        self.MAJ_totaux()
        self.MAJ_affichage()

    def DrawColonne(self, dc, x, largeur, label="", alignement=None, couleur=None, font=None):
        if largeur <= 0:
            return
        render = wx.RendererNative.Get()
        options = wx.HeaderButtonParams()
        options.m_labelText = label
        if alignement:
            options.m_labelAlignment = alignement
        if couleur:
            options.m_labelColour = couleur
        if font:
            options.m_labelFont = font
        hauteur = max(self.hauteur, self.GetClientSize().GetHeight())
        render.DrawHeaderButton(self, dc, (x, 0, largeur, hauteur), params=options)

    def _LargeurColonne(self, index, col):
        """Suit la largeur effective du ListCtrl, pas la largeur historique du modèle."""
        try:
            largeur = int(self.listview.GetColumnWidth(index))
            if largeur >= 0:
                return largeur
        except Exception:
            pass
        try:
            return max(0, int(col.width))
        except Exception:
            return 0

    def Paint(self, dc):
        if self.listview is None:
            return

        dc.SetFont(self.GetFont())
        try:
            x = -self.listview.GetScrollPos(wx.HORIZONTAL)
        except Exception:
            x = 0

        self.listeImpression = []
        dernierTexte = ""
        for indexColonne, col in enumerate(self.listview.columns):
            texte = ""
            font = self._PoliceFooter()
            couleur = UTILS_Interface.GetCouleurRole("on_surface_variant", sombre=UTILS_Interface.EstSombre())
            largeur = self._LargeurColonne(indexColonne, col)
            converter = col.stringConverter
            nom = col.valueGetter

            if col.align == "left":
                alignement = wx.ALIGN_LEFT
            elif col.align == "centre":
                alignement = wx.ALIGN_CENTER
            elif col.align == "right":
                alignement = wx.ALIGN_RIGHT
            else:
                alignement = wx.ALIGN_LEFT

            mode = None
            if nom in self.dictColonnes:
                infoColonne = self.dictColonnes[nom]
                mode = infoColonne["mode"]

                if mode == "total":
                    if nom in self.dictTotaux:
                        texte = self.dictTotaux[nom]
                    else:
                        texte = datetime.timedelta(0) if infoColonne.get("format") in ("temps", "duree") else 0
                    if converter is not None:
                        texte = converter(texte)
                    liste_types = (int, float, long) if six.PY2 else (int, float)
                    if type(texte) in liste_types:
                        texte = str(texte)

                elif mode == "nombre":
                    nombre = len(self.listview.innerList)
                    texte = u"%d %s" % (nombre, infoColonne["pluriel"] if nombre > 1 else infoColonne["singulier"])

                elif mode == "texte":
                    texte = infoColonne["texte"]

                if "alignement" in infoColonne:
                    alignement = infoColonne["alignement"]
                if "font" in infoColonne:
                    font = infoColonne["font"]
                # Compatibilité métier : une couleur explicitement fournie reste
                # possible, mais le défaut est toujours le rôle sémantique.
                if "couleur" in infoColonne:
                    couleur = infoColonne["couleur"]

            ajustement = UTILS_UIMetrics.spacing(1) if mode != "total" and dernierTexte == "" else 0
            self.DrawColonne(dc, x - ajustement, largeur + ajustement, texte, alignement, couleur, font)
            x += largeur
            self.listeImpression.append({"texte": texte, "alignement": alignement})
            dernierTexte = texte if mode == "total" else ""

        if self.afficherColonneDroite:
            self.DrawColonne(dc, x, max(0, self.GetClientSize().GetWidth() - x))

    def GetDonneesImpression(self, typeInfo="texte"):
        return [info[typeInfo] for info in self.listeImpression][1:]

    def OnPaint(self, evt):
        self.AppliquerTheme()
        dc = wx.BufferedPaintDC(self)
        try:
            dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        except Exception:
            pass
        dc.Clear()
        self.Paint(dc)

    def OnErase(self, evt):
        pass

    def AcceptsFocus(self):
        return False

    def DoGetBestSize(self):
        return (100, self.hauteur)

    def ShouldInheritColours(self):
        return False


if __name__ == '__main__':
    app = wx.App()
    f = wx.Frame(None)
    p = wx.Panel(f)
    t = Footer(p)
    s = wx.BoxSizer(wx.VERTICAL)
    s.Add(t, flag=wx.GROW, proportion=1)
    p.SetSizer(s)
    f.Show()
    app.MainLoop()
