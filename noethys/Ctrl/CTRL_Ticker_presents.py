#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-13 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import datetime

import wx
from wx.lib.ticker import Ticker

import GestionDB
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


def _CouleurTexteLisible(fond):
    """Choisit un contraste lisible pour un fond explicitement personnalisé."""
    try:
        luminance = 0.2126 * fond.Red() + 0.7152 * fond.Green() + 0.0722 * fond.Blue()
        # Cas exceptionnel : le fond est fourni par le métier et n'appartient
        # donc pas nécessairement à la palette sémantique active.
        return wx.Colour(24, 24, 24) if luminance >= 150 else wx.Colour(248, 248, 248)
    except Exception:
        return Style.couleur("on_surface")


class CTRL(wx.Panel):
    """Ticker des présents, actualisé périodiquement et aligné sur Repens."""

    def __init__(self, parent, delai=60, listeActivites=[], fps=20, ppf=2, couleurFond=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.BORDER_NONE)
        self.parent = parent
        self.delai = delai
        self.listeActivites = listeActivites

        if couleurFond is None:
            fond = Style.couleur("surface_container")
            texte = Style.couleur("on_surface")
            Style.appliquer_fenetre(self, "surface_container")
        else:
            fond = couleurFond
            texte = _CouleurTexteLisible(fond)
            self.SetBackgroundColour(fond)
            self.SetForegroundColour(texte)

        self.SetMinSize((-1, Style.hauteur_panneau("compact")))

        self.timer = wx.Timer(self, -1)
        self.ticker = Ticker(self)
        self.ticker.SetBackgroundColour(fond)
        self.ticker.SetForegroundColour(texte)
        self.ticker.SetFPS(fps)
        self.ticker.SetPPF(ppf)
        self.ticker.SetFont(Style.police("label"))

        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.ticker, 1, wx.EXPAND | wx.ALL, Style.espace(2))
        self.SetSizer(sizer_base)
        self.Layout()

        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

    def SetTexte(self, texte=u""):
        self.ticker.SetText(texte)

    def Stop(self):
        """Stoppe le déplacement du texte et le rafraîchissement périodique."""
        if self.timer.IsRunning():
            self.timer.Stop()
        if self.ticker.IsTicking():
            self.ticker.Stop()

    def Start(self):
        """Démarre le rafraîchissement périodique."""
        if not self.timer.IsRunning():
            self.timer.Start(self.delai * 1000)

    def OnTimer(self, event):
        self.MAJ()

    def SetActivites(self, listeActivites=[]):
        self.listeActivites = listeActivites

    def MAJ(self):
        try:
            texte = self.GetTexte(self.listeActivites)
            self.SetTexte(texte)
        except Exception:
            texte = u""

        if len(texte) > 0:
            etat = True
            if self.ticker.IsTicking() is False:
                self.ticker.Start()
        else:
            etat = False
            if self.ticker.IsTicking():
                self.ticker.Stop()
        try:
            self.parent.AffichePresents(etat)
        except Exception:
            pass

    def JoinListe(self, listeTemp=[]):
        if len(listeTemp) > 2:
            return _(u"%s et %s") % (u", ".join(listeTemp[:-1]), listeTemp[-1])
        return _(u" et ").join(listeTemp)

    def GetTexte(self, listeActivites=[]):
        """Récupère les effectifs présents dans la base de données."""
        if len(listeActivites) == 0:
            conditionActivites = "()"
        elif len(listeActivites) == 1:
            conditionActivites = "(%d)" % listeActivites[0]
        else:
            conditionActivites = str(tuple(listeActivites))

        now = datetime.datetime.now()
        date = datetime.date(now.year, now.month, now.day)
        heure = "%02d:%02d" % (now.hour, now.minute)

        DB = GestionDB.DB()
        req = """SELECT activites.IDactivite, activites.nom, groupes.IDgroupe, groupes.nom, groupes.ordre, COUNT(IDconso), SUM(quantite)
        FROM consommations
        LEFT JOIN activites ON activites.IDactivite = consommations.IDactivite
        LEFT JOIN groupes ON groupes.IDgroupe = consommations.IDgroupe
        WHERE consommations.IDactivite IN %s
        AND date = '%s'
        AND heure_debut <= '%s'
        AND heure_fin >= '%s'
        AND consommations.etat IN ("reservation", "present")
        GROUP BY consommations.IDactivite, consommations.IDindividu, groupes.IDgroupe
        ORDER BY activites.nom, groupes.ordre;""" % (conditionActivites, date, heure, heure)
        DB.ExecuterReq(req)
        listeConso = DB.ResultatReq()
        DB.Close()

        if len(listeConso) == 0:
            return u""

        dictTemp = {}
        listeActivitesTriees = []
        for IDactivite, nomActivite, IDgroupe, nomGroupe, ordreGroupe, nbreConso, quantite in listeConso:
            if IDactivite not in dictTemp:
                dictTemp[IDactivite] = {"nom": nomActivite, "nbre": 0, "groupes": {}}
                listeActivitesTriees.append(IDactivite)
            if IDgroupe not in dictTemp[IDactivite]["groupes"]:
                dictTemp[IDactivite]["groupes"][IDgroupe] = {"nom": nomGroupe, "ordre": ordreGroupe, "nbre": 0}
            dictTemp[IDactivite]["groupes"][IDgroupe]["nbre"] += 1
            dictTemp[IDactivite]["nbre"] += 1

        listeTextes = []
        for IDactivite in listeActivitesTriees:
            nomActivite = dictTemp[IDactivite]["nom"]
            listeGroupes = []
            for IDgroupe, dictGroupe in dictTemp[IDactivite]["groupes"].items():
                label = u"%d %s" % (dictGroupe["nbre"], dictGroupe["nom"])
                listeGroupes.append((dictGroupe["ordre"], label))
            listeGroupes.sort()
            groupes = [label for ordre, label in listeGroupes]

            nbre = dictTemp[IDactivite]["nbre"]
            temp = _(u"individu") if nbre == 1 else _(u"individus")
            listeTextes.append(_(u"%d %s sur l'activité %s (%s)") % (nbre, temp, nomActivite, self.JoinListe(groupes)))

        return _(u"Il y a actuellement %s") % self.JoinListe(listeTextes)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1, name="test1")
        Style.appliquer_fenetre(panel, "surface")
        self.ctrl = CTRL(panel, delai=60, listeActivites=[1])
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, Style.espace(2))
        panel.SetSizer(sizer)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(panel, 1, wx.EXPAND)
        self.SetSizer(principal)
        self.Layout()
        self.ctrl.MAJ()
        self.ctrl.Start()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "OL TEST")
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
