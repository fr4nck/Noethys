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
import sys

import wx
import wx.lib.masked as masked

import Chemins
import GestionDB
from Ctrl import CTRL_ActionRepens
from Utils import UTILS_Config
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


def _AppliqueStyleSaisie(ctrl, largeur_min=-1):
    Style.appliquer_saisie(ctrl)
    if largeur_min != -1:
        ctrl.SetMinSize((largeur_min, Style.cible_action("compact")))


def Importation_donnees():
    con = sqlite3.connect(Chemins.GetStaticPath("Databases/Geographie.dat"))
    cur = con.cursor()
    cur.execute("SELECT IDville, nom, cp FROM villes")
    listeVillesTmp = cur.fetchall()
    cur.execute("SELECT num_dep, num_region, departement FROM departements")
    listeDepartements = cur.fetchall()
    cur.execute("SELECT num_region, region FROM regions")
    listeRegions = cur.fetchall()
    con.close()

    DB = GestionDB.DB()
    DB.ExecuterReq("""SELECT IDcorrection, mode, IDville, nom, cp
    FROM corrections_villes; """)
    listeCorrections = DB.ResultatReq()
    DB.Close()

    dictCorrections = {}
    for IDcorrection, mode, IDville, nom, cp in listeCorrections:
        if mode == "ajout":
            listeVillesTmp.append((None, nom, cp))
        else:
            dictCorrections[IDville] = {"mode": mode, "nom": nom, "cp": cp}

    listeNomsVilles = []
    listeVilles = []
    for IDville, nom, cp in listeVillesTmp:
        valide = True
        if IDville in dictCorrections:
            correction = dictCorrections[IDville]
            if correction["mode"] == "modif":
                nom, cp = correction["nom"], correction["cp"]
            elif correction["mode"] == "suppr":
                valide = False
        if valide:
            try:
                cp = int(cp)
                listeVilles.append((nom, "%05d" % cp))
                listeNomsVilles.append(nom)
            except Exception:
                pass

    dictRegions = {num_region: region for num_region, region in listeRegions}
    dictDepartements = {num_dep: (departement, num_region) for num_dep, num_region, departement in listeDepartements}
    return listeNomsVilles, listeVilles, dictRegions, dictDepartements


class TextCtrlCp(masked.TextCtrl):
    def __init__(self, parent, id=-1, value=None, ctrlVille=None, listeVilles=None, activeAutoComplete=True, **par):
        masked.TextCtrl.__init__(self, parent, id, value, **par)
        self.parent = parent
        self.ctrlVille = ctrlVille
        self.listeVilles = listeVilles or []
        self.autoComplete = True
        _AppliqueStyleSaisie(self, Style.px(72))
        if activeAutoComplete:
            self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

    def OnKillFocus(self, event):
        if not self.autoComplete:
            event.Skip()
            return
        textCode = self.GetValue()
        villeSelect = self.ctrlVille.GetValue()
        if villeSelect != '':
            for ville, cp in self.listeVilles:
                if ville == villeSelect and cp == textCode:
                    event.Skip()
                    return

        reponses = [ville for ville, cp in self.listeVilles if cp == textCode]
        if not reponses:
            if textCode.strip() != '':
                dlg = wx.MessageDialog(self, _(u"Ce code postal n'est pas répertorié dans la base de données. \nVérifiez que vous n'avez pas fait d'erreur de saisie."), _(u"Information"), wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
            event.Skip()
            return

        resultat = reponses[0] if len(reponses) == 1 else self.ChoixVilles(textCode, reponses)
        if resultat:
            self.ctrlVille.SetValue(resultat)
            self.ctrlVille.SetSelection(0, len(resultat))
        event.Skip()

    def ChoixVilles(self, cp, listeReponses):
        listeReponses.sort()
        message = str(len(listeReponses)) + _(u" villes possèdent le code postal ") + str(cp) + _(u". Double-cliquez sur\nle nom d'une ville pour la sélectionner :")
        dlg = wx.SingleChoiceDialog(self, message, _(u"Sélection d'une ville"), listeReponses, wx.CHOICEDLG_STYLE)
        resultat = dlg.GetStringSelection() if dlg.ShowModal() == wx.ID_OK else ""
        dlg.Destroy()
        return resultat

    def SetInfobulleVille(self):
        cp = self.GetValue()
        if cp in ("", "     "):
            self.SetToolTip(wx.ToolTip(_(u"Saisissez un code postal")))
            return
        try:
            num_dep = cp[:2]
            nomDepartement, num_region = self.dictDepartements[num_dep]
            nomRegion = self.dictRegions[num_region]
            texte = _(u"Département : %s (%s)\nRégion : %s") % (nomDepartement, num_dep, nomRegion)
            self.SetToolTip(wx.ToolTip(texte))
        except Exception:
            self.SetToolTip(wx.ToolTip(_(u"Le code postal saisi ne figure pas dans la base de données")))


class TextCtrlVille(wx.TextCtrl):
    def __init__(self, parent, id=-1, value=None, ctrlCp=None, listeVilles=None, listeNomsVilles=None, activeAutoComplete=True, **par):
        wx.TextCtrl.__init__(self, parent, id, value, **par)
        self.parent = parent
        self.ctrlCp = ctrlCp
        self.listeVilles = listeVilles or []
        self.listeNomsVilles = listeNomsVilles or []
        self.ignoreEvtText = False
        self.autoComplete = True
        _AppliqueStyleSaisie(self, Style.px(150))
        if activeAutoComplete:
            self.Bind(wx.EVT_TEXT, self.OnText)
            self.Bind(wx.EVT_CHAR, self.OnChar)
            self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)

    def OnKillFocus(self, event):
        if not self.autoComplete:
            event.Skip()
            return
        villeSelect = self.GetValue()
        if villeSelect == '':
            event.Skip()
            return

        nbreCodes = self.listeNomsVilles.count(villeSelect)
        if nbreCodes > 1:
            listeCodes = [cp for ville, cp in self.listeVilles if villeSelect == ville]
            resultat = self.ChoixCodes(villeSelect, listeCodes)
            if resultat:
                self.ctrlCp.SetValue(resultat)
        elif nbreCodes == 0:
            dlg = wx.MessageDialog(self, _(u"Cette ville n'est pas répertoriée dans la base de données. \nVérifiez que vous n'avez pas fait d'erreur de saisie."), _(u"Information"), wx.OK | wx.ICON_INFORMATION)
            dlg.ShowModal()
            dlg.Destroy()
        event.Skip()

    def OnChar(self, event):
        if event.GetKeyCode() == 8:
            self.ignoreEvtText = True
        event.Skip()

    def OnText(self, event):
        if not self.autoComplete:
            event.Skip()
            return
        if self.ignoreEvtText:
            self.ignoreEvtText = False
            event.Skip()
            return

        currentText = event.GetString().upper()
        for ville, cp in self.listeVilles:
            if ville.startswith(currentText):
                self.ignoreEvtText = True
                self.SetValue(ville)
                self.SetInsertionPoint(len(currentText))
                self.SetSelection(len(currentText), len(ville))
                self.ctrlCp.SetValue(cp)
                return
        self.ctrlCp.SetValue('')
        event.Skip()

    def ChoixCodes(self, ville, listeReponses):
        listeReponses.sort()
        message = str(len(listeReponses)) + _(u" villes portent le nom ") + str(ville) + _(u". Double-cliquez sur\nle code postal d'une ville pour la sélectionner :")
        dlg = wx.SingleChoiceDialog(self, message, _(u"Sélection d'une ville"), listeReponses, wx.CHOICEDLG_STYLE)
        resultat = dlg.GetStringSelection() if dlg.ShowModal() == wx.ID_OK else ""
        dlg.Destroy()
        return resultat


