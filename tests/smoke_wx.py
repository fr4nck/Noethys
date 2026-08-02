#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Smoke test wx.App — vérifie la création et la destruction d'une application
wxPython sans interface visible, sans base de données ni données utilisateur.

Doit être exécuté sur un runner Windows (pas de DISPLAY requis sous Windows).
"""
import wx

app = wx.App(False)  # redirect=False : pas de redirection stdout/stderr
print("wx.App créé, version :", wx.version())
app.Destroy()
print("smoke_wx OK")
