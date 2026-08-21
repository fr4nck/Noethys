#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Licence:          GNU GPL
#------------------------------------------------------------------------

"""Interface du bloc de tarifs Noethys publié comme texte Connecthys."""

import html as html_std

import wx
import wx.html as wxhtml

import GestionDB
from Utils.UTILS_Traduction import _
from Utils import UTILS_Portail_tarifs_bloc
from Utils import UTILS_Portail_tarifs_donnees


class CTRL(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDelement = None
        self.config = UTILS_Portail_tarifs_bloc.normaliser_configuration()
        self.catalogue = []
        self.html_actuel = ""

        self.label_intro = wx.StaticText(
            self,
            -1,
            _(u"Publiez les tarifs configurés dans Noethys sans les ressaisir. En mode automatique, une nouvelle activité tarifée apparaîtra d'elle-même."),
        )
        self.label_intro.Wrap(560)

        self.label_titre = wx.StaticText(self, -1, _(u"Titre affiché :"))
        self.ctrl_titre = wx.TextCtrl(self, -1, UTILS_Portail_tarifs_bloc.TITRE_DEFAUT)

        self.radio_auto = wx.RadioButton(self, -1, _(u"Automatique (recommandé)"), style=wx.RB_GROUP)
        self.radio_selection = wx.RadioButton(self, -1, _(u"Sélection manuelle"))
        self.radio_auto.SetValue(True)

        self.label_activites = wx.StaticText(self, -1, _(u"Activités avec un tarif courant ou futur :"))
        self.ctrl_activites = wx.CheckListBox(self, -1)
        self.ctrl_activites.SetMinSize((250, 120))

        self.label_regle = wx.StaticText(
            self,
            -1,
            _(u"En automatique, décocher une activité l'exclut. En sélection manuelle, seules les activités cochées sont publiées."),
        )
        self.label_regle.Wrap(560)

        self.bouton_apercu = wx.Button(self, -1, _(u"Actualiser l'aperçu"))
        self.ctrl_apercu = wxhtml.HtmlWindow(
            self,
            -1,
            style=wxhtml.HW_NO_SELECTION | wx.BORDER_THEME,
        )
        self.ctrl_apercu.SetMinSize((320, 150))

        self.__do_layout()
        self.Bind(wx.EVT_BUTTON, self.OnApercu, self.bouton_apercu)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnMode, self.radio_auto)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnMode, self.radio_selection)

        self.ChargerCatalogue()
        self.AppliquerConfiguration(self.config)
        self.RafraichirApercu(silencieux=True)

    def __do_layout(self):
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(self.label_intro, 0, wx.ALL | wx.EXPAND, 10)

        ligne_titre = wx.BoxSizer(wx.HORIZONTAL)
        ligne_titre.Add(self.label_titre, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        ligne_titre.Add(self.ctrl_titre, 1, wx.EXPAND)
        principal.Add(ligne_titre, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        ligne_mode = wx.BoxSizer(wx.HORIZONTAL)
        ligne_mode.Add(self.radio_auto, 0, wx.RIGHT, 18)
        ligne_mode.Add(self.radio_selection, 0)
        principal.Add(ligne_mode, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        principal.Add(self.label_activites, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        principal.Add(self.ctrl_activites, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        principal.Add(self.label_regle, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        ligne_apercu = wx.BoxSizer(wx.HORIZONTAL)
        ligne_apercu.AddStretchSpacer(1)
        ligne_apercu.Add(self.bouton_apercu, 0)
        principal.Add(ligne_apercu, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        principal.Add(self.ctrl_apercu, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        self.SetSizer(principal)
        self.Layout()

    def ChargerCatalogue(self):
        """Découvre les activités publiables sans mémoriser une liste figée."""
        DB = GestionDB.DB()
        try:
            publication = UTILS_Portail_tarifs_donnees.construire_publication(
                DB,
                politique={
                    "mode": "automatique",
                    "IDsactivites": [],
                    "IDsactivites_exclues": [],
                },
                titre=self.ctrl_titre.GetValue(),
            )
        finally:
            DB.Close()

        par_id = {}
        for description in publication.get("descriptions", []):
            IDactivite = description.get("IDactivite")
            if IDactivite is None:
                continue
            par_id[IDactivite] = description.get("activite") or _(u"Activité %s") % IDactivite
        self.catalogue = sorted(par_id.items(), key=lambda item: str(item[1]).lower())
        self.ctrl_activites.Set([nom for IDactivite, nom in self.catalogue])

    def GetIDsCoches(self):
        resultat = []
        for index, (IDactivite, nom) in enumerate(self.catalogue):
            if self.ctrl_activites.IsChecked(index):
                resultat.append(IDactivite)
        return resultat

    def GetPolitique(self):
        IDs_coches = self.GetIDsCoches()
        IDs_catalogue = [IDactivite for IDactivite, nom in self.catalogue]
        if self.radio_selection.GetValue():
            return {
                "mode": "selection",
                "IDsactivites": IDs_coches,
                "IDsactivites_exclues": [],
            }
        return {
            "mode": "automatique",
            "IDsactivites": [],
            "IDsactivites_exclues": [IDactivite for IDactivite in IDs_catalogue if IDactivite not in IDs_coches],
        }

    def GetConfiguration(self):
        politique = self.GetPolitique()
        return UTILS_Portail_tarifs_bloc.normaliser_configuration({
            "mode": politique["mode"],
            "IDsactivites": politique["IDsactivites"],
            "IDsactivites_exclues": politique["IDsactivites_exclues"],
            "titre": self.ctrl_titre.GetValue(),
        })

    def AppliquerConfiguration(self, config):
        self.config = UTILS_Portail_tarifs_bloc.normaliser_configuration(config)
        self.ctrl_titre.SetValue(self.config["titre"])
        manuel = self.config["mode"] == UTILS_Portail_tarifs_bloc.MODE_SELECTION
        self.radio_selection.SetValue(manuel)
        self.radio_auto.SetValue(not manuel)

        inclus = set(self.config["IDsactivites"])
        exclus = set(self.config["IDsactivites_exclues"])
        for index, (IDactivite, nom) in enumerate(self.catalogue):
            if manuel:
                coche = IDactivite in inclus
            else:
                coche = IDactivite not in exclus
            self.ctrl_activites.Check(index, coche)

    def ConstruirePublication(self):
        config = self.GetConfiguration()
        DB = GestionDB.DB()
        try:
            publication = UTILS_Portail_tarifs_donnees.construire_publication(
                DB,
                politique=UTILS_Portail_tarifs_bloc.politique_depuis_configuration(config),
                titre=config["titre"],
            )
        finally:
            DB.Close()
        return config, publication

    def RafraichirApercu(self, silencieux=False):
        try:
            config, publication = self.ConstruirePublication()
            html = publication.get("html") or ""
            if not publication.get("descriptions"):
                html = '<div class="noethys-tarifs"><h3>%s</h3><p>%s</p></div>' % (
                    html_std.escape(config["titre"]),
                    html_std.escape(_(u"Aucun tarif publiable pour le moment.")),
                )
            self.html_actuel = html
            self.ctrl_apercu.SetPage(html)
            return publication
        except Exception as err:
            if not silencieux:
                dlg = wx.MessageDialog(
                    self,
                    _(u"Impossible de générer l'aperçu des tarifs : %s") % err,
                    _(u"Erreur"),
                    wx.OK | wx.ICON_ERROR,
                )
                dlg.ShowModal()
                dlg.Destroy()
            return None

    def OnApercu(self, event):
        self.RafraichirApercu()

    def OnMode(self, event):
        event.Skip()

    def GetParametres(self):
        publication = self.RafraichirApercu(silencieux=True)
        config = self.GetConfiguration()
        return {"elements": [{
            "IDelement": self.IDelement,
            "titre": "",
            "date_debut": None,
            "date_fin": None,
            "parametres": UTILS_Portail_tarifs_bloc.serialiser_configuration(config),
            "texte_xml": None,
            "texte_html": self.html_actuel,
        }]}

    def SetParametres(self, dictParametres=None):
        dictParametres = dictParametres or {}
        elements = dictParametres.get("elements", [])
        if not elements:
            return
        element = elements[0]
        self.IDelement = element.get("IDelement")
        config = UTILS_Portail_tarifs_bloc.deserialiser_configuration(element.get("parametres"))
        self.AppliquerConfiguration(config)
        self.html_actuel = element.get("texte_html") or ""
        self.RafraichirApercu(silencieux=True)

    def Validation(self):
        if not self.ctrl_titre.GetValue().strip():
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez saisir un titre pour la publication des tarifs."),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_EXCLAMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_titre.SetFocus()
            return False
        if self.radio_selection.GetValue() and not self.GetIDsCoches():
            dlg = wx.MessageDialog(
                self,
                _(u"En sélection manuelle, cochez au moins une activité."),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_EXCLAMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False
        return self.RafraichirApercu(silencieux=False) is not None


def EstBlocTarifs(dictParametres=None):
    dictParametres = dictParametres or {}
    elements = dictParametres.get("elements", [])
    if not elements:
        return False
    return UTILS_Portail_tarifs_bloc.est_configuration_bloc_tarifs(elements[0].get("parametres"))