class Adresse(wx.Panel):
    def __init__(self, parent, size=(-1, -1)):
        wx.Panel.__init__(self, parent, id=-1, size=size, style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        Style.appliquer_fenetre(self, "surface")
        self.listeNomsVilles, self.listeVilles, self.dictRegions, self.dictDepartements = Importation_donnees()
        activeAutoComplete = UTILS_Config.GetParametre("adresse_autocomplete", True)
        mask_cp = UTILS_Config.GetParametre("mask_cp", "#####")

        self.ctrl_cp = TextCtrlCp(self, value="", listeVilles=self.listeVilles, activeAutoComplete=activeAutoComplete, style=wx.TE_CENTRE, mask=mask_cp)
        self.label_ville = wx.StaticText(self, -1, _(u"Ville :"))
        Style.appliquer_texte(self.label_ville, role="label", role_texte="on_surface", role_fond="surface")
        self.ctrl_ville = TextCtrlVille(self, value="", ctrlCp=self.ctrl_cp, listeVilles=self.listeVilles, listeNomsVilles=self.listeNomsVilles, activeAutoComplete=activeAutoComplete)
        self.ctrl_cp.ctrlVille = self.ctrl_ville
        self.bouton_options = CTRL_ActionRepens.CTRL(
            self,
            label=u"",
            icone="search",
            variante="ghost",
            tooltip=_(u"Rechercher une ville ou saisir une ville absente de la base"),
            compact=True,
        )

        if "linux" in sys.platform:
            self.ctrl_ville.Enable(False)

        self.ctrl_cp.SetToolTip(wx.ToolTip(_(u"Saisissez ici le code postal de la ville")))
        self.ctrl_ville.SetToolTip(wx.ToolTip(_(u"Saisissez ici le nom de la ville")))

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.ctrl_cp, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.label_ville, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, Style.espace(2))
        sizer.Add(self.ctrl_ville, 1, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, Style.espace(1))
        sizer.Add(self.bouton_options, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, Style.espace(1))
        self.SetSizer(sizer)
        self.Layout()
        self.Bind(wx.EVT_BUTTON, self.OnOptionsVille, self.bouton_options)

    def GetValueCP(self):
        cp = self.ctrl_cp.GetValue()
        return None if cp == "     " else cp

    def GetValueVille(self):
        ville = self.ctrl_ville.GetValue()
        return None if ville == "" else ville

    def SetValueCP(self, cp=""):
        if cp is None:
            return None
        try:
            self.ctrl_cp.SetValue(cp)
            return True
        except Exception:
            return False

    def SetValueVille(self, ville=""):
        if ville is not None:
            self.ctrl_ville.autoComplete = False
            self.ctrl_ville.SetValue(ville)
            self.ctrl_ville.autoComplete = True

    def OnOptionsVille(self, event):
        from Dlg import DLG_Villes
        dlg = DLG_Villes.Dialog(None, modeImportation=True)
        if dlg.ShowModal() == wx.ID_OK:
            cp, ville = dlg.GetVille()
            self.SetValueCP(cp)
            self.SetValueVille(ville)
        dlg.Destroy()

        self.listeNomsVilles, self.listeVilles, self.dictRegions, self.dictDepartements = Importation_donnees()
        self.ctrl_cp.listeVilles = self.listeVilles
        self.ctrl_ville.listeVilles = self.listeVilles
        self.ctrl_ville.listeNomsVilles = self.listeNomsVilles


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(panel, "surface")
        self.ctrl = Adresse(panel)
        self.ctrl.SetValueCP("69380")
        self.ctrl.SetValueVille("CHASSELAY")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 0, wx.ALL | wx.EXPAND, Style.espace(2))
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
