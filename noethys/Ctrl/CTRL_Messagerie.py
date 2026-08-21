#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Licence :        GNU GPL
#------------------------------------------------------------------------
"""Structure UI du futur client mail intégré.

Ce fichier ne réalise volontairement aucune connexion IMAP à l'import. Le
module principal ne devra l'importer que si ``UTILS_Modules.EstActif('messagerie')``
est vrai.
"""

import wx

from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


class Panel(wx.Panel):
    """Client mail desktop dense : dossiers, liste, aperçu."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, name="messagerie", style=wx.TAB_TRAVERSAL)

        style_splitter = wx.SP_LIVE_UPDATE | wx.SP_NOBORDER
        self.splitter_principal = wx.SplitterWindow(self, style=style_splitter)
        self.splitter_contenu = wx.SplitterWindow(self.splitter_principal, style=style_splitter)

        self.panel_dossiers = wx.Panel(self.splitter_principal)
        self.panel_liste = wx.Panel(self.splitter_contenu)
        self.panel_apercu = wx.Panel(self.splitter_contenu)

        self.ctrl_dossiers = wx.ListBox(
            self.panel_dossiers,
            choices=[
                _(u"Réception"),
                _(u"À traiter"),
                _(u"Envoyés"),
                _(u"Brouillons"),
                _(u"Archives"),
                _(u"Corbeille"),
            ],
        )
        self.ctrl_dossiers.SetSelection(0)

        self.ctrl_messages = wx.ListCtrl(
            self.panel_liste,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES,
        )
        self.ctrl_messages.AppendColumn(_(u"Correspondant"), width=Style.px(180))
        self.ctrl_messages.AppendColumn(_(u"Objet"), width=Style.px(320))
        self.ctrl_messages.AppendColumn(_(u"Date"), width=Style.px(120))

        self.ctrl_entete = wx.StaticText(
            self.panel_apercu,
            label=_(u"Sélectionnez un message pour afficher son contenu."),
        )
        self.ctrl_apercu = wx.TextCtrl(
            self.panel_apercu,
            value="",
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_NONE,
        )

        self._AppliqueApparence()
        self._ConstruitLayout()
        self.ctrl_messages.Bind(wx.EVT_SIZE, self._OnMessagesSize)

    def _AppliqueApparence(self):
        Style.appliquer_fenetre(self, "surface")
        for panel in (self.panel_dossiers, self.panel_liste, self.panel_apercu):
            Style.appliquer_fenetre(panel, "surface")
        for ctrl in (self.ctrl_dossiers, self.ctrl_messages, self.ctrl_apercu):
            Style.appliquer_liste(ctrl)
        Style.appliquer_texte(
            self.ctrl_entete,
            role="body_emphasis",
            role_texte="on_surface",
            role_fond="surface",
        )

    def _ConstruitLayout(self):
        marge = Style.espace(2)

        sizer_dossiers = wx.BoxSizer(wx.VERTICAL)
        sizer_dossiers.Add(self.ctrl_dossiers, 1, wx.EXPAND | wx.ALL, marge)
        self.panel_dossiers.SetSizer(sizer_dossiers)

        sizer_liste = wx.BoxSizer(wx.VERTICAL)
        sizer_liste.Add(self.ctrl_messages, 1, wx.EXPAND)
        self.panel_liste.SetSizer(sizer_liste)

        sizer_apercu = wx.BoxSizer(wx.VERTICAL)
        sizer_apercu.Add(self.ctrl_entete, 0, wx.EXPAND | wx.ALL, Style.espace(3))
        sizer_apercu.Add(
            self.ctrl_apercu,
            1,
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            Style.espace(3),
        )
        self.panel_apercu.SetSizer(sizer_apercu)

        self.splitter_contenu.SetMinimumPaneSize(Style.px(180))
        self.splitter_contenu.SplitVertically(self.panel_liste, self.panel_apercu)
        self.splitter_contenu.SetSashGravity(0.52)

        self.splitter_principal.SetMinimumPaneSize(Style.px(130))
        self.splitter_principal.SplitVertically(self.panel_dossiers, self.splitter_contenu)
        self.splitter_principal.SetSashGravity(0.18)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.splitter_principal, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()

        # Proportions initiales, puis les sash gravities laissent wx répartir
        # proprement l'espace lorsque la fenêtre est redimensionnée.
        wx.CallAfter(self._PositionneSplitters)
        wx.CallAfter(self._AjusteColonnes)

    def _PositionneSplitters(self):
        largeur = max(1, self.GetClientSize().GetWidth())
        self.splitter_principal.SetSashPosition(
            max(Style.px(150), int(largeur * 0.17))
        )
        largeur_contenu = max(1, self.splitter_contenu.GetClientSize().GetWidth())
        self.splitter_contenu.SetSashPosition(
            max(Style.px(300), int(largeur_contenu * 0.50))
        )

    def _OnMessagesSize(self, event):
        event.Skip()
        wx.CallAfter(self._AjusteColonnes)

    def _AjusteColonnes(self):
        """Répartit les colonnes selon la largeur réellement disponible."""
        try:
            largeur = self.ctrl_messages.GetClientSize().GetWidth()
            if largeur <= Style.px(260):
                return
            largeur_date = Style.px(120)
            largeur_correspondant = max(Style.px(140), int(largeur * 0.30))
            largeur_objet = max(
                Style.px(160),
                largeur - largeur_correspondant - largeur_date - Style.espace(2),
            )
            self.ctrl_messages.SetColumnWidth(0, largeur_correspondant)
            self.ctrl_messages.SetColumnWidth(1, largeur_objet)
            self.ctrl_messages.SetColumnWidth(2, largeur_date)
        except Exception:
            pass

    def Initialisation(self):
        """Point d'entrée futur pour démarrer la synchronisation IMAP lazy."""
        return True

    def Arret(self):
        """Point d'arrêt futur du worker/timer de relève."""
        return True


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        self.ctrl = Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.SetSize((1200, 720))
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame = MyFrame(None, -1, _(u"Messagerie Noethys"))
    app.SetTopWindow(frame)
    frame.Show()
    app.MainLoop()
