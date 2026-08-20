#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import sqlite3
import wx

import Chemins
from Utils.UTILS_Traduction import _
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Ctrl import CTRL_Bouton_image


class SaisiePays(wx.Panel):
    """Sélection d'un pays ou d'une nationalité."""

    def __init__(self, parent, mode="pays"):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.mode = mode
        self.IDpays = None

        self.image_pays = wx.StaticBitmap(self, -1, self._ChargeDrapeau("france"))
        self.bouton_pays = CTRL_Bouton_image.CTRL(
            self,
            texte="",
            iconeFluent="edit",
            tailleImage=(UTILS_UIMetrics.icon_size("inline"), UTILS_UIMetrics.icon_size("inline")),
        )

        self._AppliqueStyle()
        self.__do_layout()
        self.Bind(wx.EVT_BUTTON, self.OnBoutonPays, self.bouton_pays)
        self.SetValue(100)

    def _ChargeDrapeau(self, code):
        chemin = Chemins.GetStaticPath("Images/Drapeaux/%s.png" % code)
        try:
            image = wx.Image(chemin, wx.BITMAP_TYPE_PNG)
            hauteur = UTILS_UIMetrics.icon_size("inline")
            largeur = max(hauteur, int(round(hauteur * 1.15)))
            if image.IsOk():
                image = image.Scale(largeur, hauteur, wx.IMAGE_QUALITY_HIGH)
                return wx.Bitmap(image)
        except Exception:
            pass
        return wx.Bitmap(chemin, wx.BITMAP_TYPE_PNG)

    def _AppliqueStyle(self):
        try:
            self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))
            cible = UTILS_UIMetrics.action_target("standard")
            self.image_pays.SetMinSize((cible, cible))
        except Exception:
            pass

    def __do_layout(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.image_pays, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, UTILS_UIMetrics.spacing(1))
        sizer.Add(self.bouton_pays, 0, wx.ALIGN_CENTER_VERTICAL)
        self.SetSizer(sizer)
        self.Fit()
        self.Layout()

    def SetValue(self, IDpays=None, nomPays=None):
        """Recherche par l'IDpays ou le nom du pays."""
        if IDpays is None and nomPays is None:
            return
        if IDpays is not None:
            pays = self.Recherche_Pays(IDpays=IDpays)
        if nomPays is not None:
            pays = self.Recherche_Pays(nomPays=nomPays)
        self.IDpays = pays[0]
        self.image_pays.SetBitmap(self._ChargeDrapeau(pays[1]))
        if self.mode == "pays":
            self.bouton_pays.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour sélectionner un autre pays de naissance")))
            self.image_pays.SetToolTip(wx.ToolTip(_(u"Pays de naissance : %s") % pays[2]))
        else:
            self.image_pays.SetToolTip(wx.ToolTip(_(u"Nationalité : %s") % pays[3]))
            self.bouton_pays.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour sélectionner une autre nationalité")))
        self.Layout()

    def GetValue(self):
        return self.IDpays

    def Recherche_Pays(self, IDpays=0, nomPays=""):
        """Récupération de la liste des pays dans la base."""
        con = sqlite3.connect(Chemins.GetStaticPath("Databases/Geographie.dat"))
        cur = con.cursor()
        if nomPays == "":
            req = "SELECT IDpays, code_drapeau, nom, nationalite FROM pays WHERE IDpays=%d" % IDpays
        else:
            req = "SELECT IDpays, code_drapeau, nom, nationalite FROM pays WHERE nom='%s'" % nomPays
        cur.execute(req)
        listePays = cur.fetchall()
        con.close()
        if len(listePays) == 0:
            return
        return listePays[0]

    def OnBoutonPays(self, event):
        from Dlg import DLG_Saisie_pays
        dlg = DLG_Saisie_pays.Dialog_pays(None, typeSelection=self.mode)
        if dlg.ShowModal() == wx.ID_OK:
            IDpays = dlg.GetIDpays()
            self.SetValue(IDpays=IDpays)
        dlg.Destroy()


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        self.ctrl = SaisiePays(panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 0, wx.ALL, UTILS_UIMetrics.spacing(2))
        panel.SetSizer(sizer)
        cadre = wx.BoxSizer(wx.VERTICAL)
        cadre.Add(panel, 1, wx.EXPAND)
        self.SetSizer(cadre)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
