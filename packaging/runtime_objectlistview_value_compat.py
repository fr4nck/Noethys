"""Normalise les valeurs vides des éditeurs ObjectListView.

Les anciens éditeurs numériques et de date peuvent transmettre ``None`` à
``wx.TextCtrl.SetValue``. wxPython Phoenix exige une chaîne. La correction est
limitée à l'éditeur texte de base et ne modifie pas la valeur métier retournée.
"""
from __future__ import annotations

from ObjectListView import CellEditor


_original_set_value = CellEditor.BaseCellTextEditor.SetValue


def _set_value_compat(self, value):
    if value is None:
        value = ""
    elif not isinstance(value, str):
        value = str(value)
    return _original_set_value(self, value)


CellEditor.BaseCellTextEditor.SetValue = _set_value_compat
