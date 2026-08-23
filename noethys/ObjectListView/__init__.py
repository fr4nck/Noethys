# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         ObjectListView module initialization
# Author:       Phillip Piper
# Created:      29 February 2008
# Copyright:    (c) 2008 by Phillip Piper
# License:      wxWindows license
#----------------------------------------------------------------------------
# Change log:
# 2008/08/02  JPP   Added list printing material
# 2008/07/24  JPP   Added list group related material
# 2008/06/19  JPP   Added sort event related material
# 2008/04/11  JPP   Initial Version

"""
An ObjectListView provides a more convienent and powerful interface to a ListCtrl.

Noethys conserve cette bibliothèque historique mais réapplique sa politique de
palette Repens aux moments où les écrans anciens peuvent encore restaurer leurs
valeurs de zebra. Le wrapper reste volontairement mince : il ne modifie ni les
colonnes, ni les renderers, ni les éditeurs, ni les données.
"""

__version__ = '1.3.2'
__copyright__ = "Copyright (c) 2008 Phillip Piper (phillip_piper@bigfoot.com)"

from . ObjectListView import ObjectListView as _ObjectListView
from . ObjectListView import VirtualObjectListView as _VirtualObjectListView
from . ObjectListView import ColumnDefn
from . ObjectListView import FastObjectListView as _FastObjectListView
from . ObjectListView import GroupListView as _GroupListView
from . ObjectListView import ListGroup, BatchedUpdate, NamedImageList
from . OLVEvent import CellEditFinishedEvent, CellEditFinishingEvent, CellEditStartedEvent, CellEditStartingEvent, SortEvent
from . OLVEvent import EVT_CELL_EDIT_STARTING, EVT_CELL_EDIT_STARTED, EVT_CELL_EDIT_FINISHING, EVT_CELL_EDIT_FINISHED, EVT_SORT
from . OLVEvent import EVT_COLLAPSING, EVT_COLLAPSED, EVT_EXPANDING, EVT_EXPANDED, EVT_GROUP_CREATING, EVT_GROUP_SORT, EVT_ITEM_CHECKED
from . CellEditor import CellEditorRegistry, MakeAutoCompleteTextBox, MakeAutoCompleteComboBox
from . ListCtrlPrinter import ListCtrlPrinter, ReportFormat, BlockFormat, LineDecoration, RectangleDecoration, ImageDecoration

from . import Filter


_MESSAGE_VIDE_VENDOR = "This list is empty"


def _normaliser_message_vide(ctrl):
    """Remplace uniquement le libellé anglais livré par la bibliothèque."""
    try:
        message = ctrl.stEmptyListMsg
        if message.GetLabel() != _MESSAGE_VIDE_VENDOR:
            return
        from Utils.UTILS_Traduction import _
        message.SetLabel(_(u"Aucun élément"))
    except Exception:
        pass


def _synchroniser_etat_vide(ctrl):
    """Restaure l'état vide natif après les anciennes rustines Phoenix.

    CTRL_ObjectListView masquait historiquement le message à chaque resize pour
    contourner un artefact visuel désormais traité par la palette Repens. La
    visibilité suit donc de nouveau le contenu réel de la liste.
    """
    try:
        message = ctrl.stEmptyListMsg
    except Exception:
        return

    try:
        vide = ctrl.GetItemCount() == 0
    except Exception:
        try:
            vide = len(ctrl.GetObjects()) == 0
        except Exception:
            return

    try:
        message.Show(vide)
        if vide:
            message.Raise()
            message.Refresh()
    except Exception:
        pass


def _lier_etat_vide(ctrl):
    """Réapplique l'état vide après resize sans remplacer le handler historique."""
    if getattr(ctrl, "_repens_etat_vide_lie", False):
        return
    try:
        import wx

        ctrl._repens_etat_vide_lie = True

        def _apres_resize(event):
            event.Skip()
            try:
                wx.CallAfter(_synchroniser_etat_vide, ctrl)
            except Exception:
                _synchroniser_etat_vide(ctrl)

        ctrl.Bind(wx.EVT_SIZE, _apres_resize)
    except Exception:
        pass


