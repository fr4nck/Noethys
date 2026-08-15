#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-17 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import wx
import sys
from importlib import import_module


def _module_absent(exc, nom_module):
    """Indique si l'ImportError correspond bien au module demandé.

    Un ImportError levé par une dépendance *interne* au module doit remonter :
    le masquer puis essayer un autre module rend les diagnostics trompeurs et
    peut charger un module homonyme inattendu.
    """
    nom_absent = getattr(exc, "name", None)
    if nom_absent is None:
        # Compatibilité avec d'anciens ImportError qui n'exposent pas .name.
        return True
    return nom_absent == nom_module or nom_module.startswith(nom_absent + ".")


def Import(nom_module=""):
    # Essaye d'importer le nom qualifié demandé.
    try:
        return import_module(nom_module)
    except ImportError as exc:
        if not _module_absent(exc, nom_module):
            raise

    # Recherche si le module est déjà chargé.
    if nom_module in sys.modules:
        return sys.modules[nom_module]

    # Fallback historique : essaye le nom court uniquement lorsque le module
    # qualifié lui-même est absent. Une erreur interne au module court remonte.
    try:
        module_path, class_name = nom_module.rsplit('.', 1)
    except ValueError:
        return None

    try:
        return import_module(class_name)
    except ImportError as exc:
        if not _module_absent(exc, class_name):
            raise

    return None


class Menu(wx.Menu):
    def __init__(self, *args, **kwds):
        wx.Menu.__init__(self, *args, **kwds)

    def AppendItem(self, item):
        if 'phoenix' in wx.PlatformInfo:
            super(Menu, self).Append(item)
        else :
            super(Menu, self).AppendItem(item)

    def AppendMenu(self, *args, **kwds):
        if 'phoenix' in wx.PlatformInfo:
            super(Menu, self).Append(*args, **kwds)
        else :
            super(Menu, self).AppendMenu(*args, **kwds)


class ToolBar(wx.ToolBar):
    def __init__(self, *args, **kwds):
        wx.ToolBar.__init__(self, *args, **kwds)

    def AddLabelTool(self, *args, **kw):
        if 'phoenix' in wx.PlatformInfo:
            if "longHelp" in kw:
                kw.pop("longHelp")
            super(ToolBar, self).AddTool(*args, **kw)
        else :
            super(ToolBar, self).AddLabelTool(*args, **kw)

    def AddSimpleTool(self, *args, **kw):
        if 'phoenix' in wx.PlatformInfo:
            if "longHelp" in kw:
                kw.pop("longHelp")
            super(ToolBar, self).AddTool(*args, **kw)
        else :
            super(ToolBar, self).AddSimpleTool(*args, **kw)


if __name__ == "__main__":
    pass