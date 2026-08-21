#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Licence:          GNU GPL
#------------------------------------------------------------------------

import wx

from Utils.UTILS_Traduction import _
from Utils import UTILS_Portail_contenus
from Utils import UTILS_Portail_tarifs_bloc
from Ctrl import CTRL_Portail_tarifs


TYPE_IFRAME = 0
TYPE_TARIFS = 1


class PAGE_Iframe(wx.Panel):
    """Editeur historique d'une page/widget web embarqué."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDelement = None

        self.label_intro = wx.StaticText(
            self,
            -1,
            _(u"Affichez une page, une photothèque, un lecteur vidéo ou un widget web sans saisir de code HTML."),
        )
        self.label_url = wx.StaticText(self, -1, _(u"Adresse (URL) :"))
        self.ctrl_url = wx.TextCtrl(self, -1, "")

        self.label_titre = wx.StaticText(self, -1, _(u"Titre accessible :"))
        self.ctrl_titre = wx.TextCtrl(self, -1, "")

        self.label_hauteur = wx.StaticText(self, -1, _(u"Hauteur :"))
        self.ctrl_hauteur = wx.SpinCtrl(
            self,
            -1,
            min=UTILS_Portail_contenus.HAUTEUR_MIN,
            max=UTILS_Portail_contenus.HAUTEUR_MAX,
            initial=UTILS_Portail_contenus.HAUTEUR_DEFAUT,
        )
        self.label_pixels = wx.StaticText(self, -1, _(u"pixels"))

        self.ctrl_defilement = wx.CheckBox(self, -1, _(u"Autoriser les barres de défilement"))
        self.ctrl_plein_ecran = wx.CheckBox(self, -1, _(u"Autoriser le plein écran"))
        self.ctrl_plein_ecran.SetValue(True)

        self.label_aide = wx.StaticText(
            self,
            -1,
            _(u"Le bloc reste stocké comme un bloc Texte standard pour rester compatible avec les hébergements Connecthys existants."),
        )
        self.label_aide.Wrap(500)

        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        self.ctrl_url.SetToolTip(wx.ToolTip(_(u"Saisissez une adresse complète commençant par http:// ou https://")))
        self.ctrl_titre.SetToolTip(wx.ToolTip(_(u"Décrivez brièvement le contenu pour les lecteurs d'écran")))
        self.ctrl_hauteur.SetToolTip(wx.ToolTip(_(u"Hauteur d'affichage du contenu dans le portail famille")))

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.label_intro, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 10)

        grille = wx.FlexGridSizer(rows=3, cols=3, vgap=10, hgap=10)
        grille.Add(self.label_url, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grille.Add(self.ctrl_url, 0, wx.EXPAND, 0)
        grille.Add((1, 1), 0, 0, 0)

        grille.Add(self.label_titre, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grille.Add(self.ctrl_titre, 0, wx.EXPAND, 0)
        grille.Add((1, 1), 0, 0, 0)

        grille.Add(self.label_hauteur, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grille.Add(self.ctrl_hauteur, 0, 0, 0)
        grille.Add(self.label_pixels, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grille.AddGrowableCol(1)
        sizer_base.Add(grille, 0, wx.ALL | wx.EXPAND, 10)

        sizer_options = wx.BoxSizer(wx.VERTICAL)
        sizer_options.Add(self.ctrl_defilement, 0, wx.BOTTOM, 8)
        sizer_options.Add(self.ctrl_plein_ecran, 0, 0, 0)
        sizer_base.Add(sizer_options, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)

        sizer_base.AddStretchSpacer(1)
        sizer_base.Add(self.label_aide, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.SetSizer(sizer_base)
        self.Layout()

    def GetParametres(self):
        config = UTILS_Portail_contenus.normaliser_parametres({
            "type": "iframe",
            "url": self.ctrl_url.GetValue(),
            "hauteur": self.ctrl_hauteur.GetValue(),
            "defilement": self.ctrl_defilement.GetValue(),
            "plein_ecran": self.ctrl_plein_ecran.GetValue(),
            "titre": self.ctrl_titre.GetValue(),
        })
        return {"elements": [{
            "IDelement": self.IDelement,
            "titre": "",
            "date_debut": None,
            "date_fin": None,
            "parametres": UTILS_Portail_contenus.serialiser_parametres(config),
            "texte_xml": None,
            "texte_html": UTILS_Portail_contenus.construire_iframe(config),
        }]}

    def SetParametres(self, dictParametres=None):
        dictParametres = dictParametres or {}
        elements = dictParametres.get("elements", [])
        if not elements:
            return
        dictElement = elements[0]
        self.IDelement = dictElement.get("IDelement")
        config = UTILS_Portail_contenus.deserialiser_parametres(dictElement.get("parametres"))
        self.ctrl_url.SetValue(config["url"])
        self.ctrl_titre.SetValue(config["titre"])
        self.ctrl_hauteur.SetValue(config["hauteur"])
        self.ctrl_defilement.SetValue(config["defilement"])
        self.ctrl_plein_ecran.SetValue(config["plein_ecran"])

    def Validation(self):
        url = self.ctrl_url.GetValue()
        if not UTILS_Portail_contenus.url_externe_valide(url):
            dlg = wx.MessageDialog(
                self,
                _(u"Vous devez saisir une adresse web complète et valide commençant par http:// ou https://."),
                _(u"Erreur de saisie"),
                wx.OK | wx.ICON_EXCLAMATION,
            )
            dlg.ShowModal()
            dlg.Destroy()
            self.ctrl_url.SetFocus()
            return False
        return True


class CTRL(wx.Panel):
    """Point d'entrée unique des contenus publiés dynamiquement dans Connecthys."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent

        self.label_type = wx.StaticText(self, -1, _(u"Source :"))
        self.ctrl_type = wx.Choice(
            self,
            -1,
            choices=[_(u"Page / widget web"), _(u"Tarifs Noethys")],
        )
        self.ctrl_type.SetSelection(TYPE_IFRAME)

        self.book = wx.Simplebook(self, -1)
        self.page_iframe = PAGE_Iframe(self.book)
        self.page_tarifs = CTRL_Portail_tarifs.CTRL(self.book)
        self.book.AddPage(self.page_iframe, "iframe")
        self.book.AddPage(self.page_tarifs, "tarifs")

        ligne_source = wx.BoxSizer(wx.HORIZONTAL)
        ligne_source.Add(self.label_type, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        ligne_source.Add(self.ctrl_type, 1, wx.EXPAND)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(ligne_source, 0, wx.ALL | wx.EXPAND, 10)
        principal.Add(self.book, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 5)
        self.SetSizer(principal)
        self.Layout()

        self.Bind(wx.EVT_CHOICE, self.OnType, self.ctrl_type)
        self.OnType()

    def OnType(self, event=None):
        index = self.ctrl_type.GetSelection()
        if index not in (TYPE_IFRAME, TYPE_TARIFS):
            index = TYPE_IFRAME
        self.book.SetSelection(index)
        self.Layout()
        if event is not None:
            event.Skip()

    def GetPageActive(self):
        return self.page_tarifs if self.ctrl_type.GetSelection() == TYPE_TARIFS else self.page_iframe

    def GetParametres(self):
        return self.GetPageActive().GetParametres()

    def SetParametres(self, dictParametres=None):
        dictParametres = dictParametres or {}
        elements = dictParametres.get("elements", [])
        parametres = elements[0].get("parametres") if elements else None
        if UTILS_Portail_tarifs_bloc.est_configuration_bloc_tarifs(parametres):
            self.ctrl_type.SetSelection(TYPE_TARIFS)
            self.page_tarifs.SetParametres(dictParametres)
        else:
            self.ctrl_type.SetSelection(TYPE_IFRAME)
            self.page_iframe.SetParametres(dictParametres)
        self.OnType()

    def Validation(self):
        return self.GetPageActive().Validation()


def EstContenuExterne(dictParametres=None):
    """Détecte les contenus gérés par cet éditeur enrichi."""
    dictParametres = dictParametres or {}
    elements = dictParametres.get("elements", [])
    if not elements:
        return False
    parametres = elements[0].get("parametres")
    return (
        UTILS_Portail_contenus.est_configuration_contenu_externe(parametres)
        or UTILS_Portail_tarifs_bloc.est_configuration_bloc_tarifs(parametres)
    )
