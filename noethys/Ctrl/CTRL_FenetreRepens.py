#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Gabarits communs de fenêtres Repens Design.

L'objectif est de sortir la géométrie et le chrome des écrans métier. Une
fenêtre migrée ne choisit plus ses marges, son fond, son footer ou le style de
ses sections : elle ajoute du contenu dans ce shell commun.
"""

import wx

from Ctrl import CTRL_ActionRepens
from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_SurfaceRepens
from Ctrl import CTRL_TexteRepens
from Utils import UTILS_StyleRepens as Style


STYLE_DIALOGUE = (
    wx.DEFAULT_DIALOG_STYLE
    | wx.RESIZE_BORDER
    | wx.MAXIMIZE_BOX
    | wx.MINIMIZE_BOX
)


def _taille_bornee(fenetre, taille, marge=0.92):
    """Adapte une taille de référence au DPI et à la zone de travail."""
    largeur = Style.px(taille[0])
    hauteur = Style.px(taille[1])
    try:
        index = wx.Display.GetFromWindow(fenetre)
        if index == wx.NOT_FOUND:
            index = 0
        zone = wx.Display(index).GetClientArea()
        max_l = max(Style.px(320), int(zone.width * marge))
        max_h = max(Style.px(240), int(zone.height * marge))
        largeur = min(largeur, max_l)
        hauteur = min(hauteur, max_h)
    except Exception:
        pass
    return wx.Size(max(Style.px(320), largeur), max(Style.px(240), hauteur))


class Section(CTRL_SurfaceRepens.CTRL):
    """Section métier commune : H2, sous-titre optionnel et contenu libre."""

    def __init__(self, parent, titre=u"", sous_titre=u"", role_fond="surface_container_low"):
        CTRL_SurfaceRepens.CTRL.__init__(
            self,
            parent,
            role_fond=role_fond,
            role_contour="outline_variant",
            rayon=9,
            padding=8,
        )
        self.titre = titre or u""
        self.sous_titre = sous_titre or u""

        self.label_titre = None
        self.label_sous_titre = None
        if self.titre:
            self.label_titre = CTRL_TexteRepens.H2(
                self,
                label=self.titre,
                role_texte="on_surface",
                role_fond=role_fond,
                wrap=True,
            )
        if self.sous_titre:
            self.label_sous_titre = CTRL_TexteRepens.CTRL(
                self,
                label=self.sous_titre,
                role="caption",
                role_texte="on_surface_variant",
                role_fond=role_fond,
                wrap=True,
            )

        self.panel_contenu = wx.Panel(self, -1, style=wx.BORDER_NONE | wx.TAB_TRAVERSAL)
        Style.appliquer_fenetre(self.panel_contenu, role_fond)
        self.sizer_contenu = wx.BoxSizer(wx.VERTICAL)
        self.panel_contenu.SetSizer(self.sizer_contenu)

        principal = wx.BoxSizer(wx.VERTICAL)
        marge = self.GetPadding()
        if self.label_titre is not None:
            principal.Add(self.label_titre, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, marge)
        if self.label_sous_titre is not None:
            principal.Add(
                self.label_sous_titre,
                0,
                wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP,
                marge,
            )
        principal.Add(self.panel_contenu, 1, wx.EXPAND | wx.ALL, marge)
        self.SetSizer(principal)

    def GetContenu(self):
        return self.panel_contenu

    def GetSizerContenu(self):
        return self.sizer_contenu

    def Ajouter(self, ctrl, proportion=0, flag=wx.EXPAND, border=0):
        self.sizer_contenu.Add(ctrl, proportion, flag, border)
        self.Layout()
        return ctrl

    def AjouterTitre(self, titre, niveau="h3", role_texte="on_surface"):
        """Ajoute un titre sémantique interne, H3 par défaut."""
        if niveau not in CTRL_TexteRepens.ROLES_TEXTE:
            niveau = "h3"
        ctrl = CTRL_TexteRepens.CTRL(
            self.panel_contenu,
            label=titre,
            role=niveau,
            role_texte=role_texte,
            role_fond=self.role_fond,
            wrap=True,
        )
        if self.sizer_contenu.GetItemCount() > 0:
            self.sizer_contenu.AddSpacer(Style.espace(2))
        self.sizer_contenu.Add(ctrl, 0, wx.EXPAND | wx.BOTTOM, Style.espace(1))
        self.Layout()
        return ctrl


class BarreActions(wx.Panel):
    """Footer commun : actions secondaires à gauche, principales à droite."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1, style=wx.BORDER_NONE | wx.TAB_TRAVERSAL)
        Style.appliquer_fenetre(self, "surface_container")
        self.sizer_gauche = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_droite = wx.BoxSizer(wx.HORIZONTAL)

        principal = wx.BoxSizer(wx.HORIZONTAL)
        principal.Add(self.sizer_gauche, 0, wx.ALIGN_CENTER_VERTICAL)
        principal.AddStretchSpacer(1)
        principal.Add(self.sizer_droite, 0, wx.ALIGN_CENTER_VERTICAL)
        marge = Style.espace(2)
        exterieur = wx.BoxSizer(wx.VERTICAL)
        exterieur.Add(principal, 1, wx.EXPAND | wx.ALL, marge)
        self.SetSizer(exterieur)
        self.SetMinSize((-1, Style.cible_action("standard") + (marge * 2)))

    def AjouterAction(
        self,
        label,
        callback=None,
        icone=None,
        variante="secondaire",
        alignement="droite",
        tooltip=None,
        compact=True,
    ):
        bouton = CTRL_ActionRepens.CTRL(
            self,
            label=label,
            icone=icone,
            variante=variante,
            tooltip=tooltip,
            compact=compact,
        )
        if callback is not None:
            bouton.Bind(wx.EVT_BUTTON, callback)
        sizer = self.sizer_gauche if alignement == "gauche" else self.sizer_droite
        if sizer.GetItemCount() > 0:
            sizer.AddSpacer(Style.espace(1))
        sizer.Add(bouton, 0, wx.ALIGN_CENTER_VERTICAL)
        self.Layout()
        return bouton


