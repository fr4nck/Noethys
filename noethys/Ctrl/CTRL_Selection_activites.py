#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import datetime

import wx
import wx.lib.agw.customtreectrl as CT

import GestionDB
from Ctrl import CTRL_Bouton_image
from Utils import UTILS_Adaptations, UTILS_Interface, UTILS_Parametres, UTILS_UIMetrics
from Utils.UTILS_Traduction import _


def _PoliceInterface():
    police = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
    facteur = UTILS_Interface.GetTailleTexte() / 100.0
    police.SetPointSize(max(8, int(round(police.GetPointSize() * facteur))))
    return police


def _StyleListe(ctrl):
    try:
        ctrl.SetFont(_PoliceInterface())
        ctrl.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
        ctrl.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
    except Exception:
        pass


class CTRL_Groupes(CT.CustomTreeCtrl):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.SIMPLE_BORDER):
        CT.CustomTreeCtrl.__init__(self, parent, id, pos, size, style)
        self.parent = parent
        self.activation = True
        self.root = self.AddRoot(_(u"Racine"))
        self.SetAGWWindowStyleFlag(wx.TR_HIDE_ROOT | wx.TR_HAS_BUTTONS | wx.TR_HAS_VARIABLE_ROW_HEIGHT)
        self.EnableSelectionVista(True)
        self.mode_importation = False
        self.dictItems = {}
        _StyleListe(self)
        self.Bind(CT.EVT_TREE_ITEM_CHECKED, self.OnCheck)

    def Activation(self, etat=True):
        self.activation = etat
        self.MAJ()

    def Importation(self):
        DB = GestionDB.DB()
        req = """SELECT groupes.IDgroupe, groupes.nom, groupes.ordre,
        activites.IDactivite, activites.nom, activites.date_fin
        FROM groupes
        LEFT JOIN activites ON activites.IDactivite = groupes.IDactivite
        ORDER BY activites.date_fin DESC;"""
        DB.ExecuterReq(req)
        listeGroupes = DB.ResultatReq()
        DB.Close()
        return listeGroupes

    def MAJ(self):
        anciensCoches = self.GetGroupes()
        self.listeDonnees = self.Importation()
        self.DeleteAllItems()
        self.root = self.AddRoot(_(u"Données"))
        self.dictItems = {}

        dictDonnees = {}
        for IDgroupe, nomGroupe, ordreGroupe, IDactivite, nomActivite, dateFinActivite in self.listeDonnees:
            if IDactivite not in dictDonnees:
                dictDonnees[IDactivite] = {
                    "nom": nomActivite,
                    "IDactivite": IDactivite,
                    "dateFinActivite": dateFinActivite,
                    "groupes": [],
                }
            dictDonnees[IDactivite]["groupes"].append((ordreGroupe, IDgroupe, nomGroupe))

        listeActivites = [(donnees["dateFinActivite"], IDactivite) for IDactivite, donnees in dictDonnees.items()]
        listeActivites.sort(reverse=True)

        for dateFinActivite, IDactivite in listeActivites:
            donneesActivite = dictDonnees[IDactivite]
            nomActivite = donneesActivite["nom"] or _(u"Activité inconnue")
            brancheActivite = self.AppendItem(self.root, nomActivite, ct_type=1)
            dataActivite = {"type": "activite", "IDactivite": IDactivite, "nom": nomActivite}
            self.SetPyData(brancheActivite, dataActivite)
            self.dictItems[brancheActivite] = dataActivite

            groupes = donneesActivite["groupes"]
            groupes.sort()
            for ordreGroupe, IDgroupe, nomGroupe in groupes:
                brancheGroupe = self.AppendItem(brancheActivite, nomGroupe, ct_type=1)
                dataGroupe = {"type": "groupe", "IDgroupe": IDgroupe, "nom": nomGroupe}
                self.SetPyData(brancheGroupe, dataGroupe)
                self.dictItems[brancheGroupe] = dataGroupe
            self.EnableChildren(brancheActivite, False)

        if not self.activation:
            self.EnableChildren(self.root, False)
        self.SetGroupes(anciensCoches)

    def OnCheck(self, event):
        self.Coche(item=event.GetItem())

    def Coche(self, item=None, etat=None):
        dictData = self.GetItemPyData(item)
        itemParent = self.GetItemParent(item)
        if etat is not None:
            self.CheckItem(item, etat)

        if dictData["type"] == "activite":
            actif = self.IsItemChecked(item)
            self.EnableChildren(item, actif)
            if not actif or not self.mode_importation:
                self.CheckChilds(item, actif)
        elif dictData["type"] == "groupe":
            if self.IsItemChecked(item):
                self.CheckItem(itemParent, True)
            elif not self.GetCochesItem(itemParent):
                self.CheckItem(itemParent, False)

    def GetCochesItem(self, item=None):
        listeItems = []
        itemTemp, cookie = self.GetFirstChild(item)
        for index in range(self.GetChildrenCount(item, recursively=False)):
            if self.IsItemChecked(itemTemp):
                listeItems.append(self.GetPyData(itemTemp))
            itemTemp, cookie = self.GetNextChild(item, cookie)
        return listeItems

    def GetGroupes(self):
        listeGroupes = [
            data["IDgroupe"] for item, data in self.dictItems.items()
            if data["type"] == "groupe" and self.IsItemEnabled(item) and self.IsItemChecked(item)
        ]
        listeGroupes.sort()
        return listeGroupes

    def SetGroupes(self, listeGroupes=None):
        if listeGroupes is None:
            listeGroupes = []
        self.mode_importation = True
        for item, data in self.dictItems.items():
            if data["type"] == "groupe":
                self.Coche(item, etat=data["IDgroupe"] in listeGroupes)
        self.mode_importation = False

    def SetActivites(self, listeActivites=None):
        if listeActivites is None:
            listeActivites = []
        for item, data in self.dictItems.items():
            if data["type"] == "activite":
                self.Coche(item, etat=data["IDactivite"] in listeActivites)


