#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#-----------------------------------------------------------

import wx

import GestionDB
from Ctrl import CTRL_ActionRepens
from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics
from Utils.UTILS_Traduction import _


class ListBox_Messages(wx.ListBox):
    def __init__(self, parent):
        wx.ListBox.__init__(self, parent, -1)
        self.parent = parent
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
        self.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        try:
            police = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
            facteur = UTILS_Interface.GetTailleTexte() / 100.0
            police.SetPointSize(max(8, int(round(police.GetPointSize() * facteur))))
            self.SetFont(police)
        except Exception:
            pass
        self.SetMinSize((UTILS_UIMetrics.px(260), UTILS_UIMetrics.panel_min_height("secondary")))
        self.SetToolTip(wx.ToolTip(_(u"Messages affichés sur la page d'accueil du portail. Double-cliquez pour modifier.")))
        self.MAJ()
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.Modifier)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    def OnKeyDown(self, event):
        if event.GetKeyCode() == wx.WXK_DELETE:
            self.Supprimer()
            return
        event.Skip()

    def MAJ(self):
        self.dictDonnees = {}
        self.listeMessages = []
        self.Clear()
        DB = GestionDB.DB()
        req = """SELECT IDmessage, titre, texte
        FROM portail_messages
        ORDER BY titre;"""
        DB.ExecuterReq(req)
        listeMessages = DB.ResultatReq()
        DB.Close()
        for IDmessage, titre, texte in listeMessages:
            self.Insert(titre, self.GetCount(), IDmessage)
            self.dictDonnees[IDmessage] = {"IDmessage": IDmessage, "titre": titre, "texte": texte}
            self.listeMessages.append((titre, texte))
        return []

    def GetSelectionMessage(self):
        index = self.GetSelection()
        if index == -1:
            return None
        IDmessage = self.GetClientData(index)
        return self.dictDonnees.get(IDmessage)

    def Ajouter(self, event=None):
        from Dlg import DLG_Saisie_portail_message
        dlg = DLG_Saisie_portail_message.Dialog(self, IDmessage=None)
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ()
        dlg.Destroy()

    def Modifier(self, event=None):
        message = self.GetSelectionMessage()
        if message is None:
            dlg = wx.MessageDialog(self, _(u"Vous n'avez sélectionné aucun message à modifier dans la liste !"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return
        from Dlg import DLG_Saisie_portail_message
        dlg = DLG_Saisie_portail_message.Dialog(self, IDmessage=message["IDmessage"])
        if dlg.ShowModal() == wx.ID_OK:
            self.MAJ()
        dlg.Destroy()

    def Supprimer(self, event=None):
        message = self.GetSelectionMessage()
        if message is None:
            if event is not None:
                dlg = wx.MessageDialog(self, _(u"Vous n'avez sélectionné aucun message à supprimer dans la liste !"), _(u"Erreur de saisie"), wx.OK | wx.ICON_EXCLAMATION)
                dlg.ShowModal()
                dlg.Destroy()
            return
        dlg = wx.MessageDialog(self, _(u"Souhaitez-vous vraiment supprimer ce message ?"), _(u"Suppression"), wx.YES_NO | wx.NO_DEFAULT | wx.CANCEL | wx.ICON_INFORMATION)
        if dlg.ShowModal() == wx.ID_YES:
            DB = GestionDB.DB()
            DB.ReqDEL("portail_messages", "IDmessage", message["IDmessage"])
            DB.Close()
            self.MAJ()
        dlg.Destroy()


class CTRL(wx.Panel):
    """Gestion des messages du portail avec barre d'actions Repens."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        self.parent = parent
        self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))

        self.ctrl_messages = ListBox_Messages(self)
        self.bouton_ajouter_message = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Ajouter"),
            icone="add",
            variante="primaire",
            tooltip=_(u"Ajouter un message sur la page d'accueil du portail"),
        )
        self.bouton_modifier_message = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Modifier"),
            icone="edit",
            variante="secondaire",
            tooltip=_(u"Modifier le message sélectionné"),
        )
        self.bouton_supprimer_message = CTRL_ActionRepens.CTRL(
            self,
            label=_(u"Supprimer"),
            icone="delete",
            variante="danger",
            tooltip=_(u"Supprimer le message sélectionné"),
        )

        self.__do_layout()
        self.Bind(wx.EVT_BUTTON, self.OnAjouterMessage, self.bouton_ajouter_message)
        self.Bind(wx.EVT_BUTTON, self.OnModifierMessage, self.bouton_modifier_message)
        self.Bind(wx.EVT_BUTTON, self.OnSupprimerMessage, self.bouton_supprimer_message)

    def __do_layout(self):
        marge = UTILS_UIMetrics.spacing(2)
        espace = UTILS_UIMetrics.spacing(1)

        actions = wx.BoxSizer(wx.HORIZONTAL)
        actions.Add(self.bouton_ajouter_message, 0, wx.RIGHT, espace)
        actions.Add(self.bouton_modifier_message, 0, wx.RIGHT, espace)
        actions.Add(self.bouton_supprimer_message, 0)
        actions.AddStretchSpacer(1)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(actions, 0, wx.EXPAND | wx.BOTTOM, marge)
        principal.Add(self.ctrl_messages, 1, wx.EXPAND)
        self.SetSizer(principal)
        self.SetMinSize((UTILS_UIMetrics.px(320), UTILS_UIMetrics.px(220)))
        self.Layout()

    def OnAjouterMessage(self, event):
        self.ctrl_messages.Ajouter()

    def OnModifierMessage(self, event):
        self.ctrl_messages.Modifier()

    def OnSupprimerMessage(self, event):
        self.ctrl_messages.Supprimer(event)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        self.ctrl = CTRL(panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.ALL | wx.EXPAND, UTILS_UIMetrics.spacing(2))
        panel.SetSizer(sizer)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(panel, 1, wx.EXPAND)
        self.SetSizer(principal)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 400))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
