#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import wx

import Chemins
from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Bouton_image
from Utils import UTILS_Config
from Utils.UTILS_Traduction import _
from Utils.UTILS_PMSL_Sync import run_sync
from Utils.UTILS_PMSL_ReturnSync import push_reference


class Dialog(wx.Dialog):
    """Synchronisation manuelle PMSL Équipe <-> Noethys.

    Le secret partagé reste volontairement en mémoire uniquement. Une simulation
    réussie dans cette fenêtre est requise avant d'activer le bouton Appliquer.
    """

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, name="DLG_PMSL_Synchronisation",
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER |
                                 wx.MAXIMIZE_BOX | wx.MINIMIZE_BOX)
        self.parent = parent
        self.preview_ok = False
        self.retry_pending = False

        titre = _(u"Synchronisation PMSL Équipe")
        intro = _(u"Échange direct avec PMSL Équipe. Le test récupère les lots et simule les ouvertures sans modifier Noethys. L'application n'est proposée qu'après une simulation valide et renvoie ensuite les accusés à PMSL.")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(
            self, titre=titre, texte=intro, hauteurHtml=42,
            nomImage="Images/32x32/Calendrier.png")

        self.box_connexion = wx.StaticBox(self, -1, _(u"Passerelle PMSL"))
        self.label_url = wx.StaticText(self, -1, _(u"URL PMSL :"))
        self.ctrl_url = wx.TextCtrl(self, -1, u"")
        self.label_instance = wx.StaticText(self, -1, _(u"Instance Noethys :"))
        self.ctrl_instance = wx.TextCtrl(self, -1, u"")
        self.label_secret = wx.StaticText(self, -1, _(u"Secret partagé :"))
        self.ctrl_secret = wx.TextCtrl(self, -1, u"", style=wx.TE_PASSWORD)
        self.label_limit = wx.StaticText(self, -1, _(u"Lots maximum :"))
        self.ctrl_limit = wx.SpinCtrl(self, -1, min=1, max=100, initial=20)
        self.label_date_start = wx.StaticText(self, -1, _(u"Référentiel du :"))
        self.ctrl_date_start = wx.TextCtrl(self, -1, u"")
        self.label_date_end = wx.StaticText(self, -1, _(u"au :"))
        self.ctrl_date_end = wx.TextCtrl(self, -1, u"")
        self.info_secret = wx.StaticText(self, -1, _(u"Le secret n'est pas enregistré sur le poste."))

        self.box_resultat = wx.StaticBox(self, -1, _(u"Résultat"))
        self.ctrl_resultat = wx.TextCtrl(self, -1, u"", style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)

        self.bouton_tester = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Tester la synchronisation"),
            cheminImage="Images/32x32/Actualiser.png")
        self.bouton_appliquer = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Appliquer"), cheminImage="Images/32x32/Valider.png")
        self.bouton_envoyer = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Envoyer le référentiel vers PMSL"), cheminImage="Images/32x32/Export.png")
        self.bouton_fermer = CTRL_Bouton_image.CTRL(
            self, texte=_(u"Fermer"), cheminImage="Images/32x32/Fermer.png")

        self._set_properties()
        self._do_layout()
        self._load_config()

        self.Bind(wx.EVT_BUTTON, self.OnTester, self.bouton_tester)
        self.Bind(wx.EVT_BUTTON, self.OnAppliquer, self.bouton_appliquer)
        self.Bind(wx.EVT_BUTTON, self.OnEnvoyerReferentiel, self.bouton_envoyer)
        self.Bind(wx.EVT_BUTTON, self.OnFermer, self.bouton_fermer)
        self.Bind(wx.EVT_TEXT, self.OnConfigurationChange, self.ctrl_url)
        self.Bind(wx.EVT_TEXT, self.OnConfigurationChange, self.ctrl_instance)
        self.Bind(wx.EVT_TEXT, self.OnConfigurationChange, self.ctrl_secret)
        self.Bind(wx.EVT_SPINCTRL, self.OnConfigurationChange, self.ctrl_limit)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def _set_properties(self):
        self.ctrl_url.SetToolTip(wx.ToolTip(_(u"Adresse du site WordPress qui héberge PMSL Équipe, par exemple https://planning.exemple.fr")))
        self.ctrl_instance.SetToolTip(wx.ToolTip(_(u"Identifiant de cette instance Noethys, identique à celui déclaré dans PMSL Équipe.")))
        self.ctrl_secret.SetToolTip(wx.ToolTip(_(u"Secret HMAC partagé configuré dans la passerelle PMSL intégrée.")))
        self.bouton_tester.SetToolTip(wx.ToolTip(_(u"Récupère les lots PMSL et simule leur application sans écriture.")))
        self.bouton_appliquer.SetToolTip(wx.ToolTip(_(u"Crée les ouvertures manquantes après confirmation et renvoie les accusés PMSL.")))
        self.info_secret.SetForegroundColour(wx.Colour(120, 120, 120))
        self.bouton_appliquer.Enable(False)
        self.SetMinSize((760, 620))

    def _do_layout(self):
        base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)

        box_connexion = wx.StaticBoxSizer(self.box_connexion, wx.VERTICAL)
        grid = wx.FlexGridSizer(rows=7, cols=2, vgap=8, hgap=10)
        grid.Add(self.label_url, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.ctrl_url, 1, wx.EXPAND)
        grid.Add(self.label_instance, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.ctrl_instance, 1, wx.EXPAND)
        grid.Add(self.label_secret, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.ctrl_secret, 1, wx.EXPAND)
        grid.Add((1, 1))
        grid.Add(self.info_secret, 0, wx.EXPAND)
        grid.Add(self.label_limit, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.ctrl_limit, 0)
        grid.Add(self.label_date_start, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.ctrl_date_start, 1, wx.EXPAND)
        grid.Add(self.label_date_end, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.ctrl_date_end, 1, wx.EXPAND)
        grid.AddGrowableCol(1)
        box_connexion.Add(grid, 1, wx.ALL | wx.EXPAND, 10)
        base.Add(box_connexion, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        box_resultat = wx.StaticBoxSizer(self.box_resultat, wx.VERTICAL)
        box_resultat.Add(self.ctrl_resultat, 1, wx.ALL | wx.EXPAND, 8)
        base.Add(box_resultat, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        boutons = wx.BoxSizer(wx.HORIZONTAL)
        boutons.Add(self.bouton_tester, 0)
        boutons.Add(self.bouton_appliquer, 0, wx.LEFT, 10)
        boutons.Add(self.bouton_envoyer, 0, wx.LEFT, 10)
        boutons.AddStretchSpacer()
        boutons.Add(self.bouton_fermer, 0)
        base.Add(boutons, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        base.AddGrowableRow(2)
        base.AddGrowableCol(0)
        self.SetSizer(base)
        base.Fit(self)
        self.Layout()
        self.CenterOnScreen()

    def _load_config(self):
        values = UTILS_Config.GetParametres({
            "pmsl_bridge_url": u"",
            "pmsl_bridge_source_instance": u"noethys-sport",
            "pmsl_bridge_limit": 20,
            "pmsl_export_date_start": u"",
            "pmsl_export_date_end": u"",
        })
        self.ctrl_url.SetValue(values.get("pmsl_bridge_url") or u"")
        self.ctrl_instance.SetValue(values.get("pmsl_bridge_source_instance") or u"noethys-sport")
        try:
            self.ctrl_limit.SetValue(int(values.get("pmsl_bridge_limit") or 20))
        except (TypeError, ValueError):
            self.ctrl_limit.SetValue(20)
        self.ctrl_date_start.SetValue(values.get("pmsl_export_date_start") or u"")
        self.ctrl_date_end.SetValue(values.get("pmsl_export_date_end") or u"")

    def _save_config(self):
        # Le secret n'est jamais persisté.
        UTILS_Config.SetParametres({
            "pmsl_bridge_url": self.ctrl_url.GetValue().strip(),
            "pmsl_bridge_source_instance": self.ctrl_instance.GetValue().strip(),
            "pmsl_bridge_limit": int(self.ctrl_limit.GetValue()),
            "pmsl_export_date_start": self.ctrl_date_start.GetValue().strip(),
            "pmsl_export_date_end": self.ctrl_date_end.GetValue().strip(),
        })

    def _parameters(self):
        url = self.ctrl_url.GetValue().strip()
        instance = self.ctrl_instance.GetValue().strip()
        secret = self.ctrl_secret.GetValue()
        if not url:
            raise ValueError(_(u"L'URL PMSL est obligatoire."))
        if not instance:
            raise ValueError(_(u"L'identifiant de l'instance Noethys est obligatoire."))
        if len(secret) < 24:
            raise ValueError(_(u"Le secret partagé doit contenir au moins 24 caractères."))
        return url, secret, instance, int(self.ctrl_limit.GetValue())

    def _reset_apply_state(self):
        self.preview_ok = False
        self.retry_pending = False
        self.bouton_appliquer.SetTexte(_(u"Appliquer"))
        self.bouton_appliquer.Enable(False)

    def OnConfigurationChange(self, event=None):
        self._reset_apply_state()
        if event is not None:
            event.Skip()

    def OnTester(self, event=None):
        self.retry_pending = False
        self.bouton_appliquer.SetTexte(_(u"Appliquer"))
        self._run(False)

    def OnEnvoyerReferentiel(self, event=None):
        busy = None
        try:
            url, secret, instance, limit = self._parameters()
            date_start = self.ctrl_date_start.GetValue().strip() or None
            date_end = self.ctrl_date_end.GetValue().strip() or None
            self._save_config()
            busy = wx.BusyInfo(_(u"Envoi du référentiel Noethys vers PMSL..."), self)
            if 'phoenix' in wx.PlatformInfo:
                wx.SafeYield(self, True)
            else:
                wx.Yield()
            result = push_reference(url, secret, instance, date_start=date_start, date_end=date_end)
        except Exception as err:
            if busy is not None:
                del busy
            self._message(_(u"Échec de l'envoi du référentiel vers PMSL.\n\n%s") % err, wx.ICON_ERROR)
            return
        if busy is not None:
            del busy
        response = result.get("response") or {}
        counts = result.get("counts") or {}
        lines = [
            _(u"Référentiel Noethys envoyé vers PMSL."),
            _(u"Activités : %d | Unités : %d | Groupes : %d | Ouvertures : %d") % (int(counts.get("activities") or 0), int(counts.get("units") or 0), int(counts.get("groups") or 0), int(counts.get("openings") or 0)),
            _(u"Lot PMSL : %s") % (response.get("batch_uuid") or u"—"),
            _(u"Lignes PMSL : %d") % int(response.get("line_count") or 0),
            _(u"Déjà reçu : %s") % (u"oui" if response.get("already_registered") else u"non"),
            _(u"Statut : prévisualisation - validation humaine obligatoire."),
        ]
        self.ctrl_resultat.SetValue(u"\n".join(lines))
        self._message(_(u"Le référentiel a été placé en prévisualisation dans PMSL. Aucune donnée PMSL n'a été appliquée automatiquement."), wx.ICON_INFORMATION)

    def OnAppliquer(self, event=None):
        if not self.preview_ok:
            self._message(_(u"Relancez d'abord une simulation valide avec la configuration actuelle."), wx.ICON_EXCLAMATION)
            return
        if self.retry_pending:
            message = _(u"Des ouvertures ont déjà été appliquées dans Noethys, mais PMSL n'a pas reçu tous les accusés.\n\nLa reprise est idempotente : les ouvertures existantes ne seront pas dupliquées et les accusés seront renvoyés.\n\nRéessayer ?")
            titre = _(u"Réessayer les accusés PMSL")
        else:
            message = _(u"Cette opération va créer dans Noethys les ouvertures manquantes des lots PMSL valides, puis envoyer les accusés de traitement à PMSL.\n\nContinuer ?")
            titre = _(u"Appliquer la synchronisation PMSL")
        dlg = wx.MessageDialog(self, message, titre, wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
        answer = dlg.ShowModal()
        dlg.Destroy()
        if answer == wx.ID_YES:
            self._run(True)

    def _run(self, apply):
        try:
            url, secret, instance, limit = self._parameters()
        except Exception as err:
            self._message(str(err), wx.ICON_EXCLAMATION)
            return
        self._save_config()
        busy = wx.BusyInfo(
            _(u"Application des lots PMSL dans Noethys...") if apply else _(u"Simulation de la synchronisation PMSL..."),
            self)
        try:
            if 'phoenix' in wx.PlatformInfo:
                wx.SafeYield(self, True)
            else:
                wx.Yield()
            result = run_sync(url, secret, instance, apply=apply, limit=limit)
        except Exception as err:
            del busy
            self._reset_apply_state()
            self.ctrl_resultat.SetValue(_(u"Échec de la synchronisation :\n%s") % err)
            self._message(_(u"La synchronisation PMSL a échoué.\n\n%s") % err, wx.ICON_ERROR)
            return
        del busy
        self.ctrl_resultat.SetValue(self._format_result(result))
        if apply:
            if result.get("synchronisation_complete"):
                self._reset_apply_state()
                self._message(_(u"Traitement terminé. Tous les lots appliqués ont été accusés auprès de PMSL."), wx.ICON_INFORMATION)
            else:
                # Les écritures locales peuvent déjà être committées. On maintient
                # donc une action de reprise idempotente au lieu de masquer l'échec.
                self.preview_ok = True
                self.retry_pending = True
                self.bouton_appliquer.SetTexte(_(u"Réessayer les accusés"))
                self.bouton_appliquer.Enable(True)
                self._message(_(u"Les ouvertures Noethys ont été traitées, mais au moins un accusé n'a pas atteint PMSL.\n\nVous pouvez utiliser « Réessayer les accusés ». Les ouvertures existantes ne seront pas recréées."), wx.ICON_EXCLAMATION)
        else:
            self.preview_ok = self._is_preview_valid(result)
            self.retry_pending = False
            self.bouton_appliquer.SetTexte(_(u"Appliquer"))
            self.bouton_appliquer.Enable(self.preview_ok and result.get("batch_count", 0) > 0)
            if result.get("batch_count", 0) == 0:
                self._message(_(u"Aucun lot PMSL en attente pour cette instance Noethys."), wx.ICON_INFORMATION)
            elif self.preview_ok:
                self._message(_(u"Simulation valide. Vous pouvez maintenant choisir Appliquer."), wx.ICON_INFORMATION)
            else:
                self._message(_(u"La simulation contient au moins un lot bloqué. Aucune écriture n'a été effectuée."), wx.ICON_EXCLAMATION)

    @staticmethod
    def _is_preview_valid(result):
        for item in result.get("results") or []:
            if not (item.get("preview") or {}).get("valid"):
                return False
        return True

    @staticmethod
    def _format_result(result):
        lines = []
        mode = result.get("mode") or "preview"
        lines.append(u"Mode : %s" % (u"APPLICATION" if mode == "apply" else u"SIMULATION"))
        lines.append(u"Instance : %s" % (result.get("source_instance") or u"—"))
        lines.append(u"Lots : %d" % int(result.get("batch_count") or 0))
        if mode == "apply":
            lines.append(u"Synchronisation complète : %s" % (u"oui" if result.get("synchronisation_complete") else u"NON"))
        lines.append(u"")
        for index, item in enumerate(result.get("results") or [], 1):
            preview = item.get("preview") or {}
            counts = preview.get("counts") or {}
            uuid = item.get("batch_uuid") or u"—"
            lines.append(u"%d. Lot %s" % (index, uuid))
            lines.append(u"   Simulation : %s" % (u"valide" if preview.get("valid") else u"BLOQUÉE"))
            lines.append(u"   À créer : %d | Déjà présentes : %d | Bloquées : %d" % (
                int(counts.get("create") or 0), int(counts.get("unchanged") or 0), int(counts.get("blocked") or 0)))
            if item.get("applied"):
                lines.append(u"   Application locale : effectuée")
                lines.append(u"   ACK PMSL : %s" % (u"envoyé" if item.get("ack_sent") else u"EN ATTENTE"))
                if item.get("ack_error"):
                    lines.append(u"   ! Erreur ACK : %s" % item.get("ack_error"))
            for row in preview.get("items") or []:
                if row.get("status") == "blocked":
                    lines.append(u"   ! %s : %s" % (row.get("pmsl_ref") or u"action", row.get("reason") or u"blocage inconnu"))
            lines.append(u"")
        if mode != "apply":
            lines.append(u"Aucune écriture effectuée dans Noethys.")
        elif not result.get("synchronisation_complete"):
            lines.append(u"Au moins un ACK PMSL reste à transmettre. Une reprise idempotente est possible.")
        return u"\n".join(lines)

    def _message(self, text, icon):
        dlg = wx.MessageDialog(self, text, _(u"Synchronisation PMSL Équipe"), wx.OK | icon)
        dlg.ShowModal()
        dlg.Destroy()

    def OnFermer(self, event=None):
        self._save_config()
        self.EndModal(wx.ID_CANCEL)

    def OnClose(self, event):
        self._save_config()
        event.Skip()


if __name__ == "__main__":
    app = wx.App(0)
    dlg = Dialog(None)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    dlg.Destroy()
    app.MainLoop()