class CTRL_Groupes_activites(wx.CheckListBox):
    def __init__(self, parent):
        wx.CheckListBox.__init__(self, parent, -1)
        self.parent = parent
        self.dictDonnees = {}
        self.dictActivites = {}
        self.dictIndex = {}
        self.listeDonnees = []
        _StyleListe(self)
        self.MAJ()
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheck)

    def MAJ(self):
        self.listeDonnees = self.Importation() or []
        self.Clear()
        self.dictIndex = {}
        self.listeDonnees.sort()
        for index, (nomGroupe, IDtype_groupe_activite) in enumerate(self.listeDonnees):
            self.Append(nomGroupe or _(u"Groupe inconnu !"))
            self.dictIndex[index] = IDtype_groupe_activite

    def Importation(self):
        DB = GestionDB.DB()
        req = """SELECT IDgroupe_activite, groupes_activites.IDactivite,
        activites.nom, types_groupes_activites.nom,
        groupes_activites.IDtype_groupe_activite
        FROM groupes_activites
        LEFT JOIN types_groupes_activites ON types_groupes_activites.IDtype_groupe_activite = groupes_activites.IDtype_groupe_activite
        LEFT JOIN activites ON activites.IDactivite = groupes_activites.IDactivite
        ORDER BY types_groupes_activites.nom;"""
        DB.ExecuterReq(req)
        listeActivites = DB.ResultatReq()
        DB.Close()

        listeDonnees = []
        self.dictDonnees = {}
        self.dictActivites = {}
        for IDgroupe_activite, IDactivite, nomActivite, nomGroupe, IDtype_groupe_activite in listeActivites:
            entree = (nomGroupe, IDtype_groupe_activite)
            if entree not in listeDonnees:
                listeDonnees.append(entree)
            self.dictDonnees.setdefault(IDtype_groupe_activite, []).append(IDactivite)
            self.dictActivites[IDactivite] = nomActivite
        return listeDonnees

    def GetDictActivites(self):
        return self.dictActivites

    def GetIDcoches(self):
        listeIDcoches = []
        for index in range(len(self.listeDonnees)):
            if self.IsChecked(index):
                for IDactivite in self.dictDonnees[self.dictIndex[index]]:
                    if IDactivite not in listeIDcoches:
                        listeIDcoches.append(IDactivite)
        listeIDcoches.sort()
        return listeIDcoches

    def GetIDgroupesCoches(self):
        liste = [self.dictIndex[index] for index in range(len(self.listeDonnees)) if self.IsChecked(index)]
        liste.sort()
        return liste

    def CocheTout(self):
        for index in range(len(self.listeDonnees)):
            self.Check(index)

    def SetIDcoches(self, listeIDcoches=None):
        if listeIDcoches is None:
            listeIDcoches = []
        for index in range(len(self.listeDonnees)):
            self.Check(index, self.dictIndex[index] in listeIDcoches)

    def OnCheck(self, event):
        self.parent.OnCheck()

    def GetLabelsGroupes(self):
        return [nom for index, (nom, IDgroupe) in enumerate(self.listeDonnees) if self.IsChecked(index)]