class Dialog(wx.Dialog):
    """Dialogue Repens standard avec H1, sections H2 et footer partagés."""

    def __init__(
        self,
        parent,
        titre=u"",
        intro=u"",
        nomImage=None,
        taille=(760, 560),
        taille_min=(520, 360),
        style=STYLE_DIALOGUE,
        afficher_bandeau=True,
        afficher_footer=True,
    ):
        wx.Dialog.__init__(self, parent, -1, title=titre, style=style)
        self.parent = parent
        self.titre_repens = titre or u""
        self._sections_ajoutees = 0
        Style.appliquer_fenetre(self, "surface")

        self.ctrl_bandeau = None
        if afficher_bandeau:
            self.ctrl_bandeau = CTRL_Bandeau.Bandeau(
                self,
                titre=titre,
                texte=intro,
                nomImage=nomImage,
            )

        self.panel_contenu = wx.Panel(self, -1, style=wx.BORDER_NONE | wx.TAB_TRAVERSAL)
        Style.appliquer_fenetre(self.panel_contenu, "surface")
        self.sizer_contenu = wx.BoxSizer(wx.VERTICAL)
        self.panel_contenu.SetSizer(self.sizer_contenu)

        self.separateur_footer = None
        self.barre_actions = None
        if afficher_footer:
            self.separateur_footer = wx.StaticLine(self, -1)
            try:
                self.separateur_footer.SetForegroundColour(Style.couleur("outline_variant"))
                self.separateur_footer.SetBackgroundColour(Style.couleur("outline_variant"))
            except Exception:
                pass
            self.barre_actions = BarreActions(self)

        principal = wx.BoxSizer(wx.VERTICAL)
        if self.ctrl_bandeau is not None:
            principal.Add(self.ctrl_bandeau, 0, wx.EXPAND)
        principal.Add(
            self.panel_contenu,
            1,
            wx.EXPAND | wx.ALL,
            Style.espace(3),
        )
        if self.separateur_footer is not None:
            principal.Add(self.separateur_footer, 0, wx.EXPAND)
        if self.barre_actions is not None:
            principal.Add(self.barre_actions, 0, wx.EXPAND)
        self.SetSizer(principal)

        taille_min_wx = _taille_bornee(self, taille_min, marge=0.88)
        taille_wx = _taille_bornee(self, taille, marge=0.92)
        self.SetMinSize(taille_min_wx)
        self.SetSize(taille_wx)
        self.Layout()
        try:
            self.CentreOnParent()
        except Exception:
            self.CentreOnScreen()

    def GetContenu(self):
        return self.panel_contenu

    def GetSizerContenu(self):
        return self.sizer_contenu

    def AjouterSection(self, titre=u"", sous_titre=u"", proportion=0, role_fond="surface_container_low"):
        if self._sections_ajoutees > 0:
            self.sizer_contenu.AddSpacer(Style.espace(2))
        section = Section(
            self.panel_contenu,
            titre=titre,
            sous_titre=sous_titre,
            role_fond=role_fond,
        )
        self.sizer_contenu.Add(section, proportion, wx.EXPAND)
        self._sections_ajoutees += 1
        self.panel_contenu.Layout()
        return section

    def AjouterAction(
        self,
        label,
        callback=None,
        icone=None,
        variante="secondaire",
        alignement="droite",
        tooltip=None,
        compact=True,
    ):
        if self.barre_actions is None:
            return None
        return self.barre_actions.AjouterAction(
            label=label,
            callback=callback,
            icone=icone,
            variante=variante,
            alignement=alignement,
            tooltip=tooltip,
            compact=compact,
        )

    def AjouterContenu(self, ctrl, proportion=0, flag=wx.EXPAND, border=0):
        self.sizer_contenu.Add(ctrl, proportion, flag, border)
        self.panel_contenu.Layout()
        return ctrl

    def Finaliser(self):
        """Relance le layout après construction métier sans imposer de Fit()."""
        try:
            self.panel_contenu.Layout()
            self.Layout()
        except Exception:
            pass


class Frame(wx.Frame):
    """Frame Repens légère pour les outils non modaux."""

    def __init__(self, parent, titre=u"", taille=(960, 680), taille_min=(640, 420), style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self, parent, -1, title=titre, style=style)
        self.parent = parent
        Style.appliquer_fenetre(self, "surface")
        self.panel_contenu = wx.Panel(self, -1, style=wx.BORDER_NONE | wx.TAB_TRAVERSAL)
        Style.appliquer_fenetre(self.panel_contenu, "surface")
        self.sizer_contenu = wx.BoxSizer(wx.VERTICAL)
        self.panel_contenu.SetSizer(self.sizer_contenu)
        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(self.panel_contenu, 1, wx.EXPAND | wx.ALL, Style.espace(3))
        self.SetSizer(principal)
        self.SetMinSize(_taille_bornee(self, taille_min, marge=0.88))
        self.SetSize(_taille_bornee(self, taille, marge=0.94))
        self.Layout()

    def GetContenu(self):
        return self.panel_contenu

    def GetSizerContenu(self):
        return self.sizer_contenu

    def AjouterContenu(self, ctrl, proportion=0, flag=wx.EXPAND, border=0):
        self.sizer_contenu.Add(ctrl, proportion, flag, border)
        self.panel_contenu.Layout()
        return ctrl
