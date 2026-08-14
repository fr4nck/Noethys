"""Compatibilité légère avec les alias supprimés de wxPython Classic.

Noethys contient encore plusieurs appels historiques tels que ``wx.EmptyIcon``
ou ``wx.BitmapFromImage``. wxPython Phoenix fournit les constructeurs modernes ;
ce hook restaure uniquement les anciens noms attendus par l'application.
"""
from __future__ import annotations

import wx


if not hasattr(wx, "EmptyBitmap"):
    wx.EmptyBitmap = lambda width, height, depth=-1: wx.Bitmap(width, height, depth)

if not hasattr(wx, "EmptyIcon"):
    wx.EmptyIcon = wx.Icon

if not hasattr(wx, "EmptyImage"):
    wx.EmptyImage = wx.Image

if not hasattr(wx, "BitmapFromImage"):
    wx.BitmapFromImage = wx.Bitmap

if not hasattr(wx, "NewId"):
    wx.NewId = lambda: int(wx.NewIdRef())