class CTRL_Activites(wx.CheckListBox):
    def __init__(self, parent):
        wx.CheckListBox.__init__(self, parent, -1)
        self.parent = parent
        self.dictActivites = {}
        self.listeDonnees = []
        _StyleListe(self)
        self.Bind(wx.EVT_CHECKLISTBOX, self.OnCheck)

    def MAJ(self):
        self.parametres = UTILS_Parametres.ParametresCategorie(
            mode="get",
            categorie="ctrl_selection_activites",
            dictParametres={"tri": "date+nom", "cacher_obsoletes": False},
        )
        self.listeDonnees = self.Importation()
        self.SetListeChoix()

    def SetListeChoix(self):
        self.Clear()
        self.dictActivites = {}
        self.dictIndex = {}
        for index, (IDactivite, nom) in enumerate(self.listeDonnees):
            nom = nom or _(u"Activité inconnue")
            self.Append(nom)
            self.dictIndex[index] = IDactivite
            self.dictActivites[IDactivite] = nom

    def Importation(self):
        tri = "nom ASC" if self.parametres["tri"] == "nom" else "date_fin DESC, nom ASC"
        condition = ""
        if self.parametres["cacher_obsoletes"]:
            condition = "WHERE (date_fin>='%s' OR date_fin IS NULL)" % datetime.date.today()
        DB = GestionDB.DB()
        req = """SELECT IDactivite, nom
        FROM activites
        %s
        ORDER BY %s;""" % (condition, tri)
        DB.ExecuterReq(req)
        listeActivites = DB.ResultatReq()
        DB.Close()
        return listeActivites

    def GetDictActivites(self):
        return self.dictActivites

    def GetIDcoches(self):
        return [self.dictIndex[index] for index in range(len(self.listeDonnees)) if self.IsChecked(index)]

    def CocheTout(self):
        for index in range(len(self.listeDonnees)):
            self.Check(index)

    def SetIDcoches(self, listeIDcoches=None):
        if listeIDcoches is None:
            listeIDcoches = []
        for index in range(len(self.listeDonnees)):
            self.Check(index, self.dictIndex[index] in listeIDcoches)

    def OnCheck(self, event):
        self.parent.OnCheck()

    def OnBoutonOptionsActivites(self, event):
        menuPop = UTILS_Adaptations.Menu()
        item = wx.MenuItem(menuPop, 200, _(u"Trier par date de fin et nom"), kind=wx.ITEM_RADIO)
        menuPop.AppendItem(item)
        item.Check(self.parametres["tri"] == "date+nom")
        self.Bind(wx.EVT_MENU, self.SetTri1, id=200)

        item = wx.MenuItem(menuPop, 201, _(u"Trier par nom"), kind=wx.ITEM_RADIO)
        menuPop.AppendItem(item)
        item.Check(self.parametres["tri"] == "nom")
        self.Bind(wx.EVT_MENU, self.SetTri2, id=201)

        menuPop.AppendSeparator()
        item = wx.MenuItem(menuPop, 202, _(u"Masquer les activités obsolètes"), kind=wx.ITEM_CHECK)
        menuPop.AppendItem(item)
        item.Check(bool(self.parametres["cacher_obsoletes"]))
        self.Bind(wx.EVT_MENU, self.SetMasquerObsoletes, id=202)
        self.PopupMenu(menuPop)
        menuPop.Destroy()

    def SetTri1(self, event=None):
        UTILS_Parametres.Parametres(mode="set", categorie="ctrl_selection_activites", nom="tri", valeur="date+nom")
        self.MAJ()

    def SetTri2(self, event=None):
        UTILS_Parametres.Parametres(mode="set", categorie="ctrl_selection_activites", nom="tri", valeur="nom")
        self.MAJ()

    def SetMasquerObsoletes(self, event=None):
        UTILS_Parametres.Parametres(
            mode="set",
            categorie="ctrl_selection_activites",
            nom="cacher_obsoletes",
            valeur=not self.parametres["cacher_obsoletes"],
        )
        self.MAJ()


