"""Normalise les largeurs de colonnes pour wxPython Phoenix.

L'ancien ObjectListView transmet parfois des valeurs flottantes via
``ListItem.m_width`` ou ``SetColumnWidth``. Phoenix exige des entiers stricts.
Ce hook limite la correction à cette frontière d'API, sans modifier les écrans.
"""
from __future__ import annotations

import wx

_original_set_column_width = wx.ListCtrl.SetColumnWidth
_original_insert_column_info = getattr(wx.ListCtrl, "InsertColumnInfo", None)


def _set_column_width_compat(self, col, width):
    return _original_set_column_width(self, int(col), int(width))


wx.ListCtrl.SetColumnWidth = _set_column_width_compat


if _original_insert_column_info is not None:
    def _insert_column_info_compat(self, col, item):
        try:
            item.SetWidth(int(item.GetWidth()))
        except Exception:
            try:
                item.m_width = int(item.m_width)
            except Exception:
                pass
        return _original_insert_column_info(self, int(col), item)

    wx.ListCtrl.InsertColumnInfo = _insert_column_info_compat
