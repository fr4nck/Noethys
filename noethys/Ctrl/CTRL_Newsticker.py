#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Site internet :  www.noethys.com
# Auteur:           Noethys
# Copyright:       (c) 2012 Noethys
# Licence:         Licence wxWidgets
# Based on wx.lib.ticker by Chris Mellon
#-----------------------------------------------------------

import wx
from wx.lib.wordwrap import wordwrap

from Utils import UTILS_StyleRepens as Style

if 'phoenix' in wx.PlatformInfo:
    from wx import Control
else:
    from wx import PyControl as Control


class Newsticker(Control):
    """Ticker historique conservé, mais rendu et métriques pilotés par Repens."""

    def __init__(
            self,
            parent,
            id=-1,
            pages=None,
            fgcolor=None,
            bgcolor=None,
            start=True,
            ppf=2,
            fps=20,
            pauseTime=2000,
            headingStyle=5,
            pos=wx.DefaultPosition,
            size=wx.DefaultSize,
            style=wx.NO_BORDER,
            name="Newsticker"
        ):
        Control.__init__(self, parent, id=id, pos=pos, size=size, style=style, name=name)
        self.timer = wx.Timer(self, -1)
        self.timerPause = wx.Timer(self, -1)
        self.textSize = (-1, -1)
        self.decalage = 0
        self._fps = fps
        self._ppf = ppf
        self.pauseTime = pauseTime
        self.pause = False
        self.pauseTemp = False
        self.indexPage = 0
        self.headingStyle = headingStyle
        self.headingHeight = 0

        # Les couleurs explicites restent acceptées pour les usages métier qui
        # dessinent ce contrôle sur une surface particulière. Sans override,
        # le ticker suit naturellement le thème Repens clair/sombre.
        self.SetBackgroundColour(bgcolor if bgcolor is not None else Style.couleur("surface_container_low"))
        self.SetForegroundColour(fgcolor if fgcolor is not None else Style.couleur("on_surface"))
        self.SetFont(Style.police("body"))

        self.SetPages([] if pages is None else pages)
        self.SetInitialSize(size)

        self.Bind(wx.EVT_TIMER, self.OnTick, self.timer)
        self.Bind(wx.EVT_TIMER, self.OnPause, self.timerPause)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnErase)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
        if start:
            self.Start()

    def SetPages(self, pages=None, restart=False):
        """Set pages to display."""
        if restart is True:
            self.Restart()
        self.indexPage = 0
        if pages is None:
            pages = []
        if isinstance(pages, (list, tuple)):
            self.listePages = list(pages) if pages else [wx.EmptyString]
        else:
            self.listePages = [pages]
        self.SetText(self.listePages[0])

    def OnEnter(self, event):
        if self.timerPause.IsRunning():
            self.timerPause.Stop()
        self.pause = True

    def OnLeave(self, event):
        if self.timerPause.IsRunning() is False:
            self.pause = False

    def Stop(self):
        self.timer.Stop()

    def Start(self):
        if not self.timer.IsRunning():
            self.timer.Start(int(1000 / self._fps))

    def IsTicking(self):
        return self.timer.IsRunning()

    def SetFPS(self, fps):
        self._fps = fps
        self.Stop()
        self.Start()

    def GetFPS(self):
        return self._fps

    def SetPPF(self, ppf):
        self._ppf = ppf

    def GetPPF(self):
        return self._ppf

    def SetFont(self, font):
        self.textSize = (-1, -1)
        wx.Control.SetFont(self, font)

    def SetPauseTime(self, milliseconds=2000):
        self.pauseTime = milliseconds

    def SetHeadingStyle(self, num=5):
        self.headingStyle = num

    def SetText(self, text):
        self._text = text
        self.textSize = (-1, -1)
        if not self._text:
            self.Refresh()

    def GetText(self):
        return self._text

    def GetNextPage(self):
        if self.indexPage == len(self.listePages) - 1:
            self.indexPage = 0
        else:
            self.indexPage += 1
        return self.listePages[self.indexPage]

    def UpdateExtent(self, dc, texte=""):
        if not texte:
            self.textSize = (-1, -1)
            return
        if 'phoenix' in wx.PlatformInfo:
            largeurBloc, hauteurBloc, hauteurLigne = dc.GetFullMultiLineTextExtent(texte, dc.GetFont())
        else:
            largeurBloc, hauteurBloc, hauteurLigne = dc.GetMultiLineTextExtent(texte, dc.GetFont())
        self.textSize = (largeurBloc, hauteurBloc)

    def _PoliceTitre(self):
        return Style.police("caption")

    def _CouleurTitre(self):
        return Style.couleur("on_surface_variant")

    def DrawText(self, dc):
        defaultFont = self.GetFont()
        dc.SetFont(defaultFont)

        titre = u""
        try:
            if self._text.startswith("<t>") and "</t>" in self._text:
                position = self._text.index("</t>")
                titre = self._text[3:position]
                texte = self._text[position + 4:]
            else:
                texte = self._text
        except Exception:
            texte = ""

        largeur_controle = max(1, self.GetClientSize().GetWidth())
        texte = wordwrap(texte, largeur_controle, dc, breakLongWords=True)
        self.UpdateExtent(dc, texte)
        y = self.GetClientSize().GetHeight() - self.decalage

        self.headingHeight = 0
        if titre:
            couleur_titre = self._CouleurTitre()
            police_titre = self._PoliceTitre()
            dc.SetFont(police_titre)
            largeur_titre, hauteur_titre = dc.GetTextExtent(titre)
            petit = Style.espace(1)
            moyen = Style.espace(2)

            if self.headingStyle == 1:
                dc.SetBrush(wx.Brush(Style.couleur("surface_container_high")))
                dc.SetPen(wx.TRANSPARENT_PEN)
                hauteur = hauteur_titre + petit
                dc.DrawRectangle(0, y + petit, largeur_titre + moyen * 2, hauteur)
                dc.SetTextForeground(Style.couleur("on_surface"))
                dc.DrawText(titre, moyen, y + petit)
                self.headingHeight = hauteur + moyen

            elif self.headingStyle == 2:
                dc.SetPen(wx.Pen(Style.couleur("outline_variant")))
                dc.DrawLine(0, y + hauteur_titre + petit, largeur_titre + moyen, y + hauteur_titre + petit)
                dc.SetTextForeground(couleur_titre)
                dc.DrawText(titre, 0, y)
                self.headingHeight = hauteur_titre + petit * 2

            elif self.headingStyle == 3:
                dc.SetPen(wx.Pen(Style.couleur("outline_variant")))
                centre = y + max(1, hauteur_titre // 2)
                dc.DrawLine(0, centre, moyen, centre)
                dc.DrawLine(largeur_titre + moyen * 2, centre, largeur_titre + moyen * 3, centre)
                dc.SetTextForeground(couleur_titre)
                dc.DrawText(titre, moyen + petit, y)
                self.headingHeight = hauteur_titre + petit

            elif self.headingStyle == 4:
                dc.SetBrush(wx.Brush(Style.couleur("primary")))
                dc.SetPen(wx.TRANSPARENT_PEN)
                marqueur = max(Style.px(3), petit)
                dc.DrawRectangle(petit, y + max(0, (hauteur_titre - marqueur) // 2), marqueur, marqueur)
                dc.SetTextForeground(couleur_titre)
                dc.DrawText(titre, petit + marqueur + petit, y)
                self.headingHeight = hauteur_titre + petit

            elif self.headingStyle == 5:
                dc.SetTextForeground(couleur_titre)
                dc.DrawText(titre, 0, y)
                self.headingHeight = hauteur_titre + petit

        dc.SetTextForeground(self.GetForegroundColour())
        dc.SetFont(defaultFont)
        taille = self.GetClientSize()
        dc.DrawLabel(
            texte,
            wx.Rect(
                x=0,
                y=int(y + self.headingHeight),
                width=max(1, taille.GetWidth()),
                height=max(1, taille.GetHeight()),
            ),
        )

    def OnPause(self, event):
        self.pause = False
        self.pauseTemp = True
        self.timerPause.Stop()

    def Restart(self):
        self.timerPause.Stop()
        self.decalage = 0
        self.pauseTemp = False
        self.pause = False

    def OnTick(self, evt):
        if self.pause is False:
            self.decalage += self._ppf
            yHautBloc = self.GetClientSize().GetHeight() - self.decalage + self.headingHeight
            yBasBloc = yHautBloc + self.textSize[1]
            if yBasBloc < 0:
                self.decalage = 0
                self.pauseTemp = False
                self.SetText(self.GetNextPage())

        yHautBloc = self.GetClientSize().GetHeight() - self.decalage
        yBasBloc = yHautBloc + self.textSize[1] + self.headingHeight

        if self.pauseTime > 0 and yHautBloc < 2 and self.pause is False and self.pauseTemp is False:
            self.pause = True
            self.pauseTemp = True
            self.timerPause.Start(self.pauseTime)

        self.Refresh()

    def OnPaint(self, evt):
        try:
            dc = wx.BufferedPaintDC(self)
            dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
            dc.Clear()
            self.DrawText(dc)
        except Exception:
            pass

    def OnErase(self, evt):
        pass

    def AcceptsFocus(self):
        return False

    def DoGetBestSize(self):
        return (Style.px(100), Style.hauteur_panneau("compact"))

    def ShouldInheritColours(self):
        return False


if __name__ == '__main__':
    app = wx.App()
    f = wx.Frame(None)
    p = wx.Panel(f)
    Style.appliquer_fenetre(p, "surface")
    pages = [
        "<t>PAGE 1</t>This is the first page.",
        "<t>PAGE 2</t>This is the second page\nwith multiline text.",
        "This page is without heading",
    ]
    t = Newsticker(p, pages=pages)
    s = wx.BoxSizer(wx.VERTICAL)
    s.Add(t, flag=wx.GROW, proportion=1)
    p.SetSizer(s)
    f.Show()
    app.MainLoop()