def _appliquer_repens(ctrl):
    """Réapplique la politique de liste existante sans dépendance métier."""
    try:
        from Utils import UTILS_StyleRepens as Style
        Style.appliquer_liste_riche(ctrl)
    except Exception:
        # La bibliothèque reste importable isolément, notamment par les outils
        # de packaging et de diagnostic qui ne chargent pas toute l'application.
        pass
    _normaliser_message_vide(ctrl)
    _lier_etat_vide(ctrl)


def _apres_set_objects(ctrl, resultat):
    _synchroniser_etat_vide(ctrl)
    return resultat


class ObjectListView(_ObjectListView):
    """ObjectListView historique avec rappel tardif de la palette Repens."""

    def __init__(self, *args, **kwargs):
        _ObjectListView.__init__(self, *args, **kwargs)
        _appliquer_repens(self)
        _synchroniser_etat_vide(self)

    def SetObjects(self, *args, **kwargs):
        # Les anciens écrans assignent souvent leur zebra juste avant SetObjects.
        # Le rappel utilise la politique prudente du moteur global : une couleur
        # métier explicite n'est donc jamais remplacée.
        _appliquer_repens(self)
        resultat = _ObjectListView.SetObjects(self, *args, **kwargs)
        return _apres_set_objects(self, resultat)


class VirtualObjectListView(_VirtualObjectListView):
    def __init__(self, *args, **kwargs):
        _VirtualObjectListView.__init__(self, *args, **kwargs)
        _appliquer_repens(self)
        _synchroniser_etat_vide(self)

    def SetObjects(self, *args, **kwargs):
        _appliquer_repens(self)
        resultat = _VirtualObjectListView.SetObjects(self, *args, **kwargs)
        return _apres_set_objects(self, resultat)


class FastObjectListView(_FastObjectListView):
    def __init__(self, *args, **kwargs):
        _FastObjectListView.__init__(self, *args, **kwargs)
        _appliquer_repens(self)
        _synchroniser_etat_vide(self)

    def SetObjects(self, *args, **kwargs):
        _appliquer_repens(self)
        resultat = _FastObjectListView.SetObjects(self, *args, **kwargs)
        return _apres_set_objects(self, resultat)


class GroupListView(_GroupListView):
    def __init__(self, *args, **kwargs):
        _GroupListView.__init__(self, *args, **kwargs)
        _appliquer_repens(self)
        _synchroniser_etat_vide(self)

    def SetObjects(self, *args, **kwargs):
        _appliquer_repens(self)
        resultat = _GroupListView.SetObjects(self, *args, **kwargs)
        return _apres_set_objects(self, resultat)

    def _InitializeImages(self):
        # CTRL_ObjectListView règle historiquement ses couleurs de groupes juste
        # avant cet appel. Le rappel ne remplace que le bleu/noir legacy reconnu
        # par UTILS_Interface et conserve toute personnalisation métier.
        _appliquer_repens(self)
        return _GroupListView._InitializeImages(self)


__all__ = [
    "BatchedUpdate",
    "BlockFormat",
    "CellEditFinishedEvent",
    "CellEditFinishingEvent",
    "CellEditorRegistry",
    "CellEditStartedEvent",
    "CellEditStartingEvent",
    "ColumnDefn",
    "EVT_CELL_EDIT_FINISHED",
    "EVT_CELL_EDIT_FINISHING",
    "EVT_CELL_EDIT_STARTED",
    "EVT_CELL_EDIT_STARTING",
    "EVT_COLLAPSED",
    "EVT_COLLAPSING",
    "EVT_EXPANDED",
    "EVT_EXPANDING",
    "EVT_GROUP_CREATING",
    "EVT_GROUP_SORT",
    "EVT_SORT",
    "Filter",
    "FastObjectListView",
    "GroupListView",
    "ListGroup",
    "ImageDecoration",
    "MakeAutoCompleteTextBox",
    "MakeAutoCompleteComboBox",
    "ListGroup",
    "ObjectListView",
    "ListCtrlPrinter",
    "RectangleDecoration",
    "ReportFormat",
    "SortEvent",
    "VirtualObjectListView",
]
