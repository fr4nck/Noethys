#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:          Licence GNU GPL
#-----------------------------------------------------------

import wx

from Ctrl import CTRL_ActionRepens
from Ol import OL_Messages
from Utils import UTILS_Adaptations
from Utils import UTILS_ColonnesResponsive
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


ID_AJOUTER = wx.Window.NewControlId()
ID_MODIFIER = wx.Window.NewControlId()
ID_PLUS = wx.Window.NewControlId()


class ListeMessagesAccueil(OL_Messages.ListView):
    """Messages d'accueil sans icône 16 px historique ni largeur 950 fixe."""

    SPECS_COLONNES = (
        (0, 0.0),
        (86, 0.0),
        (180, 3.0),
        (72, 0.0),
    )

    def __init__(self, *args, **kwds):
        OL_Messages.ListView.__init__(self, *args, **kwds)
        Style.appliquer_liste(self)
        UTILS_ColonnesResponsive.Installer(self, self.SPECS_COLONNES)

    def InitObjectListView(self):
        def FormateDateCourt(dateDD):
            if dateDD is None:
                return ""
            return OL_Messages.DateEngFr(str(dateDD))

        def FormatePriorite(priorite):
            return _(u"Prioritaire") if priorite == "HAUTE" else ""

        self.oddRowsBackColor = Style.couleur("surface_container_low")
        self.evenRowsBackColor = Style.couleur("surface_container_lowest")
        self.SetBackgroundColour(Style.couleur("surface_container_lowest"))
        self.SetForegroundColour(Style.couleur("on_surface"))
        self.SetFont(Style.police("body"))
        self.useExpansionColumn = False

        colonnes = [
            OL_Messages.ColumnDefn(u"", "left", 0, "IDmessage", typeDonnee="entier"),
            OL_Messages.ColumnDefn(_(u"Date"), "centre", 86, "date_parution", typeDonnee="date", stringConverter=FormateDateCourt),
            OL_Messages.ColumnDefn(_(u"Message"), "left", 180, "texte", typeDonnee="texte"),
            OL_Messages.ColumnDefn(_(u"Priorité"), "centre", 72, "priorite", typeDonnee="texte", stringConverter=FormatePriorite),
        ]
        self.SetColumns(colonnes)
        self.SetEmptyListMsg(_(u"Aucun message à traiter"))
        self.SetSortColumn(self.columns[1])
        self.SetObjects(self.donnees)
        wx.CallAfter(UTILS_ColonnesResponsive.Ajuster, self)


class Panel(wx.Panel):
    """Messages & alertes : surface de travail compacte du cockpit."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL)
        self.parent = parent
        Style.appliquer_fenetre(self, "surface")

        self.ctrl_compteur = wx.StaticText(self, label=_(u"Aucun message"))
        Style.appliquer_texte(
            self.ctrl_compteur,
            role="body_emphasis",
            role_texte="on_surface_variant",
            role_fond="surface",
        )

        self.ctrl_ajouter = CTRL_ActionRepens.CTRL(
            self,
            id=ID_AJOUTER,
            label=_(u"Nouveau"),
            icone="add",
            variante="primaire",
            tooltip=_(u"Saisir un message ou une alerte"),
        )
        self.ctrl_modifier = CTRL_ActionRepens.CTRL(
            self,
            id=ID_MODIFIER,
            label=_(u"Modifier"),
            icone="edit",
            tooltip=_(u"Modifier le message sélectionné"),
        )
        self.ctrl_plus = CTRL_ActionRepens.CTRL(
            self,
            id=ID_PLUS,
            label=_(u"Plus"),
            icone="more",
            variante="ghost",
            tooltip=_(u"Supprimer ou actualiser"),
        )

        self.ctrl_messages = ListeMessagesAccueil(
            self,
            -1,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.NO_BORDER,
        )

        self.ctrl_ajouter.Bind(wx.EVT_BUTTON, self.OnAjouterMessage)
        self.ctrl_modifier.Bind(wx.EVT_BUTTON, self.OnModifierMessage)
        self.ctrl_plus.Bind(wx.EVT_BUTTON, self.OnPlus)
        self.ctrl_messages.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelectionChange)
        self.ctrl_messages.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnSelectionChange)

        self.__do_layout()
        self._ActualiserActions()
        wx.CallAfter(self._ActualisePaneAui)

    def _ActualisePaneAui(self):
        gestionnaire = getattr(self.GetParent(), "_mgr", None)
        if gestionnaire is None:
            return
        try:
            pane = gestionnaire.GetPane(self)
            if pane.IsOk():
                pane.Caption(_(u"Messages & alertes"))
                pane.CloseButton(True)
                pane.MinimizeButton(True)
                pane.MaximizeButton(True)
                pane.Resizable(True)
                gestionnaire.Update()
        except Exception:
            pass

    def __do_layout(self):
        marge = Style.espace(2)
        petit = Style.espace(1)
        sizer = wx.BoxSizer(wx.VERTICAL)

        commandes = wx.BoxSizer(wx.HORIZONTAL)
        commandes.Add(self.ctrl_compteur, 1, wx.ALIGN_CENTER_VERTICAL)
        commandes.Add(self.ctrl_ajouter, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, marge)
        commandes.Add(self.ctrl_modifier, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, petit)
        commandes.Add(self.ctrl_plus, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, petit)
        sizer.Add(commandes, 0, wx.EXPAND | wx.ALL, marge)
        sizer.Add(self.ctrl_messages, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, petit)

        self.SetSizer(sizer)
        self.Layout()

    def _Selection(self):
        try:
            return bool(self.ctrl_messages.GetSelectedObjects())
        except Exception:
            return False

    def _ActualiserActions(self):
        self.ctrl_modifier.Enable(self._Selection())
        self.ctrl_modifier.Refresh()

    def OnSelectionChange(self, event):
        wx.CallAfter(self._ActualiserActions)
        event.Skip()

    def MAJ(self):
        self.ctrl_messages.MAJ()
        try:
            nbre = len(self.ctrl_messages.donnees)
            self.ctrl_compteur.SetLabel(
                _(u"%d message(s) à traiter") % nbre if nbre else _(u"Aucun message à traiter")
            )
        except Exception:
            self.ctrl_compteur.SetLabel("")
        self._ActualiserActions()
        self.Layout()

    def OnAjouterMessage(self, event=None):
        self.ctrl_messages.Ajouter(None)
        self.MAJ()

    def OnModifierMessage(self, event=None):
        self.ctrl_messages.Modifier(None)
        self.MAJ()

    def OnPlus(self, event=None):
        menu = UTILS_Adaptations.Menu()
        identifiant_supprimer = wx.Window.NewControlId()
        item = menu.Append(identifiant_supprimer, _(u"Supprimer le message…"))
        item.Enable(self._Selection())
        self.Bind(wx.EVT_MENU, self.OnSupprimerMessage, id=identifiant_supprimer)
        menu.AppendSeparator()
        identifiant_actualiser = wx.Window.NewControlId()
        menu.Append(identifiant_actualiser, _(u"Actualiser"))
        self.Bind(wx.EVT_MENU, lambda evt: self.MAJ(), id=identifiant_actualiser)
        self.PopupMenu(menu)
        menu.Destroy()

    def OnSupprimerMessage(self, event=None):
        self.ctrl_messages.Supprimer(None)
        self.MAJ()

    def GetMessages(self):
        return self.ctrl_messages.donnees


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(self, "surface")
        Style.appliquer_fenetre(panel, "surface")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = Panel(panel)
        self.ctrl.MAJ()
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.EXPAND)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(900, 420))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
