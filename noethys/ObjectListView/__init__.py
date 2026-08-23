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


def _appliquer_repens(ctrl):
    """Réapplique la politique de liste existante sans dépendance métier."""
    try:
        from Utils import UTILS_StyleRepens as Style
        Style.appliquer_liste_riche(ctrl)
    except Exception:
        # La bibliothèque reste importable isolément, notamment par les outils
        # de packaging et de diagnostic qui ne chargent pas toute l'application.
        pass


class ObjectListView(_ObjectListView):
    """ObjectListView historique avec rappel tardif de la palette Repens."""

    def __init__(self, *args, **kwargs):
        _ObjectListView.__init__(self, *args, **kwargs)
        _appliquer_repens(self)

    def SetObjects(self, *args, **kwargs):
        # Les anciens écrans assignent souvent leur zebra juste avant SetObjects.
        # Le rappel utilise la politique prudente du moteur global : une couleur
        # métier explicite n'est donc jamais remplacée.
        _appliquer_repens(self)
        return _ObjectListView.SetObjects(self, *args, **kwargs)


class VirtualObjectListView(_VirtualObjectListView):
    def __init__(self, *args, **kwargs):
        _VirtualObjectListView.__init__(self, *args, **kwargs)
        _appliquer_repens(self)

    def SetObjects(self, *args, **kwargs):
        _appliquer_repens(self)
        return _VirtualObjectListView.SetObjects(self, *args, **kwargs)


class FastObjectListView(_FastObjectListView):
    def __init__(self, *args, **kwargs):
        _FastObjectListView.__init__(self, *args, **kwargs)
        _appliquer_repens(self)

    def SetObjects(self, *args, **kwargs):
        _appliquer_repens(self)
        return _FastObjectListView.SetObjects(self, *args, **kwargs)


class GroupListView(_GroupListView):
    def __init__(self, *args, **kwargs):
        _GroupListView.__init__(self, *args, **kwargs)
        _appliquer_repens(self)

    def SetObjects(self, *args, **kwargs):
        _appliquer_repens(self)
        return _GroupListView.SetObjects(self, *args, **kwargs)

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
