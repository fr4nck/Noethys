#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Édition de la fonction d'un individu dans une famille/entité."""

from __future__ import annotations

import wx

from Utils.UTILS_Traduction import _
from Utils import UTILS_Fonctions_entites


class Dialog(wx.Dialog):
    def __init__(self, parent, IDrattachement=None):
        wx.Dialog.__init__(
            self, parent, -1, _(u"Fonction dans l'entité"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.IDrattachement = IDrattachement
        self.infos = UTILS_Fonctions_entites.GetInfosRattachement(IDrattachement)
        if self.infos is None:
            raise ValueError("Rattachement inconnu : %s" % IDrattachement)

        type_entite = UTILS_Fonctions_entites.GetTypeEntiteFamille(self.infos["IDfamille"])
        try:
            from Data import DATA_Fonctions_entites
            label_type = DATA_Fonctions_entites.GetLabelType(type_entite)
        except Exception:
            label_type = _(u"Entité")

        actuel = UTILS_Fonctions_entites.GetFonctionRattachement(IDrattachement)
        suggestions = UTILS_Fonctions_entites.GetSuggestionsFonctions(
            self.infos["IDfamille"], sexe=self.infos.get("sexe")
        )

        self.label_personne = wx.StaticText(
            self, -1,
            _(u"%s — %s") % (self.infos.get("nom_complet") or _(u"Individu"), label_type),
        )

        self.label_fonction = wx.StaticText(self, -1, _(u"Fonction :"))
        self.ctrl_fonction = wx.ComboBox(
            self, -1, actuel.get("fonction") or u"",
            choices=suggestions, style=wx.CB_DROPDOWN,
        )
        self.ctrl_fonction.SetToolTip(wx.ToolTip(
            _(u"Sélectionnez une fonction proposée ou saisissez librement une autre fonction.")
        ))

        self.box_usages = wx.StaticBox(self, -1, _(u"Usages dans cette entité"))
        self.ctrl_representant = wx.CheckBox(self, -1, _(u"Représentant de l'entité"))
        self.ctrl_signataire = wx.CheckBox(self, -1, _(u"Signataire des documents"))
        self.ctrl_facturation = wx.CheckBox(self, -1, _(u"Référent facturation"))
        self.ctrl_planning = wx.CheckBox(self, -1, _(u"Référent planning / organisation"))
        self.ctrl_defaut = wx.CheckBox(self, -1, _(u"Contact préféré par défaut pour ses usages"))

        self.ctrl_representant.SetValue(bool(actuel.get("representant")))
        self.ctrl_signataire.SetValue(bool(actuel.get("signataire")))
        self.ctrl_facturation.SetValue(bool(actuel.get("facturation")))
        self.ctrl_planning.SetValue(bool(actuel.get("planning")))
        self.ctrl_defaut.SetValue(bool(actuel.get("defaut")))

        self.bouton_ok = wx.Button(self, wx.ID_OK, _(u"Enregistrer"))
        self.bouton_ok.SetDefault()
        self.bouton_annuler = wx.Button(self, wx.ID_CANCEL, _(u"Annuler"))

        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)

        self.__do_layout()
        self.SetMinSize((500, -1))
        self.Fit()
        self.CentreOnParent()

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.label_personne, 0, wx.ALL | wx.EXPAND, 10)

        sizer_fonction = wx.FlexGridSizer(rows=1, cols=2, vgap=5, hgap=8)
        sizer_fonction.Add(self.label_fonction, 0, wx.ALIGN_CENTER_VERTICAL)
        sizer_fonction.Add(self.ctrl_fonction, 1, wx.EXPAND)
        sizer_fonction.AddGrowableCol(1)
        sizer_base.Add(sizer_fonction, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        box = wx.StaticBoxSizer(self.box_usages, wx.VERTICAL)
        for ctrl in (
            self.ctrl_representant,
            self.ctrl_signataire,
            self.ctrl_facturation,
            self.ctrl_planning,
            self.ctrl_defaut,
        ):
            box.Add(ctrl, 0, wx.ALL, 4)
        sizer_base.Add(box, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        sizer_boutons = wx.StdDialogButtonSizer()
        sizer_boutons.AddButton(self.bouton_ok)
        sizer_boutons.AddButton(self.bouton_annuler)
        sizer_boutons.Realize()
        sizer_base.Add(sizer_boutons, 0, wx.ALL | wx.ALIGN_RIGHT, 10)

        self.SetSizer(sizer_base)

    def OnBoutonOk(self, event):
        fonction = self.ctrl_fonction.GetValue().strip()
        usages = (
            self.ctrl_representant.GetValue(),
            self.ctrl_signataire.GetValue(),
            self.ctrl_facturation.GetValue(),
            self.ctrl_planning.GetValue(),
        )
        # Le champ peut être laissé vide tant qu'aucun usage n'est coché.
        # Dès qu'on veut exploiter cette personne automatiquement, une
        # fonction explicite évite de générer "représenté par ... en
        # qualité de ..." avec une donnée absente.
        if any(usages) and not fonction:
            dlg = wx.MessageDialog(
                self,
                _(u"Indiquez la fonction de cette personne dans l'entité "
                  u"avant de lui attribuer un usage automatique."),
                _(u"Fonction manquante"),
                wx.OK | wx.ICON_EXCLAMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_fonction.SetFocus()
            return

        UTILS_Fonctions_entites.EnregistrerFonctionRattachement(
            self.IDrattachement,
            fonction=fonction,
            representant=self.ctrl_representant.GetValue(),
            signataire=self.ctrl_signataire.GetValue(),
            facturation=self.ctrl_facturation.GetValue(),
            planning=self.ctrl_planning.GetValue(),
            defaut=self.ctrl_defaut.GetValue(),
        )
        self.EndModal(wx.ID_OK)


if __name__ == "__main__":
    app = wx.App(False)
    dlg = Dialog(None, IDrattachement=1)
    dlg.ShowModal()
    dlg.Destroy()
    app.Destroy()
