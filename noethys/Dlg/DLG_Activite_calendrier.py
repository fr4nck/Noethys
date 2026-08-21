#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:          Licence GNU GPL
#-----------------------------------------------------------

import wx

from Ctrl import CTRL_ActionRepens
from Ctrl import CTRL_Calendrier_ouvertures
from Ctrl import CTRL_FenetreRepens
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


class Panel(wx.Panel):
    """Calendrier d'activité utilisant la section et les actions Repens communes."""

    def __init__(self, parent, IDactivite=None, nouvelleActivite=False):
        wx.Panel.__init__(self, parent, id=-1, name="panel_unites", style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        self.parent = parent
        self.IDactivite = IDactivite
        Style.appliquer_fenetre(self, "surface")

        self.section_ouvertures = CTRL_FenetreRepens.Section(
            self,
            titre=_(u"Calendrier des ouvertures et des évènements"),
            sous_titre=_(u"Visualisez les périodes puis ouvrez l'éditeur pour modifier les ouvertures et évènements."),
        )
        parent_section = self.section_ouvertures.GetContenu()

        self.bouton_ouvertures_modifier = CTRL_ActionRepens.CTRL(
            parent_section,
            label=_(u"Modifier le calendrier"),
            icone="calendar",
            variante="primaire",
            tooltip=_(u"Modifier le calendrier des ouvertures et des évènements"),
        )

        self.ctrl_ouvertures = CTRL_Calendrier_ouvertures.Calendrier(parent_section, IDactivite=self.IDactivite)
        self.ctrl_ouvertures.Initialisation()
        try:
            Style.appliquer_fenetre(self.ctrl_ouvertures, "surface_container_lowest")
        except Exception:
            pass
        self.ctrl_ouvertures.SetToolTip(wx.ToolTip(_(u"Calendrier des ouvertures et des évènements")))

        barre = wx.BoxSizer(wx.HORIZONTAL)
        barre.AddStretchSpacer(1)
        barre.Add(self.bouton_ouvertures_modifier, 0, wx.ALIGN_CENTER_VERTICAL)

        contenu = self.section_ouvertures.GetSizerContenu()
        contenu.Add(barre, 0, wx.EXPAND | wx.BOTTOM, Style.espace(2))
        contenu.Add(self.ctrl_ouvertures, 1, wx.EXPAND)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(self.section_ouvertures, 1, wx.EXPAND | wx.ALL, Style.espace(2))
        self.SetSizer(principal)
        self.Layout()

        self.bouton_ouvertures_modifier.Bind(wx.EVT_BUTTON, self.OnBoutonOuvertures_Modifier)

    def OnBoutonOuvertures_Modifier(self, event):
        from Dlg import DLG_Ouvertures
        dlg = DLG_Ouvertures.Dialog(self, IDactivite=self.IDactivite)
        if dlg.ShowModal() == wx.ID_OK:
            self.ctrl_ouvertures.MAJ()
        dlg.Destroy()

    def Validation(self):
        return True

    def Sauvegarde(self):
        pass


class MyFrame(CTRL_FenetreRepens.Frame):
    def __init__(self, *args, **kwds):
        CTRL_FenetreRepens.Frame.__init__(self, None, titre=_(u"Calendrier d'activité"), taille=(760, 540))
        self.ctrl = Panel(self.GetContenu(), IDactivite=1)
        self.AjouterContenu(self.ctrl, 1, wx.EXPAND)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame()
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
