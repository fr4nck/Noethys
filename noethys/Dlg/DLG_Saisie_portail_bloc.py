#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Licence:          GNU GPL
#------------------------------------------------------------------------

"""Composition extensible de l'éditeur de blocs Connecthys.

L'implémentation historique du dialogue reste dans
``DLG_Saisie_portail_bloc_core``. Ce module conserve le point d'import public
historique et compose la palette de blocs avec les extensions Noethys.

Les codes des blocs enrichis sont uniquement des codes d'interface : ils sont
convertis en catégories Connecthys historiques au moment de la sauvegarde.
"""

import Chemins
import wx
import wx.lib.agw.labelbook as LB

from Utils.UTILS_Traduction import _
from Utils import UTILS_Portail_blocs
from Ctrl import CTRL_Portail_contenu_externe
from Ctrl import CTRL_Portail_tarifs
from Dlg import DLG_Saisie_portail_bloc_core as _core
from Dlg.DLG_Saisie_portail_bloc_core import *


class CTRL_Parametres(LB.FlatImageBook):
    """Palette de blocs : types historiques et extensions indépendantes."""

    def __init__(self, parent):
        LB.FlatImageBook.__init__(self, parent, id=-1, agwStyle=LB.INB_BORDER | LB.INB_LEFT)
        self.parent = parent

        self.listePages = [
            (_("bloc_texte"), _(u"Texte"), _core.PAGE_Texte(self), wx.Bitmap(Chemins.GetStaticPath('Images/32x32/Texte_bloc.png'), wx.BITMAP_TYPE_PNG)),
            (UTILS_Portail_blocs.CODE_CONTENU_EXTERNE, _(u"Contenu externe"), CTRL_Portail_contenu_externe.CTRL(self), wx.Bitmap(Chemins.GetStaticPath('Images/32x32/Apercu.png'), wx.BITMAP_TYPE_PNG)),
            (UTILS_Portail_blocs.CODE_TARIFS, _(u"Tarifs Noethys"), CTRL_Portail_tarifs.CTRL(self), wx.Bitmap(Chemins.GetStaticPath('Images/32x32/Euro.png'), wx.BITMAP_TYPE_PNG)),
            (_("bloc_onglets"), _(u"Onglets"), _core.PAGE_Onglets(self), wx.Bitmap(Chemins.GetStaticPath('Images/32x32/Onglets.png'), wx.BITMAP_TYPE_PNG)),
            (_("bloc_blog"), _(u"Blog"), _core.PAGE_Blog(self), wx.Bitmap(Chemins.GetStaticPath('Images/32x32/Blog.png'), wx.BITMAP_TYPE_PNG)),
            (_("bloc_calendrier"), _(u"Calendrier"), _core.PAGE_Calendrier(self), wx.Bitmap(Chemins.GetStaticPath('Images/32x32/Calendrier.png'), wx.BITMAP_TYPE_PNG)),
            (_("bloc_trombi"), _(u"Portraits"), _core.PAGE_Trombi(self), wx.Bitmap(Chemins.GetStaticPath('Images/32x32/Trombi.png'), wx.BITMAP_TYPE_PNG)),
        ]

        images = wx.ImageList(32, 32)
        for code, label, ctrl, image in self.listePages:
            images.Add(image)
        self.AssignImageList(images)

        for index, (code, label, ctrl, image) in enumerate(self.listePages):
            self.AddPage(ctrl, label, imageId=index)

        self.SetSelection(0)

    def GetPageByCode(self, code=""):
        for codetemp, label, ctrl, image in self.listePages:
            if code == codetemp:
                return ctrl
        return None

    def SetPageByCode(self, code=""):
        for index, (codetemp, label, ctrl, image) in enumerate(self.listePages):
            if code == codetemp:
                self.SetSelection(index)
                return True
        return False

    def GetPageActive(self):
        return self.listePages[self.GetSelection()][2]

    def GetCodePageActive(self):
        return self.listePages[self.GetSelection()][0]

    def Validation(self):
        return self.GetPageActive().Validation()

    def GetParametres(self):
        dictParametres = self.GetPageActive().GetParametres()
        code = self.GetCodePageActive()
        dictParametres["categorie"] = UTILS_Portail_blocs.categorie_persistante(code)
        return dictParametres

    def SetParametres(self, dictParametres=None):
        dictParametres = dictParametres or {}
        code = UTILS_Portail_blocs.detecter_code(dictParametres)
        if not self.SetPageByCode(code):
            self.SetPageByCode(_("bloc_texte"))
        self.GetPageActive().SetParametres(dictParametres)


# Le dialogue historique résout CTRL_Parametres dans son module au moment de
# l'instanciation. On lui fournit donc la palette composée ci-dessus tout en
# conservant son code de sauvegarde éprouvé et son chemin d'import public.
_core.CTRL_Parametres = CTRL_Parametres
Dialog = _core.Dialog
