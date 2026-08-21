#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Licence :        GNU GPL
#------------------------------------------------------------------------
"""Vue hebdomadaire read-only des présences Teamworks."""

import datetime
import threading

import wx
import wx.grid as gridlib

from Ctrl import CTRL_ActionRepens
from Utils import UTILS_Aui
from Utils import UTILS_Responsive
from Utils import UTILS_StyleRepens as Style
from Utils import UTILS_Teamworks_Planning
from Utils.UTILS_Traduction import _


JOURS_COURTS = (_(u"Lun"), _(u"Mar"), _(u"Mer"), _(u"Jeu"), _(u"Ven"), _(u"Sam"), _(u"Dim"))


class Panel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name="planning_semaine", style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        Style.appliquer_fenetre(self, "surface")

        self.date_reference = datetime.date.today()
        self.lundi = self._GetLundi(self.date_reference)
        self._chargement = False

        self.btn_precedent = CTRL_ActionRepens.CTRL(
            self,
            label=u"",
            icone="arrow_left",
            variante="ghost",
            tooltip=_(u"Afficher la semaine précédente"),
            compact=True,
        )
        self.btn_aujourdhui = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Aujourd'hui"),
            icone="calendar",
            variante="secondaire",
            tooltip=_(u"Revenir à la semaine en cours"),
            compact=True,
        )
        self.btn_suivant = CTRL_ActionRepens.CTRL(
            self,
            label=u"",
            icone="arrow_right",
            variante="ghost",
            tooltip=_(u"Afficher la semaine suivante"),
            compact=True,
        )
        self.label_semaine = wx.StaticText(self, -1, "")
        self.label_source = wx.StaticText(self, -1, "")
        self.btn_source = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Source Teamworks…"),
            icone="settings",
            variante="ghost",
            tooltip=_(u"Choisir la base Teamworks utilisée en lecture seule"),
            compact=True,
        )

        self.grid = gridlib.Grid(self, -1)
        self.grid.CreateGrid(0, 8)
        self.grid.EnableEditing(False)
        self.grid.EnableDragRowSize(False)
        self.grid.SetRowLabelSize(0)
        self.grid.SetColLabelAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        self.grid.SetSelectionMode(gridlib.Grid.SelectRows)

        self._ConfigureColonnes()
        self._AppliqueApparence()
        self._ConstruitLayout()
        self._Bind()
        self._MAJLibelleSemaine()

        wx.CallAfter(self._AjusteColonnes)

    @staticmethod
    def _GetLundi(date_dd):
        return date_dd - datetime.timedelta(days=date_dd.weekday())

    def _ConfigureColonnes(self):
        self.grid.SetColLabelValue(0, _(u"Salarié"))
        for index in range(7):
            self.grid.SetColLabelValue(index + 1, JOURS_COURTS[index])

    def _AppliqueApparence(self):
        fond = Style.couleur("surface")
        fond_donnees = Style.couleur("surface_container_lowest")
        texte = Style.couleur("on_surface")

        Style.appliquer_texte(
            self.label_semaine,
            role="h4",
            role_texte="on_surface",
            role_fond="surface",
        )
        Style.appliquer_texte(
            self.label_source,
            role="body_small",
            role_texte="on_surface_variant",
            role_fond="surface",
        )

        self.grid.SetDefaultCellFont(Style.police("body"))
        self.grid.SetLabelFont(Style.police("label"))
        self.grid.SetDefaultCellBackgroundColour(fond_donnees)
        self.grid.SetDefaultCellTextColour(texte)
        self.grid.SetGridLineColour(Style.couleur("outline_variant"))
        self.grid.SetSelectionBackground(Style.couleur("selection"))
        self.grid.SetSelectionForeground(Style.couleur("selection_text"))
        self.grid.SetLabelBackgroundColour(Style.couleur("surface_container"))
        self.grid.SetLabelTextColour(texte)
        self.grid.SetBackgroundColour(fond)
        UTILS_Aui.ConfigurerGrille(self.grid)

    def _ConstruitLayout(self):
        petit = Style.espace(1)
        moyen = Style.espace(2)
        grand = Style.espace(3)

        barre = wx.BoxSizer(wx.HORIZONTAL)
        barre.Add(self.btn_precedent, 0, wx.RIGHT, petit)
        barre.Add(self.btn_aujourdhui, 0, wx.RIGHT, petit)
        barre.Add(self.btn_suivant, 0, wx.RIGHT, grand)
        barre.Add(self.label_semaine, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, grand)
        barre.AddStretchSpacer(1)
        barre.Add(self.label_source, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, moyen)
        barre.Add(self.btn_source, 0)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(barre, 0, wx.EXPAND | wx.ALL, moyen)
        sizer.Add(self.grid, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, moyen)
        self.SetSizer(sizer)
        self.Layout()

    def _Bind(self):
        self.Bind(wx.EVT_BUTTON, self.OnPrecedent, self.btn_precedent)
        self.Bind(wx.EVT_BUTTON, self.OnAujourdhui, self.btn_aujourdhui)
        self.Bind(wx.EVT_BUTTON, self.OnSuivant, self.btn_suivant)
        self.Bind(wx.EVT_BUTTON, self.OnSource, self.btn_source)
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def Initialisation(self):
        self.Rafraichir()

    def _MAJLibelleSemaine(self):
        dimanche = self.lundi + datetime.timedelta(days=6)
        if self.lundi.month == dimanche.month:
            texte = _(u"Semaine du %d au %d %s %d") % (
                self.lundi.day,
                dimanche.day,
                self._NomMois(dimanche.month),
                dimanche.year,
            )
        else:
            texte = _(u"Semaine du %d %s au %d %s %d") % (
                self.lundi.day,
                self._NomMois(self.lundi.month),
                dimanche.day,
                self._NomMois(dimanche.month),
                dimanche.year,
            )
        self.label_semaine.SetLabel(texte)
        for index in range(7):
            jour = self.lundi + datetime.timedelta(days=index)
            self.grid.SetColLabelValue(index + 1, u"%s %02d/%02d" % (JOURS_COURTS[index], jour.day, jour.month))
        self.Layout()

    @staticmethod
    def _NomMois(mois):
        noms = (
            u"janvier", u"février", u"mars", u"avril", u"mai", u"juin",
            u"juillet", u"août", u"septembre", u"octobre", u"novembre", u"décembre",
        )
        return noms[mois - 1]

    def OnPrecedent(self, event):
        self.lundi -= datetime.timedelta(days=7)
        self._MAJLibelleSemaine()
        self.Rafraichir()

    def OnAujourdhui(self, event):
        self.lundi = self._GetLundi(datetime.date.today())
        self._MAJLibelleSemaine()
        self.Rafraichir()

    def OnSuivant(self, event):
        self.lundi += datetime.timedelta(days=7)
        self._MAJLibelleSemaine()
        self.Rafraichir()

    def OnSource(self, event):
        dlg = wx.FileDialog(
            self,
            message=_(u"Sélectionnez la base de données Teamworks"),
            wildcard=_(u"Bases Teamworks (*.dat)|*.dat|Tous les fichiers|*.*"),
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        try:
            if dlg.ShowModal() == wx.ID_OK:
                UTILS_Teamworks_Planning.SetCheminBase(dlg.GetPath())
                self.Rafraichir()
        finally:
            dlg.Destroy()

    def OnSize(self, event):
        event.Skip()
        wx.CallAfter(self._AjusteColonnes)

    def _AjusteColonnes(self):
        largeur = self.grid.GetClientSize().GetWidth()
        if largeur <= 0:
            return

        facteur = min(UTILS_Responsive.GetFacteurEcran(), 1.35)
        largeur_nom = max(Style.px(155), int(round(155 * facteur)))
        min_jour = max(Style.px(112), int(round(112 * facteur)))
        marge = Style.espace(7)
        restant = largeur - largeur_nom - marge
        largeur_jour = max(min_jour, restant // 7 if restant > 0 else min_jour)

        self.grid.SetColSize(0, largeur_nom)
        for index in range(1, 8):
            self.grid.SetColSize(index, largeur_jour)

    def Rafraichir(self):
        if self._chargement:
            return
        self._chargement = True
        self.label_source.SetLabel(_(u"Chargement Teamworks…"))
        thread = threading.Thread(target=self._ChargeSemaine, name="Noethys-Planning-Teamworks")
        thread.daemon = True
        thread.start()

    def _ChargeSemaine(self):
        erreur = None
        try:
            lundi, presences = UTILS_Teamworks_Planning.GetSemaine(self.lundi)
        except Exception as exc:
            lundi, presences = self.lundi, []
            erreur = str(exc)
        wx.CallAfter(self._AfficheSemaine, lundi, presences, erreur)

    def _AfficheSemaine(self, lundi, presences, erreur=None):
        self._chargement = False
        self.lundi = lundi
        self._MAJLibelleSemaine()

        if erreur:
            self.label_source.SetLabel(_(u"Teamworks : lecture impossible"))
        elif UTILS_Teamworks_Planning.EstDisponible():
            self.label_source.SetLabel(_(u"Teamworks · lecture seule"))
        else:
            self.label_source.SetLabel(_(u"Teamworks non détecté"))

        personnes = {}
        for presence in presences:
            identifiant = presence.get("IDpersonne")
            nom_complet = u"%s %s" % (presence.get("nom", ""), presence.get("prenom", ""))
            nom_complet = nom_complet.strip() or _(u"Personne %s") % identifiant
            entree = personnes.setdefault(identifiant, {"nom": nom_complet, "jours": {}})
            entree["jours"].setdefault(presence["date"], []).append(presence)

        lignes = sorted(personnes.values(), key=lambda item: item["nom"].casefold())
        self._RedimensionneLignes(len(lignes))

        facteur = min(UTILS_Responsive.GetFacteurEcran(), 1.35)
        hauteur_ligne = max(Style.hauteur_ligne("table"), int(round(27 * facteur)))
        for row, personne in enumerate(lignes):
            self.grid.SetCellValue(row, 0, personne["nom"])
            self.grid.SetCellAlignment(row, 0, wx.ALIGN_LEFT, wx.ALIGN_TOP)
            max_evenements = 1
            for index in range(7):
                jour = lundi + datetime.timedelta(days=index)
                evenements = personne["jours"].get(jour, [])
                max_evenements = max(max_evenements, len(evenements))
                textes = [self._FormatePresence(presence) for presence in evenements]
                self.grid.SetCellValue(row, index + 1, u"\n".join(textes))
                self.grid.SetCellAlignment(row, index + 1, wx.ALIGN_LEFT, wx.ALIGN_TOP)
            hauteur_contenu = max(Style.hauteur_ligne("table"), int(round((18 * max_evenements + 8) * facteur)))
            self.grid.SetRowSize(row, max(hauteur_ligne, hauteur_contenu))

        self._AjusteColonnes()
        self.grid.ForceRefresh()

    def _RedimensionneLignes(self, nombre):
        actuel = self.grid.GetNumberRows()
        if nombre > actuel:
            self.grid.AppendRows(nombre - actuel)
        elif nombre < actuel:
            self.grid.DeleteRows(0, actuel - nombre)

    @staticmethod
    def _FormatePresence(presence):
        debut = presence.get("heure_debut", "")
        fin = presence.get("heure_fin", "")
        horaire = u"%s–%s" % (debut, fin) if debut or fin else ""
        libelle = presence.get("intitule") or presence.get("categorie") or ""
        if presence.get("categorie") and presence.get("intitule"):
            libelle = u"%s · %s" % (presence["categorie"], presence["intitule"])
        if horaire and libelle:
            return u"%s  %s" % (horaire, libelle)
        return horaire or libelle


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        self.ctrl = Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetSize((1350, 650))
        self.CentreOnScreen()
        self.ctrl.Initialisation()


if __name__ == '__main__':
    app = wx.App(0)
    frame = MyFrame(None, -1, _(u"Semaine équipe"))
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
