#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import datetime
import sqlite3

import Chemins
import wx
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _
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
    """Accueil sobre : information utile, sans décor ni carte surdimensionnée."""

    def __init__(self, parent, size=(-1, -1)):
        wx.Panel.__init__(self, parent, name="panel_accueil", id=-1, size=size, style=wx.TAB_TRAVERSAL)
        # wx.AutoBufferedPaintDC exige explicitement ce style sous wxMSW/Phoenix.
        # Le définir dès le constructeur évite l'assertion native au premier paint.
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self._annonce = None
        self._annonce_chargee = False
        self.AppliquerTheme()

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda event: None)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def AppliquerTheme(self):
        Style.appliquer_fenetre(self, "surface")

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

    def OnPaint(self, event):
        self.AppliquerTheme()
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()

        largeur, hauteur = self.GetClientSize()
        if largeur <= 0 or hauteur <= 0:
            return

        fond = Style.couleur("surface")
        texte = Style.couleur("on_surface")
        secondaire = Style.couleur("on_surface_variant")
        accent = Style.couleur("primary")

        dc.SetBrush(wx.Brush(fond))
        dc.SetPen(wx.Pen(fond))
        dc.DrawRectangle(0, 0, largeur, hauteur)

        marge = Style.espace(5)
        barre = max(Style.px(3), 1)
        ecart = Style.espace(3)
        x_barre = marge
        x_texte = x_barre + barre + ecart
        largeur_contenu = max(
            Style.px(220),
            min(Style.px(700), largeur - x_texte - marge),
        )

        annonce = self._GetAnnonce()
        if annonce:
            titre = annonce.get("titre") or _(u"À savoir")
            corps = annonce.get("texte_html") or ""
        else:
            titre = _(u"Bienvenue dans Noethys")
            corps = _(u"Ouvrez un fichier ou utilisez les commandes principales pour commencer.")

        y = marge
        dc.SetFont(Style.police("h2"))
        dc.SetTextForeground(texte)
        dc.DrawText(titre, x_texte, y)
        hauteur_titre = dc.GetCharHeight()

        y_corps = y + hauteur_titre + Style.espace(2)
        dc.SetFont(Style.police("body"))
        dc.SetTextForeground(secondaire)
        corps = wordwrap(corps, largeur_contenu, dc, breakLongWords=True)
        lignes = corps.splitlines() or [u""]
        hauteur_ligne = max(dc.GetCharHeight(), Style.hauteur_ligne("compact"))
        hauteur_corps = max(hauteur_ligne, len(lignes) * hauteur_ligne)
        dc.DrawLabel(corps, wx.Rect(x_texte, y_corps, largeur_contenu, hauteur_corps))

        hauteur_bloc = max(
            Style.cible_action("standard"),
            (y_corps - y) + hauteur_corps,
        )
        dc.SetBrush(wx.Brush(accent))
        dc.SetPen(wx.Pen(accent))
        dc.DrawRectangle(x_barre, y, barre, hauteur_bloc)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(panel, "surface")
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
