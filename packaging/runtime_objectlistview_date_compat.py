"""Sécurise l'éditeur de dates historique d'ObjectListView.

L'ancien contrôle suppose que toute valeur non vide possède directement les
attributs ``day``, ``month`` et ``year``. Les chaînes partielles, dates wx
invalides ou valeurs inattendues doivent être traitées comme une absence de date
plutôt que provoquer un crash d'interface.
"""
from __future__ import annotations

import datetime

import wx

try:
    from ObjectListView import CellEditor
except Exception as err:
    print("Compatibilité DateEditor non initialisée : %s" % err)
else:
    _original_get_value = CellEditor.DateEditor.GetValue

    def _set_value_compat(self, value):
        if isinstance(value, datetime.datetime):
            value = value.date()

        if isinstance(value, datetime.date):
            dt = wx.DateTime()
            dt.Set(int(value.day), int(value.month) - 1, int(value.year))
        else:
            # Une valeur vide, partielle ou inattendue ne doit pas faire planter
            # l'éditeur : le contrôle revient à la date du jour.
            dt = wx.DateTime.Today()

        return wx.adv.DatePickerCtrl.SetValue(self, dt)

    def _get_value_compat(self):
        try:
            value = _original_get_value(self)
        except (AttributeError, TypeError, ValueError, OverflowError):
            return None
        return value if isinstance(value, datetime.date) else None

    CellEditor.DateEditor.SetValue = _set_value_compat
    CellEditor.DateEditor.GetValue = _get_value_compat
