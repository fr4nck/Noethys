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


class CTRL(wx.Panel):
    """Editeur d'un contenu externe rendu comme bloc texte Connecthys."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        self.IDelement = None
        self.texte_html_precedent = None

        self.label_intro = wx.StaticText(
            self,
            -1,
            _(u"Affichez une page, une photothèque, un lecteur vidéo ou un flux d'actualités sans saisir de code HTML."),
        )

        self.label_type = wx.StaticText(self, -1, _(u"Type de contenu :"))
        self.ctrl_type = wx.Choice(self, -1, choices=[
            _(u"Page / widget web"),
            _(u"Flux RSS / Atom"),
        ])
        self.ctrl_type.SetSelection(0)

        self.label_url = wx.StaticText(self, -1, _(u"Adresse (URL) :"))
        self.ctrl_url = wx.TextCtrl(self, -1, "")

        # Options iframe
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

        # Options RSS / Atom
        self.label_nombre_articles = wx.StaticText(self, -1, _(u"Nombre d'actualités :"))
        self.ctrl_nombre_articles = wx.SpinCtrl(
            self,
            -1,
            min=UTILS_Portail_contenus.RSS_NOMBRE_MIN,
            max=UTILS_Portail_contenus.RSS_NOMBRE_MAX,
            initial=UTILS_Portail_contenus.RSS_NOMBRE_DEFAUT,
        )
        self.ctrl_afficher_date = wx.CheckBox(self, -1, _(u"Afficher la date"))
        self.ctrl_afficher_date.SetValue(True)
        self.ctrl_afficher_extrait = wx.CheckBox(self, -1, _(u"Afficher l'extrait"))
        self.ctrl_afficher_extrait.SetValue(True)
        self.ctrl_liens_nouvel_onglet = wx.CheckBox(self, -1, _(u"Ouvrir les articles dans un nouvel onglet"))
        self.ctrl_liens_nouvel_onglet.SetValue(True)

        self.label_aide = wx.StaticText(
            self,
            -1,
            _(u"Le bloc reste compatible avec les hébergements Connecthys existants. Les flux RSS/Atom sont actualisés par Noethys lors de la synchronisation."),
        )
        self.label_aide.Wrap(500)

        self.__set_properties()
        self.__do_layout()
        self.Bind(wx.EVT_CHOICE, self.OnChoixType, self.ctrl_type)
        self.MAJAffichage()

    def __set_properties(self):
        self.ctrl_type.SetToolTip(wx.ToolTip(_(u"Choisissez une page embarquée ou un flux d'actualités RSS/Atom")))
        self.ctrl_url.SetToolTip(wx.ToolTip(_(u"Saisissez une adresse complète commençant par http:// ou https://")))
        self.ctrl_titre.SetToolTip(wx.ToolTip(_(u"Décrivez brièvement le contenu embarqué pour les lecteurs d'écran")))
        self.ctrl_hauteur.SetToolTip(wx.ToolTip(_(u"Hauteur d'affichage du contenu dans le portail famille")))
        self.ctrl_nombre_articles.SetToolTip(wx.ToolTip(_(u"Nombre maximum d'actualités affichées dans le portail")))

    def __do_layout(self):
        sizer_base = wx.BoxSizer(wx.VERTICAL)
        sizer_base.Add(self.label_intro, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.EXPAND, 10)

        grille_commune = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=10)
        grille_commune.Add(self.label_type, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grille_commune.Add(self.ctrl_type, 0, wx.EXPAND, 0)
        grille_commune.Add(self.label_url, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grille_commune.Add(self.ctrl_url, 0, wx.EXPAND, 0)
        grille_commune.AddGrowableCol(1)
        sizer_base.Add(grille_commune, 0, wx.ALL | wx.EXPAND, 10)

        # Zone iframe
        self.sizer_iframe = wx.BoxSizer(wx.VERTICAL)
        grille_iframe = wx.FlexGridSizer(rows=2, cols=3, vgap=10, hgap=10)
        grille_iframe.Add(self.label_titre, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grille_iframe.Add(self.ctrl_titre, 0, wx.EXPAND, 0)
        grille_iframe.Add((1, 1), 0, 0, 0)
        grille_iframe.Add(self.label_hauteur, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grille_iframe.Add(self.ctrl_hauteur, 0, 0, 0)
        grille_iframe.Add(self.label_pixels, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grille_iframe.AddGrowableCol(1)
        self.sizer_iframe.Add(grille_iframe, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.sizer_iframe.Add(self.ctrl_defilement, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)
        self.sizer_iframe.Add(self.ctrl_plein_ecran, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)
        sizer_base.Add(self.sizer_iframe, 0, wx.EXPAND, 0)

        # Zone RSS
        self.sizer_rss = wx.BoxSizer(wx.VERTICAL)
        grille_rss = wx.FlexGridSizer(rows=1, cols=2, vgap=10, hgap=10)
        grille_rss.Add(self.label_nombre_articles, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL, 0)
        grille_rss.Add(self.ctrl_nombre_articles, 0, 0, 0)
        self.sizer_rss.Add(grille_rss, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)
        self.sizer_rss.Add(self.ctrl_afficher_date, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)
        self.sizer_rss.Add(self.ctrl_afficher_extrait, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)
        self.sizer_rss.Add(self.ctrl_liens_nouvel_onglet, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)
        sizer_base.Add(self.sizer_rss, 0, wx.EXPAND, 0)

        sizer_base.AddStretchSpacer(1)
        sizer_base.Add(self.label_aide, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 10)

        self.SetSizer(sizer_base)
        self.Layout()

    def OnChoixType(self, event):
        self.MAJAffichage()

    def GetType(self):
        if self.ctrl_type.GetSelection() == 1:
            return UTILS_Portail_contenus.TYPE_RSS
        return UTILS_Portail_contenus.TYPE_IFRAME

    def SetType(self, type_contenu):
        self.ctrl_type.SetSelection(1 if type_contenu == UTILS_Portail_contenus.TYPE_RSS else 0)
        self.MAJAffichage()

    def MAJAffichage(self):
        rss = self.GetType() == UTILS_Portail_contenus.TYPE_RSS
        for controle in (
            self.label_titre, self.ctrl_titre,
            self.label_hauteur, self.ctrl_hauteur, self.label_pixels,
            self.ctrl_defilement, self.ctrl_plein_ecran,
        ):
            controle.Show(not rss)
        for controle in (
            self.label_nombre_articles, self.ctrl_nombre_articles,
            self.ctrl_afficher_date, self.ctrl_afficher_extrait,
            self.ctrl_liens_nouvel_onglet,
        ):
            controle.Show(rss)
        self.Layout()

    def GetParametres(self):
        config = {
            "type": self.GetType(),
            "url": self.ctrl_url.GetValue(),
            "hauteur": self.ctrl_hauteur.GetValue(),
            "defilement": self.ctrl_defilement.GetValue(),
            "plein_ecran": self.ctrl_plein_ecran.GetValue(),
            "titre": self.ctrl_titre.GetValue(),
            "nombre_articles": self.ctrl_nombre_articles.GetValue(),
            "afficher_date": self.ctrl_afficher_date.GetValue(),
            "afficher_extrait": self.ctrl_afficher_extrait.GetValue(),
            "liens_nouvel_onglet": self.ctrl_liens_nouvel_onglet.GetValue(),
        }
        config = UTILS_Portail_contenus.normaliser_parametres(config)

        if config["type"] == UTILS_Portail_contenus.TYPE_IFRAME:
            texte_html = UTILS_Portail_contenus.construire_iframe(config)
        else:
            # Ne déclenche aucune requête réseau depuis la fenêtre de saisie.
            # La synchronisation actualisera le flux et remplacera ce cache.
            texte_html = self.texte_html_precedent or UTILS_Portail_contenus.construire_placeholder_flux()

        dictElement = {
            "IDelement": self.IDelement,
            "titre": "",
            "date_debut": None,
            "date_fin": None,
            "parametres": UTILS_Portail_contenus.serialiser_parametres(config),
            "texte_xml": None,
            "texte_html": texte_html,
        }
        return {"elements": [dictElement]}

    def SetParametres(self, dictParametres=None):
        dictParametres = dictParametres or {}
        elements = dictParametres.get("elements", [])
        if not elements:
            return

        dictElement = elements[0]
        self.IDelement = dictElement.get("IDelement")
        self.texte_html_precedent = dictElement.get("texte_html")
        config = UTILS_Portail_contenus.deserialiser_parametres(dictElement.get("parametres"))
        self.SetType(config["type"])
        self.ctrl_url.SetValue(config["url"])
        self.ctrl_titre.SetValue(config["titre"])
        self.ctrl_hauteur.SetValue(config["hauteur"])
        self.ctrl_defilement.SetValue(config["defilement"])
        self.ctrl_plein_ecran.SetValue(config["plein_ecran"])
        self.ctrl_nombre_articles.SetValue(config["nombre_articles"])
        self.ctrl_afficher_date.SetValue(config["afficher_date"])
        self.ctrl_afficher_extrait.SetValue(config["afficher_extrait"])
        self.ctrl_liens_nouvel_onglet.SetValue(config["liens_nouvel_onglet"])
        self.MAJAffichage()

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


def EstContenuExterne(dictParametres=None):
    """Indique si un bloc texte existant a été créé par cet éditeur."""
    dictParametres = dictParametres or {}
    elements = dictParametres.get("elements", [])
    if not elements:
        return False
    return UTILS_Portail_contenus.est_configuration_contenu_externe(elements[0].get("parametres"))
