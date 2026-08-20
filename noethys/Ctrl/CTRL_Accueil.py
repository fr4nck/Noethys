#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import Chemins
import wx
import datetime
import sqlite3
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from wx.lib.wordwrap import wordwrap


def ConvertVersionTuple(texteVersion=""):
    return tuple(int(num) for num in texteVersion.split("."))


def GetAnnonce():
    """Récupère l'annonce locale applicable à la date du jour."""
    dateJour = datetime.date.today()
    dictAnnonce = None
    found = False

    if not found:
        try:
            con = sqlite3.connect(Chemins.GetStaticPath("Databases/Annonces.dat"))
            cur = con.cursor()

            def ListeEnDict(donnees):
                IDannonce, image, titre, texte_html = donnees
                return {
                    "IDannonce": IDannonce,
                    "image": image,
                    "titre": titre,
                    "texte_html": texte_html,
                }

            req = """SELECT IDannonce, image, titre, texte_html FROM annonces_dates
            WHERE date_debut<='%s' AND date_fin>='%s'
            ORDER BY date_debut;""" % (dateJour, dateJour)
            cur.execute(req)
            listeAnnonces = cur.fetchall()
            if listeAnnonces:
                dictAnnonce = ListeEnDict(listeAnnonces[0])
                found = True

            if not found:
                req = """SELECT IDannonce, image, titre, texte_html FROM annonces_periodes
                WHERE jour_debut<=%d AND mois_debut<=%d AND jour_fin>=%d AND mois_fin>=%d
                ORDER BY jour_debut, mois_debut;""" % (
                    dateJour.day,
                    dateJour.month,
                    dateJour.day,
                    dateJour.month,
                )
                cur.execute(req)
                listeAnnonces = cur.fetchall()
                if listeAnnonces:
                    dictAnnonce = ListeEnDict(listeAnnonces[0])
                    found = True

            if not found:
                cur.execute(
                    """SELECT IDannonce, image, titre, texte_html FROM annonces_aleatoires
                    ORDER BY RANDOM() LIMIT 1;"""
                )
                listeAnnonces = cur.fetchall()
                if listeAnnonces:
                    dictAnnonce = ListeEnDict(listeAnnonces[0])

            con.close()
        except Exception:
            return None

    return dictAnnonce


class Panel(wx.Panel):
    """Accueil neutre : le contenu prime sur l'ancien papier peint historique."""

    def __init__(self, parent, size=(-1, -1)):
        wx.Panel.__init__(self, parent, name="panel_accueil", id=-1, size=size, style=wx.TAB_TRAVERSAL)
        self._annonce = None
        self._annonce_chargee = False
        self.AppliquerTheme()

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda event: None)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def AppliquerTheme(self):
        try:
            self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))
            self.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        except Exception:
            pass

    def _GetAnnonce(self):
        # L'ancienne vue relisait SQLite à chaque paint/resize. Le contenu ne
        # change pas pendant une session : une lecture suffit.
        if not self._annonce_chargee:
            self._annonce = GetAnnonce()
            self._annonce_chargee = True
        return self._annonce

    def OnSize(self, event):
        self.Refresh(False)
        event.Skip()

    def _Police(self, delta=0, gras=False):
        police = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
        try:
            base = max(8, police.GetPointSize())
            facteur = UTILS_Interface.GetTailleTexte() / 100.0
            police.SetPointSize(max(8, int(round((base + delta) * facteur))))
            if gras:
                police.SetWeight(wx.FONTWEIGHT_SEMIBOLD if hasattr(wx, "FONTWEIGHT_SEMIBOLD") else wx.FONTWEIGHT_BOLD)
        except Exception:
            pass
        return police

    def OnPaint(self, event):
        self.AppliquerTheme()
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()

        largeur, hauteur = self.GetClientSize()
        if largeur <= 0 or hauteur <= 0:
            return

        fond = UTILS_Interface.GetCouleurRole("surface")
        panneau = UTILS_Interface.GetCouleurRole("surface_container")
        texte = UTILS_Interface.GetCouleurRole("on_surface")
        secondaire = UTILS_Interface.GetCouleurRole("on_surface_variant")
        accent = UTILS_Interface.GetCouleurRole("primary")
        contour = UTILS_Interface.GetCouleurRole("outline_variant")

        dc.SetBrush(wx.Brush(fond))
        dc.SetPen(wx.Pen(fond))
        dc.DrawRectangle(0, 0, largeur, hauteur)

        marge = UTILS_UIMetrics.spacing(5)
        largeur_carte = min(max(UTILS_UIMetrics.px(420), int(largeur * 0.42)), max(0, largeur - 2 * marge))
        hauteur_carte = min(UTILS_UIMetrics.px(250), max(UTILS_UIMetrics.px(150), int(hauteur * 0.34)))
        x = marge
        y = marge

        # Surface volontairement simple : une zone de contenu élevée, pas une
        # grosse carte mobile ni un bitmap décoratif étiré.
        dc.SetBrush(wx.Brush(panneau))
        dc.SetPen(wx.Pen(contour, 1))
        dc.DrawRoundedRectangle(x, y, largeur_carte, hauteur_carte, UTILS_UIMetrics.px(6))
        dc.SetBrush(wx.Brush(accent))
        dc.SetPen(wx.Pen(accent))
        dc.DrawRectangle(x, y, UTILS_UIMetrics.px(4), hauteur_carte)

        inset = UTILS_UIMetrics.spacing(4)
        tx = x + inset
        ty = y + inset
        contenu_largeur = max(80, largeur_carte - 2 * inset)

        annonce = self._GetAnnonce()
        if annonce:
            titre = annonce.get("titre") or _(u"À savoir")
            corps = annonce.get("texte_html") or ""
        else:
            titre = _(u"Bienvenue dans Noethys")
            corps = _(u"Ouvrez un fichier ou utilisez les commandes principales pour commencer.")

        dc.SetFont(self._Police(delta=2, gras=True))
        dc.SetTextForeground(texte)
        dc.DrawText(titre, tx, ty)

        ty += dc.GetCharHeight() + UTILS_UIMetrics.spacing(2)
        dc.SetFont(self._Police())
        dc.SetTextForeground(secondaire)
        corps = wordwrap(corps, contenu_largeur, dc, breakLongWords=True)
        dc.DrawLabel(corps, wx.Rect(tx, ty, contenu_largeur, max(0, y + hauteur_carte - ty - inset)))


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = Panel(panel)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.EXPAND)
        panel.SetSizer(sizer_2)
        self.SetSize((1100, 900))
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