class CTRL(wx.Panel):
    def __init__(self, parent, afficheToutes=False, modeGroupes=False):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.afficheToutes = afficheToutes
        self.modeGroupes = modeGroupes
        try:
            self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))
        except Exception:
            pass

        self.radio_toutes = wx.RadioButton(self, -1, _(u"Toutes les activités"), style=wx.RB_GROUP)
        style = 0 if self.afficheToutes else wx.RB_GROUP
        self.radio_groupes_activites = wx.RadioButton(self, -1, _(u"Les groupes d'activités suivants :"), style=style)
        self.ctrl_groupes_activites = CTRL_Groupes_activites(self)
        self.radio_activites = wx.RadioButton(self, -1, _(u"Les activités suivantes :"))
        self.bouton_options_activites = CTRL_Bouton_image.CTRL(
            self,
            texte="",
            cheminImage="Images/16x16/Options.png",
            tailleImage=(UTILS_UIMetrics.icon_size("inline"), UTILS_UIMetrics.icon_size("inline")),
        )
        self.bouton_options_activites.SetToolTip(wx.ToolTip(_(u"Options d'affichage des activités")))
        self.ctrl_activites = CTRL_Activites(self)
        self.ctrl_groupes = CTRL_Groupes(self)

        hauteur_liste = UTILS_UIMetrics.row_height("comfortable") * 3
        for ctrl in (self.ctrl_groupes_activites, self.ctrl_activites, self.ctrl_groupes):
            ctrl.SetMinSize((UTILS_UIMetrics.px(240), hauteur_liste))
        for radio in (self.radio_toutes, self.radio_groupes_activites, self.radio_activites):
            try:
                radio.SetFont(_PoliceInterface())
                radio.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
            except Exception:
                pass

        if not self.modeGroupes:
            self.ctrl_activites.MAJ()
            self.ctrl_activites.Enable(self.radio_activites.GetValue())
        else:
            self.ctrl_groupes.Activation(self.radio_activites.GetValue())
        self.ctrl_activites.Show(not self.modeGroupes)
        self.ctrl_groupes.Show(self.modeGroupes)

        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioActivites, self.radio_toutes)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioActivites, self.radio_groupes_activites)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnRadioActivites, self.radio_activites)
        self.Bind(wx.EVT_BUTTON, self.ctrl_activites.OnBoutonOptionsActivites, self.bouton_options_activites)

        marge_indentation = UTILS_UIMetrics.spacing(5)
        espace = UTILS_UIMetrics.spacing(2)
        ligne_activites = wx.BoxSizer(wx.HORIZONTAL)
        ligne_activites.Add(self.radio_activites, 0, wx.ALIGN_CENTER_VERTICAL)
        ligne_activites.Add(self.bouton_options_activites, 0, wx.LEFT | wx.ALIGN_CENTER_VERTICAL, UTILS_UIMetrics.spacing(1))

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(self.radio_toutes, 0, wx.BOTTOM, espace)
        principal.Add(self.radio_groupes_activites, 0)
        principal.Add(self.ctrl_groupes_activites, 1, wx.LEFT | wx.TOP | wx.BOTTOM | wx.EXPAND, marge_indentation)
        principal.Add(ligne_activites, 0, wx.TOP, espace)
        principal.Add(self.ctrl_activites, 1, wx.LEFT | wx.TOP | wx.EXPAND, marge_indentation)
        principal.Add(self.ctrl_groupes, 1, wx.LEFT | wx.TOP | wx.EXPAND, marge_indentation)
        self.SetSizer(principal)
        self.Layout()

        self.ctrl_groupes_activites.Enable(self.radio_groupes_activites.GetValue())
        if not self.afficheToutes:
            self.radio_toutes.Show(False)

    def OnRadioActivites(self, event):
        if self.ctrl_activites.IsShown():
            self.ctrl_activites.Enable(self.radio_activites.GetValue())
        if self.ctrl_groupes.IsShown():
            self.ctrl_groupes.Activation(self.radio_activites.GetValue())
        self.ctrl_groupes_activites.Enable(self.radio_groupes_activites.GetValue())
        self.OnCheck()

    def Validation(self):
        if self.afficheToutes and self.radio_toutes.GetValue():
            return True
        if self.radio_groupes_activites.GetValue() and not self.GetActivites():
            return self._ErreurSelection()
        if self.radio_activites.GetValue():
            vide = not self.GetActivites() if not self.modeGroupes else not self.GetGroupes()
            if vide:
                return self._ErreurSelection()
        return True

    def _ErreurSelection(self):
        dlg = wx.MessageDialog(self, _(u"Vous n'avez sélectionné aucune activité !"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
        dlg.ShowModal()
        dlg.Destroy()
        return False

    def SetActivites(self, listeActivites=None):
        if listeActivites is None:
            listeActivites = []
        if not self.modeGroupes:
            self.ctrl_activites.SetIDcoches(listeActivites)
        else:
            self.ctrl_groupes.SetActivites(listeActivites)
        if listeActivites:
            self.radio_activites.SetValue(True)
            self.OnRadioActivites(None)

    def GetActivites(self):
        if self.radio_groupes_activites.GetValue():
            return self.ctrl_groupes_activites.GetIDcoches()
        if not self.modeGroupes:
            return self.ctrl_activites.GetIDcoches()
        return []

    def SetGroupes(self, listeGroupes=None):
        if listeGroupes is None:
            listeGroupes = []
        self.ctrl_groupes.SetGroupes(listeGroupes)
        if listeGroupes:
            self.radio_activites.SetValue(True)
            self.OnRadioActivites(None)

    def GetGroupes(self):
        if self.radio_activites.GetValue() and self.modeGroupes:
            return self.ctrl_groupes.GetGroupes()
        return []

    def GetDictActivites(self):
        if self.radio_groupes_activites.GetValue():
            return self.ctrl_groupes_activites.GetDictActivites()
        return self.ctrl_activites.GetDictActivites()

    def OnCheck(self):
        try:
            self.parent.OnCheckActivites()
        except Exception:
            pass

    def GetLabelActivites(self):
        if self.radio_groupes_activites.GetValue():
            return self.ctrl_groupes_activites.GetLabelsGroupes()
        dictActivites = self.GetDictActivites()
        return [dictActivites[IDactivite] for IDactivite in self.GetActivites()]

    def GetValeurs(self):
        if self.afficheToutes and self.radio_toutes.GetValue():
            return "toutes", []
        if self.radio_groupes_activites.GetValue():
            return "groupes", self.ctrl_groupes_activites.GetIDgroupesCoches()
        listeID = self.ctrl_activites.GetIDcoches() if not self.modeGroupes else self.ctrl_groupes.GetGroupes()
        return "activites", listeID

    def SetValeurs(self, mode="", listeID=None):
        if listeID is None:
            listeID = []
        if mode == "toutes":
            self.radio_toutes.SetValue(True)
        elif mode == "groupes":
            self.radio_groupes_activites.SetValue(True)
            self.ctrl_groupes_activites.SetIDcoches(listeID)
        elif mode == "activites":
            self.radio_activites.SetValue(True)
            if not self.modeGroupes:
                self.ctrl_activites.SetIDcoches(listeID)
            else:
                self.ctrl_groupes.SetGroupes(listeID)
        self.OnRadioActivites(None)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        self.ctrl = CTRL(panel, modeGroupes=False)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(3))
        panel.SetSizer(sizer)
        cadre = wx.BoxSizer(wx.VERTICAL)
        cadre.Add(panel, 1, wx.EXPAND)
        self.SetSizer(cadre)
        self.SetMinSize((UTILS_UIMetrics.px(520), UTILS_UIMetrics.px(420)))
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 560))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
