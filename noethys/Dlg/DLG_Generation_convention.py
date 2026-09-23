#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Dialogue de génération d'une convention depuis la fiche Famille.

Réutilise les composants existants (CTRL_Choix_modele.CTRL_Choice pour
le choix du modèle, CTRL_Grille_periode.MyDatePickerCtrl pour les
dates) : aucun nouveau composant visuel n'est créé. Aucune saison ni
type de structure n'est rendu obligatoire ici : c'est une saisie
ponctuelle facultative qui préremplit {CONVENTION_SAISON}, laissée
vide si l'utilisateur ne la renseigne pas.

Ce dialogue propose les représentants/signataires et référents
facturation explicitement définis sur les rattachements de l'entité.
Le choix reste corrigeable manuellement et les anciennes bases sans
fonction structurée conservent le repli historique. La date et le lieu
de signature restent des saisies ponctuelles. Ces saisies ne sont
que des overrides de génération transmis à
Utils.UTILS_Convention_champs.GetChampsConvention : rien n'est jamais
enregistré dans les données Noethys (prestations, tarifs,
consommations, individus, familles).

Un bouton "Imprimer le planning" permet, depuis le même écran, de
générer le Planning séparé (moteur Réservations historique, inchangé)
pour la même famille et la même période : Convention et Planning
restent deux fichiers PDF distincts, aucune fusion n'est faite ici.
"""

from __future__ import annotations

import datetime

import wx

from Utils.UTILS_Traduction import _
from Ctrl.CTRL_Choix_modele import CTRL_Choice
from Ctrl.CTRL_Grille_periode import MyDatePickerCtrl


class Dialog(wx.Dialog):
    def __init__(self, parent, IDfamille=None, date_debut=None, date_fin=None, saison=""):
        wx.Dialog.__init__(self, parent, -1, _(u"Générer une convention"),
                            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.IDfamille = IDfamille

        # Valeurs automatiques actuellement affichées (pour savoir si
        # l'utilisateur a corrigé manuellement une valeur préremplie --
        # voir RecalculerValeursAutomatiques ci-dessous).
        self._auto_representant = u""
        self._auto_representant_fonction = u""
        self._representant_selectionne = None
        self._referent_facturation_selectionne = None
        self._representants_disponibles = []
        self._referents_facturation_disponibles = []
        self._auto_tarif = u""
        self._auto_tarif_adulte = u""
        self._auto_tarif_enfant = u""

        # --- Modèle -----------------------------------------------------
        label_modele = wx.StaticText(self, -1, _(u"Modèle de convention :"))
        self.ctrl_modele = CTRL_Choice(self, categorie="convention")

        # --- Période ------------------------------------------------------
        label_periode = wx.StaticText(self, -1, _(u"Période concernée :"))
        self.ctrl_date_debut = MyDatePickerCtrl(self)
        self.ctrl_date_fin = MyDatePickerCtrl(self)
        aujourdhui = datetime.date.today()
        periode_auto = (None, None)
        if self.IDfamille is not None and (date_debut is None or date_fin is None):
            try:
                from Utils import UTILS_Convention_champs as CC
                periode_auto = CC.GetPeriodeParDefaut(self.IDfamille, date_reference=aujourdhui)
            except Exception:
                periode_auto = (None, None)
        debut_initial = date_debut or periode_auto[0] or aujourdhui
        fin_initiale = date_fin or periode_auto[1] or debut_initial
        self.ctrl_date_debut.SetDate(debut_initial)
        self.ctrl_date_fin.SetDate(fin_initiale)
        self.label_periode_info = wx.StaticText(self, -1, u"")
        if periode_auto[0] is not None and periode_auto[1] is not None:
            self.label_periode_info.SetLabel(_(u"Période préremplie depuis les séances enregistrées."))
        elif date_debut is None and date_fin is None:
            self.label_periode_info.SetLabel(_(u"Aucune séance trouvée : vérifiez la période manuellement."))
            self.label_periode_info.SetForegroundColour(wx.Colour(180, 70, 0))
        label_saison = wx.StaticText(self, -1, _(u"Saison (facultatif, ex. 2026-2027) :"))
        saison_initiale = saison
        if not saison_initiale and periode_auto[0] is not None and periode_auto[1] is not None:
            try:
                from Utils import UTILS_Convention_champs as CC
                saison_initiale = CC.SaisonDepuisPeriode(periode_auto[0], periode_auto[1])
            except Exception:
                saison_initiale = u""
        self.ctrl_saison = wx.TextCtrl(self, -1, saison_initiale)

        # --- Représentant / signataire --------------------------------
        label_representant_choix = wx.StaticText(self, -1, _(u"Représentant / signataire :"))
        self.ctrl_representant_choix = wx.Choice(self, -1)

        label_representant = wx.StaticText(self, -1, _(u"Nom retenu :"))
        self.ctrl_representant_nom_complet = wx.TextCtrl(self, -1, u"")
        self.ctrl_representant_nom_complet.SetToolTip(wx.ToolTip(
            _(u"Prérempli depuis le contact choisi. La saisie reste modifiable pour un cas exceptionnel.")))

        label_fonction = wx.StaticText(self, -1, _(u"Fonction :"))
        self.ctrl_representant_fonction = wx.TextCtrl(self, -1, u"")

        # --- Référent facturation --------------------------------------
        label_facturation = wx.StaticText(self, -1, _(u"Référent facturation :"))
        self.ctrl_facturation_choix = wx.Choice(self, -1)
        self.ctrl_facturation_choix.SetToolTip(wx.ToolTip(
            _(u"Choisissez un référent facturation enregistré sur l'entité. "
              u"Le contact par défaut reste sélectionné automatiquement si vous ne changez rien.")))

        self.ChargerContactsDisponibles()

        # --- Signature ------------------------------------------------
        label_date_signature = wx.StaticText(self, -1, _(u"Date et lieu de signature :"))
        self.ctrl_date_signature = MyDatePickerCtrl(self)
        self.ctrl_date_signature.SetDate(aujourdhui)

        self.ctrl_lieu_signature = wx.TextCtrl(self, -1, u"")
        self.ctrl_lieu_signature.SetToolTip(wx.ToolTip(_(u"Lieu de signature (ex. LANNILIS)")))

        # --- Tarifs ------------------------------------------------------
        label_tarifs = wx.StaticText(self, -1, _(u"Tarifs horaires détectés (€) :"))
        self.ctrl_tarif_horaire = wx.TextCtrl(self, -1, u"")
        self.ctrl_tarif_adulte = wx.TextCtrl(self, -1, u"")
        self.ctrl_tarif_enfant = wx.TextCtrl(self, -1, u"")
        self.label_tarif_horaire_provenance = wx.StaticText(self, -1, u"", size=(390, -1))
        self.label_tarif_adulte_provenance = wx.StaticText(self, -1, u"", size=(390, -1))
        self.label_tarif_enfant_provenance = wx.StaticText(self, -1, u"", size=(390, -1))
        sizer_tarifs = wx.FlexGridSizer(rows=3, cols=3, vgap=5, hgap=8)
        for libelle, ctrl, provenance in (
            (_(u"Unique :"), self.ctrl_tarif_horaire, self.label_tarif_horaire_provenance),
            (_(u"Adultes :"), self.ctrl_tarif_adulte, self.label_tarif_adulte_provenance),
            (_(u"Enfants :"), self.ctrl_tarif_enfant, self.label_tarif_enfant_provenance),
        ):
            sizer_tarifs.Add(wx.StaticText(self, -1, libelle), 0, wx.ALIGN_CENTER_VERTICAL)
            sizer_tarifs.Add(ctrl, 0, wx.EXPAND)
            sizer_tarifs.Add(provenance, 1, wx.ALIGN_CENTER_VERTICAL | wx.EXPAND)
        sizer_tarifs.AddGrowableCol(2)
        self.ctrl_tarif_horaire.SetToolTip(wx.ToolTip(_(u"Utilisé seulement quand un taux unique est démontré sur la période.")))
        self.ctrl_tarif_adulte.SetToolTip(wx.ToolTip(_(u"Prérempli quand les données démontrent un taux adulte stable.")))
        self.ctrl_tarif_enfant.SetToolTip(wx.ToolTip(_(u"Prérempli quand les données démontrent un taux enfant stable.")))

        # --- Boutons ------------------------------------------------------
        self.bouton_planning = wx.Button(self, -1, _(u"Imprimer le planning"))
        self.bouton_planning.SetToolTip(wx.ToolTip(
            _(u"Génère, pour la même famille et la même période, le Planning séparé (document distinct de la Convention).")))
        bouton_ok = wx.Button(self, wx.ID_OK, _(u"Générer la convention"))
        bouton_ok.SetDefault()
        bouton_annuler = wx.Button(self, wx.ID_CANCEL, _(u"Annuler"))

        self.Bind(wx.EVT_BUTTON, self.OnBoutonPlanning, self.bouton_planning)
        self.Bind(wx.EVT_CHOICE, self.OnChoixRepresentant, self.ctrl_representant_choix)
        self.Bind(wx.EVT_CHOICE, self.OnChoixReferentFacturation, self.ctrl_facturation_choix)

        # --- Mise en page ------------------------------------------------
        sizer_periode_ligne = wx.BoxSizer(wx.HORIZONTAL)
        sizer_periode_ligne.Add(self.ctrl_date_debut, 0, wx.RIGHT, 5)
        sizer_periode_ligne.Add(wx.StaticText(self, -1, _(u"au")), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 5)
        sizer_periode_ligne.Add(self.ctrl_date_fin, 0)
        sizer_periode = wx.BoxSizer(wx.VERTICAL)
        sizer_periode.Add(sizer_periode_ligne, 0)
        sizer_periode.Add(self.label_periode_info, 0, wx.TOP, 4)

        sizer_signature = wx.BoxSizer(wx.HORIZONTAL)
        sizer_signature.Add(self.ctrl_date_signature, 0, wx.RIGHT, 10)
        sizer_signature.Add(self.ctrl_lieu_signature, 1, wx.EXPAND)

        sizer_boutons = wx.StdDialogButtonSizer()
        sizer_boutons.AddButton(bouton_ok)
        sizer_boutons.AddButton(bouton_annuler)
        sizer_boutons.Realize()

        sizer_bas = wx.BoxSizer(wx.HORIZONTAL)
        sizer_bas.Add(self.bouton_planning, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer_bas.AddStretchSpacer()
        sizer_bas.Add(sizer_boutons, 0)

        sizer_general = wx.BoxSizer(wx.VERTICAL)
        for label, ctrl in (
            (label_modele, self.ctrl_modele),
            (label_periode, sizer_periode),
            (label_saison, self.ctrl_saison),
            (label_representant_choix, self.ctrl_representant_choix),
            (label_representant, self.ctrl_representant_nom_complet),
            (label_fonction, self.ctrl_representant_fonction),
            (label_facturation, self.ctrl_facturation_choix),
            (label_date_signature, sizer_signature),
            (label_tarifs, sizer_tarifs),
        ):
            sizer_general.Add(label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 10)
            if isinstance(ctrl, wx.Sizer):
                sizer_general.Add(ctrl, 0, wx.ALL | wx.EXPAND, 10)
            else:
                sizer_general.Add(ctrl, 0, wx.ALL | wx.EXPAND, 10)
        sizer_general.Add(sizer_bas, 0, wx.ALL | wx.EXPAND, 10)

        self.SetSizer(sizer_general)
        sizer_general.Fit(self)
        self.CentreOnParent()

        # Préremplissage initial des valeurs automatiques (représentant,
        # tarif) pour la période sélectionnée par défaut.
        self.RecalculerValeursAutomatiques()

    # ------------------------------------------------------------------
    # Contacts de l'entité
    # ------------------------------------------------------------------

    @staticmethod
    def _LabelContact(contact):
        nom = contact.get("nom_complet") or u""
        fonction = contact.get("fonction") or u""
        if fonction:
            return u"%s — %s" % (nom, fonction)
        return nom

    def ChargerContactsDisponibles(self):
        """Charge les menus sans créer/modifier aucune donnée."""
        self._representants_disponibles = []
        self._referents_facturation_disponibles = []
        if self.IDfamille is not None:
            try:
                from Utils import UTILS_Convention_champs as CC
                self._representants_disponibles = CC.GetRepresentantsDisponibles(self.IDfamille)
                self._referents_facturation_disponibles = CC.GetReferentsFacturationDisponibles(self.IDfamille)
            except Exception:
                # Une base ancienne sans métadonnées de fonction doit
                # continuer à fonctionner exactement comme avant.
                self._representants_disponibles = []
                self._referents_facturation_disponibles = []

        self.ctrl_representant_choix.SetItems(
            [_(u"Automatique / saisie manuelle")] +
            [self._LabelContact(c) for c in self._representants_disponibles]
        )
        if self._representants_disponibles:
            # La liste est déjà triée avec le contact marqué "défaut"
            # en premier. On montre donc immédiatement le choix réel à
            # l'utilisateur plutôt qu'un libellé abstrait "automatique".
            self.ctrl_representant_choix.SetSelection(1)
            self._representant_selectionne = self._representants_disponibles[0]
            self.ctrl_representant_nom_complet.SetValue(
                self._representant_selectionne.get("nom_complet") or u""
            )
            self.ctrl_representant_fonction.SetValue(
                self._representant_selectionne.get("fonction") or u""
            )
        else:
            self.ctrl_representant_choix.SetSelection(0)

        self.ctrl_facturation_choix.SetItems(
            [_(u"Automatique (référent par défaut)")] +
            [self._LabelContact(c) for c in self._referents_facturation_disponibles]
        )
        if self._referents_facturation_disponibles:
            self.ctrl_facturation_choix.SetSelection(1)
            self._referent_facturation_selectionne = self._referents_facturation_disponibles[0]
        else:
            self.ctrl_facturation_choix.SetSelection(0)

    def OnChoixRepresentant(self, event=None):
        index = self.ctrl_representant_choix.GetSelection()
        if index <= 0:
            self._representant_selectionne = None
            self.ctrl_representant_nom_complet.SetValue(u"")
            self.ctrl_representant_fonction.SetValue(u"")
            self.RecalculerValeursAutomatiques()
            return

        contact = self._representants_disponibles[index - 1]
        self._representant_selectionne = contact
        self.ctrl_representant_nom_complet.SetValue(contact.get("nom_complet") or u"")
        self.ctrl_representant_fonction.SetValue(contact.get("fonction") or u"")

    def OnChoixReferentFacturation(self, event=None):
        index = self.ctrl_facturation_choix.GetSelection()
        if index <= 0:
            self._referent_facturation_selectionne = None
            return
        self._referent_facturation_selectionne = self._referents_facturation_disponibles[index - 1]

    # ------------------------------------------------------------------
    # Rafraîchissement des valeurs automatiques (représentant, tarif)
    # ------------------------------------------------------------------

    def OnSelection(self):
        """ Appelée par CTRL_Grille_periode.MyDatePickerCtrl.OnDateChanged
        lorsque l'utilisateur change une date : les dates de début/fin
        étant des enfants directs de ce dialogue, elles utilisent son
        parent (donc self) comme cible de rappel. Un changement de
        période peut changer le tarif horaire détectable (le
        représentant, lui, ne dépend pas de la période). """
        self.RecalculerValeursAutomatiques()

    def RecalculerValeursAutomatiques(self):
        """ Recalcule le représentant et le tarif horaire automatiques
        pour la période actuellement sélectionnée, et met à jour les
        champs correspondants -- SAUF si l'utilisateur les a déjà
        corrigés manuellement (la valeur affichée ne correspond plus à
        la dernière valeur automatique connue). Ne modifie jamais aucune
        donnée Noethys : lecture seule. """
        if self.IDfamille is None:
            return
        try:
            from Utils import UTILS_Convention_champs as CC
            champs, _donnees = CC.GetChampsConvention(
                IDfamille=self.IDfamille,
                date_debut=str(self.ctrl_date_debut.GetDate()),
                date_fin=str(self.ctrl_date_fin.GetDate()),
            )
        except Exception:
            # Lecture seule, best-effort : une erreur ici ne doit jamais
            # empêcher l'utilisateur de continuer à saisir manuellement.
            return

        nouveau_representant = champs.get("{CONVENTION_REPRESENTANT_NOM_COMPLET}") or u""
        nouvelle_fonction = champs.get("{CONVENTION_REPRESENTANT_FONCTION}") or u""
        if self._representant_selectionne is None:
            valeurActuelle = self.ctrl_representant_nom_complet.GetValue().strip()
            if valeurActuelle in (u"", self._auto_representant):
                self.ctrl_representant_nom_complet.SetValue(nouveau_representant)

            fonctionActuelle = self.ctrl_representant_fonction.GetValue().strip()
            if fonctionActuelle in (u"", self._auto_representant_fonction):
                self.ctrl_representant_fonction.SetValue(nouvelle_fonction)

        self._auto_representant = nouveau_representant
        self._auto_representant_fonction = nouvelle_fonction

        def MajTarif(ctrl, attribut, code):
            tarif = champs.get(code)
            nouveau = (u"%.2f" % tarif) if isinstance(tarif, (int, float)) else u""
            valeurActuelle = ctrl.GetValue().strip()
            precedente = getattr(self, attribut)
            if valeurActuelle in (u"", precedente):
                ctrl.SetValue(nouveau)
            setattr(self, attribut, nouveau)
        MajTarif(self.ctrl_tarif_horaire, "_auto_tarif", "{CONVENTION_TARIF_HORAIRE}")
        MajTarif(self.ctrl_tarif_adulte, "_auto_tarif_adulte", "{CONVENTION_TARIF_ADULTE}")
        MajTarif(self.ctrl_tarif_enfant, "_auto_tarif_enfant", "{CONVENTION_TARIF_ENFANT}")
        for label, code in (
            (self.label_tarif_horaire_provenance, "{CONVENTION_TARIF_HORAIRE_PROVENANCE}"),
            (self.label_tarif_adulte_provenance, "{CONVENTION_TARIF_ADULTE_PROVENANCE}"),
            (self.label_tarif_enfant_provenance, "{CONVENTION_TARIF_ENFANT_PROVENANCE}"),
        ):
            label.SetLabel(champs.get(code) or u"")
            label.Wrap(390)

    # ------------------------------------------------------------------
    # Planning séparé (moteur Réservations historique, inchangé)
    # ------------------------------------------------------------------

    def OnBoutonPlanning(self, event):
        """ Génère le Planning séparé pour la même famille et la même
        période que la Convention en cours de préparation. Ne ferme pas
        le dialogue : l'utilisateur peut ensuite toujours générer la
        Convention. Deux documents PDF distincts, aucune fusion. """
        if self.IDfamille is None:
            return
        from Utils import UTILS_Convention_champs as CC
        from Utils import UTILS_Impression_reservations as RESA

        date_debut = str(self.ctrl_date_debut.GetDate())
        date_fin = str(self.ctrl_date_fin.GetDate())
        try:
            listeIDindividus = CC.GetIndividusRattaches(self.IDfamille)
            dictDonnees = RESA.GetDonnees(
                listeIDindividus=listeIDindividus, date_debut=date_debut, date_fin=date_fin,
            )
            if not dictDonnees:
                dlg = wx.MessageDialog(
                    self, _(u"Aucune donnée de planning trouvée pour cette période."),
                    _(u"Planning"), wx.OK | wx.ICON_INFORMATION,
                )
                dlg.ShowModal()
                dlg.Destroy()
                return
            RESA.Impression(dictDonnees)
        except Exception as err:
            dlg = wx.MessageDialog(
                self, _(u"Impossible de générer le planning.\n\n%s") % err,
                _(u"Planning"), wx.OK | wx.ICON_ERROR,
            )
            dlg.ShowModal()
            dlg.Destroy()

    # ------------------------------------------------------------------
    # Accesseurs
    # ------------------------------------------------------------------

    def GetIDmodele(self):
        return self.ctrl_modele.GetID()

    def GetDateDebut(self):
        return self.ctrl_date_debut.GetDate()

    def GetDateFin(self):
        return self.ctrl_date_fin.GetDate()

    def GetSaison(self):
        return self.ctrl_saison.GetValue().strip() or None

    def GetOverrides(self):
        """ Dict {"{CODE}": valeur} à transmettre tel quel à
        UTILS_Impression_convention.Impression(overrides=...). Reflète
        exactement ce qui est affiché dans le dialogue (valeur
        automatique non touchée, ou correction manuelle de
        l'utilisateur) : jamais écrit dans Noethys, seulement utilisé
        pour la génération de ce PDF. """
        overrides = {
            "{CONVENTION_REPRESENTANT_NOM_COMPLET}": self.ctrl_representant_nom_complet.GetValue().strip(),
            "{CONVENTION_REPRESENTANT_FONCTION}": self.ctrl_representant_fonction.GetValue().strip(),
            "{CONVENTION_DATE_SIGNATURE}": self.ctrl_date_signature.GetDate().strftime("%d/%m/%Y"),
            "{CONVENTION_LIEU_SIGNATURE}": self.ctrl_lieu_signature.GetValue().strip(),
        }
        if self._referent_facturation_selectionne is not None:
            contact = self._referent_facturation_selectionne
            overrides.update({
                "{CONVENTION_REFERENT_FACTURATION_NOM}": contact.get("nom") or u"",
                "{CONVENTION_REFERENT_FACTURATION_PRENOM}": contact.get("prenom") or u"",
                "{CONVENTION_REFERENT_FACTURATION_NOM_COMPLET}": contact.get("nom_complet") or u"",
                "{CONVENTION_REFERENT_FACTURATION_FONCTION}": contact.get("fonction") or u"",
                "{CONVENTION_REFERENT_FACTURATION_EMAIL}": contact.get("mail") or u"",
                "{CONVENTION_REFERENT_FACTURATION_TELEPHONE}": contact.get("telephone") or u"",
            })

        for code, ctrl in (
            ("{CONVENTION_TARIF_HORAIRE}", self.ctrl_tarif_horaire),
            ("{CONVENTION_TARIF_ADULTE}", self.ctrl_tarif_adulte),
            ("{CONVENTION_TARIF_ENFANT}", self.ctrl_tarif_enfant),
        ):
            tarif_saisi = ctrl.GetValue().strip().replace(",", ".")
            if tarif_saisi:
                try:
                    overrides[code] = float(tarif_saisi)
                except ValueError:
                    pass
        return overrides