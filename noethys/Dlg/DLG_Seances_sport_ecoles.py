#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Saisie quotidienne des séances de sport réalisées pour une école."""

from __future__ import unicode_literals

import datetime

import wx

import GestionDB
from Utils.UTILS_Traduction import _
from Utils import UTILS_Interventions
from Utils import UTILS_Tiers_Schema
from Utils import UTILS_Utilisateurs


STATUTS_UI = (
    ("planifiee", _(u"Planifiée")),
    ("realisee", _(u"Réalisée")),
    ("annulee", _(u"Annulée")),
)


def _date_fr(date_iso):
    try:
        return datetime.datetime.strptime(date_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return date_iso or u""


def _duree_humaine(minutes):
    try:
        minutes = int(minutes or 0)
    except Exception:
        minutes = 0
    heures, reste = divmod(minutes, 60)
    if heures and reste:
        return u"%dh%02d" % (heures, reste)
    if heures:
        return u"%dh" % heures
    return u"%d min" % reste


class DialogSeance(wx.Dialog):
    def __init__(self, parent, seance=None):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            title=_(u"Séance de sport"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.seance = dict(seance or {})

        self.label_date = wx.StaticText(self, -1, _(u"Date"))
        self.ctrl_date = wx.TextCtrl(self, -1)
        self.label_debut = wx.StaticText(self, -1, _(u"Heure de début"))
        self.ctrl_debut = wx.TextCtrl(self, -1)
        self.label_fin = wx.StaticText(self, -1, _(u"Heure de fin"))
        self.ctrl_fin = wx.TextCtrl(self, -1)
        self.label_libelle = wx.StaticText(self, -1, _(u"Libellé"))
        self.ctrl_libelle = wx.TextCtrl(self, -1)
        self.label_statut = wx.StaticText(self, -1, _(u"Statut"))
        self.ctrl_statut = wx.Choice(self, -1, choices=[label for code, label in STATUTS_UI])
        self.label_notes = wx.StaticText(self, -1, _(u"Notes"))
        self.ctrl_notes = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE)

        self.bouton_ok = wx.Button(self, wx.ID_OK, _(u"Enregistrer"))
        self.bouton_annuler = wx.Button(self, wx.ID_CANCEL, _(u"Annuler"))
        self.bouton_ok.SetDefault()

        self._initialiser_valeurs()
        self._layout()
        self.Bind(wx.EVT_BUTTON, self.OnOK, self.bouton_ok)

    def _initialiser_valeurs(self):
        self.ctrl_date.SetValue(_date_fr(self.seance.get("date")) or datetime.date.today().strftime("%d/%m/%Y"))
        self.ctrl_debut.SetValue(self.seance.get("heure_debut") or "09:00")
        self.ctrl_fin.SetValue(self.seance.get("heure_fin") or "10:00")
        self.ctrl_libelle.SetValue(self.seance.get("libelle") or _(u"Séance de sport"))
        statut = self.seance.get("statut") or "realisee"
        codes = [code for code, label in STATUTS_UI]
        self.ctrl_statut.SetSelection(codes.index(statut) if statut in codes else 1)
        self.ctrl_notes.SetValue(self.seance.get("notes") or u"")

    def _layout(self):
        grille = wx.FlexGridSizer(rows=6, cols=2, vgap=8, hgap=12)
        grille.Add(self.label_date, 0, wx.ALIGN_CENTER_VERTICAL)
        grille.Add(self.ctrl_date, 1, wx.EXPAND)
        grille.Add(self.label_debut, 0, wx.ALIGN_CENTER_VERTICAL)
        grille.Add(self.ctrl_debut, 1, wx.EXPAND)
        grille.Add(self.label_fin, 0, wx.ALIGN_CENTER_VERTICAL)
        grille.Add(self.ctrl_fin, 1, wx.EXPAND)
        grille.Add(self.label_libelle, 0, wx.ALIGN_CENTER_VERTICAL)
        grille.Add(self.ctrl_libelle, 1, wx.EXPAND)
        grille.Add(self.label_statut, 0, wx.ALIGN_CENTER_VERTICAL)
        grille.Add(self.ctrl_statut, 1, wx.EXPAND)
        grille.Add(self.label_notes, 0, wx.ALIGN_TOP)
        grille.Add(self.ctrl_notes, 1, wx.EXPAND)
        grille.AddGrowableCol(1)
        grille.AddGrowableRow(5)

        boutons = wx.BoxSizer(wx.HORIZONTAL)
        boutons.AddStretchSpacer(1)
        boutons.Add(self.bouton_annuler, 0, wx.RIGHT, 8)
        boutons.Add(self.bouton_ok, 0)

        base = wx.BoxSizer(wx.VERTICAL)
        base.Add(grille, 1, wx.ALL | wx.EXPAND, 16)
        base.Add(boutons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 16)
        self.SetSizer(base)
        self.SetMinSize((500, 390))
        self.SetSize((560, 430))
        self.CenterOnParent()

    def GetDonnees(self):
        index = self.ctrl_statut.GetSelection()
        if index < 0:
            index = 1
        return {
            "date": self.ctrl_date.GetValue(),
            "heure_debut": self.ctrl_debut.GetValue(),
            "heure_fin": self.ctrl_fin.GetValue(),
            "libelle": self.ctrl_libelle.GetValue(),
            "statut": STATUTS_UI[index][0],
            "notes": self.ctrl_notes.GetValue(),
        }

    def OnOK(self, event):
        donnees = self.GetDonnees()
        try:
            UTILS_Interventions._date_iso(donnees["date"])
            UTILS_Interventions.CalculerDureeMinutes(donnees["heure_debut"], donnees["heure_fin"])
        except ValueError as err:
            dlg = wx.MessageDialog(self, str(err), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        self.EndModal(wx.ID_OK)


class Dialog(wx.Dialog):
    def __init__(self, parent, IDecole, nom_ecole=u""):
        wx.Dialog.__init__(
            self,
            parent,
            -1,
            title=_(u"Séances sport — %s") % nom_ecole,
            name="DLG_Seances_sport_ecoles",
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX,
        )
        self.IDecole = int(IDecole)
        self.nom_ecole = nom_ecole
        self.db = GestionDB.DB()
        self.service = UTILS_Interventions.GestionnaireInterventions(self.db)
        self.ecole = None
        self.schema_ok = False
        self.dict_seances = {}

        self.titre = wx.StaticText(self, -1, _(u"École : %s") % nom_ecole)
        font = self.titre.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        font.SetPointSize(max(font.GetPointSize() + 2, 11))
        self.titre.SetFont(font)
        self.sous_titre = wx.StaticText(
            self,
            -1,
            _(u"Enregistrez ici les séances de sport réalisées ou planifiées pour cette école."),
        )

        self.liste = wx.ListCtrl(self, -1, style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SIMPLE)
        self.liste.InsertColumn(0, _(u"Date"), width=95)
        self.liste.InsertColumn(1, _(u"Horaire"), width=125)
        self.liste.InsertColumn(2, _(u"Durée"), width=80)
        self.liste.InsertColumn(3, _(u"Libellé"), width=260)
        self.liste.InsertColumn(4, _(u"Statut"), width=100)

        self.bouton_ajouter = wx.Button(self, -1, _(u"Ajouter une séance"))
        self.bouton_modifier = wx.Button(self, -1, _(u"Modifier"))
        self.bouton_archiver = wx.Button(self, -1, _(u"Archiver"))
        self.bouton_fermer = wx.Button(self, wx.ID_CANCEL, _(u"Fermer"))

        self._layout()
        self.Bind(wx.EVT_BUTTON, self.Ajouter, self.bouton_ajouter)
        self.Bind(wx.EVT_BUTTON, self.Modifier, self.bouton_modifier)
        self.Bind(wx.EVT_BUTTON, self.Archiver, self.bouton_archiver)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.Modifier, self.liste)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self._initialiser_metier()

    def _layout(self):
        entete = wx.BoxSizer(wx.VERTICAL)
        entete.Add(self.titre, 0, wx.BOTTOM, 4)
        entete.Add(self.sous_titre, 0)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_ajouter, 0, wx.RIGHT, 8)
        actions.Add(self.bouton_modifier, 0, wx.RIGHT, 8)
        actions.Add(self.bouton_archiver, 0)
        actions.AddStretchSpacer(1)
        actions.Add(self.bouton_fermer, 0)

        base = wx.BoxSizer(wx.VERTICAL)
        base.Add(entete, 0, wx.ALL | wx.EXPAND, 16)
        base.Add(self.liste, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 16)
        base.Add(actions, 0, wx.ALL | wx.EXPAND, 16)
        self.SetSizer(base)
        self.SetMinSize((760, 500))
        self.SetSize((900, 620))
        self.CenterOnParent()

    def _initialiser_metier(self):
        try:
            resultat = UTILS_Tiers_Schema.AssurerSchema062B(self.db, appliquer=True)
            if not resultat.get("ok"):
                raise RuntimeError(
                    "Schéma tiers/interventions incohérent : %s" % ", ".join(resultat.get("tables_incoherentes", ()))
                )
            self.ecole = self.service.SynchroniserEcoleHistorique(self.IDecole)
            self.nom_ecole = self.ecole.get("nom") or self.nom_ecole
            self.titre.SetLabel(_(u"École : %s") % self.nom_ecole)
            self.SetTitle(_(u"Séances sport — %s") % self.nom_ecole)
            self.schema_ok = True
            self.MAJ()
        except Exception as err:
            self.schema_ok = False
            self.bouton_ajouter.Enable(False)
            self.bouton_modifier.Enable(False)
            self.bouton_archiver.Enable(False)
            dlg = wx.MessageDialog(
                self,
                _(u"Impossible d'activer la saisie des séances de sport.\n\n%s") % str(err),
                _(u"Séances sport"),
                wx.OK | wx.ICON_ERROR,
            )
            dlg.ShowModal()
            dlg.Destroy()

    def _selection_id(self):
        index = self.liste.GetFirstSelected()
        if index == -1:
            return None
        return self.liste.GetItemData(index)

    def _selection_obligatoire(self):
        IDintervention = self._selection_id()
        if IDintervention is None:
            dlg = wx.MessageDialog(
                self,
                _(u"Sélectionnez d'abord une séance."),
                _(u"Séances sport"),
                wx.OK | wx.ICON_INFORMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
        return IDintervention

    def MAJ(self, selection=None):
        if not self.schema_ok or not self.ecole:
            return
        self.liste.DeleteAllItems()
        self.dict_seances = {}
        seances = self.service.ListerSeancesSportEcole(self.ecole["IDstructure"])
        labels_statut = dict(STATUTS_UI)
        selection_index = None
        for ligne, seance in enumerate(seances):
            IDintervention = int(seance["IDintervention"])
            index = self.liste.InsertItem(ligne, _date_fr(seance.get("date")))
            self.liste.SetItem(index, 1, u"%s – %s" % (seance.get("heure_debut") or u"", seance.get("heure_fin") or u""))
            self.liste.SetItem(index, 2, _duree_humaine(seance.get("duree_minutes")))
            self.liste.SetItem(index, 3, seance.get("libelle") or u"")
            self.liste.SetItem(index, 4, labels_statut.get(seance.get("statut"), seance.get("statut") or u""))
            self.liste.SetItemData(index, IDintervention)
            self.dict_seances[IDintervention] = seance
            if selection == IDintervention:
                selection_index = index
        if selection_index is not None:
            self.liste.Select(selection_index)
            self.liste.EnsureVisible(selection_index)

    def Ajouter(self, event):
        if not self.schema_ok:
            return
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_ecoles", "creer") == False:
            return

        donnees_initiales = None
        while True:
            dlg = DialogSeance(self, seance=donnees_initiales)
            reponse = dlg.ShowModal()
            donnees = dlg.GetDonnees() if reponse == wx.ID_OK else None
            dlg.Destroy()
            if reponse != wx.ID_OK:
                return
            try:
                IDintervention = self.service.CreerSeanceSportEcole(
                    self.ecole["IDstructure"],
                    donnees["date"],
                    donnees["heure_debut"],
                    donnees["heure_fin"],
                    libelle=donnees["libelle"],
                    statut=donnees["statut"],
                    notes=donnees["notes"],
                )
            except Exception as err:
                self._afficher_erreur(err)
                donnees_initiales = donnees
                continue
            self.MAJ(selection=IDintervention)
            return

    def Modifier(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_ecoles", "modifier") == False:
            return
        IDintervention = self._selection_obligatoire()
        if IDintervention is None:
            return
        donnees_initiales = self.dict_seances.get(IDintervention) or self.service.LireIntervention(IDintervention)

        while True:
            dlg = DialogSeance(self, seance=donnees_initiales)
            reponse = dlg.ShowModal()
            donnees = dlg.GetDonnees() if reponse == wx.ID_OK else None
            dlg.Destroy()
            if reponse != wx.ID_OK:
                return
            try:
                self.service.ModifierSeanceSport(IDintervention, donnees)
            except Exception as err:
                self._afficher_erreur(err)
                donnees_initiales = donnees
                continue
            self.MAJ(selection=IDintervention)
            return

    def Archiver(self, event):
        if UTILS_Utilisateurs.VerificationDroitsUtilisateurActuel("parametrage_ecoles", "supprimer") == False:
            return
        IDintervention = self._selection_obligatoire()
        if IDintervention is None:
            return
        dlg = wx.MessageDialog(
            self,
            _(u"Archiver cette séance ? Elle ne sera pas supprimée de l'historique."),
            _(u"Séances sport"),
            wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION,
        )
        reponse = dlg.ShowModal()
        dlg.Destroy()
        if reponse != wx.ID_YES:
            return
        try:
            self.service.ArchiverSeanceSport(IDintervention)
            self.MAJ()
        except Exception as err:
            self._afficher_erreur(err)

    def _afficher_erreur(self, err):
        dlg = wx.MessageDialog(self, str(err), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def OnClose(self, event):
        try:
            self.db.Close()
        except Exception:
            pass
        event.Skip()

    def Destroy(self):
        try:
            self.db.Close()
        except Exception:
            pass
        return wx.Dialog.Destroy(self)