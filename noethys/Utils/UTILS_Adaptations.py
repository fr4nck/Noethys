#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-17 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import time
import wx
from importlib import import_module


def _module_absent(exc, nom_module):
    """Indique si l'ImportError correspond bien au module demandé.

    Un ImportError levé par une dépendance *interne* au module doit remonter :
    le masquer puis essayer un autre module rend les diagnostics trompeurs et
    peut charger un module homonyme inattendu.
    """
    nom_absent = getattr(exc, "name", None)
    if nom_absent is None:
        return True
    return nom_absent == nom_module or nom_module.startswith(nom_absent + ".")


def Import(nom_module=""):
    """Importe un module en conservant le fallback historique par nom court."""
    if not nom_module:
        return None

    candidats = [nom_module]
    if "." in nom_module:
        nom_court = nom_module.rsplit(".", 1)[1]
        if nom_court != nom_module:
            candidats.append(nom_court)

    for candidat in candidats:
        try:
            return import_module(candidat)
        except ImportError as exc:
            if not _module_absent(exc, candidat):
                raise

    return None


def _InstallerDoubleClicObjectListView():
    """Fiabilise l'activation par double-clic des ObjectListView sous Phoenix."""
    if "phoenix" not in wx.PlatformInfo or wx.Platform != "__WXMSW__":
        return

    try:
        import ObjectListView as OLV
    except ImportError:
        return

    classe = getattr(OLV, "ObjectListView", None)
    if classe is None or getattr(classe, "_noethys_double_clic_corrige", False):
        return

    bind_original = classe.Bind
    double_clic_original = classe._HandleLeftClickOrDoubleClick
    type_activation = getattr(wx.EVT_LIST_ITEM_ACTIVATED, "typeId", None)

    def Bind(self, event, handler, source=None, id=wx.ID_ANY, id2=wx.ID_ANY):
        type_event = getattr(event, "typeId", None)
        if type_activation is not None and type_event == type_activation:
            compteur = getattr(self, "_noethys_compteur_handlers_activation", 0) + 1
            self._noethys_compteur_handlers_activation = compteur
            cle_handler = compteur

            def handler_activation(evt, _handler=handler, _cle=cle_handler):
                index = -1
                try:
                    index = evt.GetIndex()
                except Exception:
                    pass

                limite = getattr(self, "_noethys_double_clic_limite", 0.0)
                index_double = getattr(self, "_noethys_double_clic_index", -2)
                if time.monotonic() <= limite and index in (-1, index_double):
                    deja_vus = getattr(self, "_noethys_double_clic_handlers_vus", None)
                    if deja_vus is None:
                        deja_vus = set()
                        self._noethys_double_clic_handlers_vus = deja_vus
                    if _cle in deja_vus:
                        return
                    deja_vus.add(_cle)

                return _handler(evt)

            handler = handler_activation

        return bind_original(self, event, handler, source=source, id=id, id2=id2)

    def _EmettreActivation(self, index):
        try:
            if index < 0 or index >= self.GetItemCount():
                return
        except Exception:
            return

        type_evt = getattr(wx, "wxEVT_LIST_ITEM_ACTIVATED", None)
        if type_evt is None:
            type_evt = getattr(wx, "wxEVT_COMMAND_LIST_ITEM_ACTIVATED", None)
        if type_evt is None:
            return

        evt = wx.ListEvent(type_evt, self.GetId())
        evt.SetEventObject(self)
        try:
            evt.SetIndex(index)
        except Exception:
            try:
                evt.Index = index
            except Exception:
                pass
        self.GetEventHandler().ProcessEvent(evt)

    def _HandleLeftClickOrDoubleClick(self, evt):
        est_double = False
        index = -1
        try:
            est_double = evt.LeftDClick()
        except Exception:
            pass

        resultat = double_clic_original(self, evt)
        if not est_double:
            return resultat

        try:
            if self.cellEditMode != self.CELLEDIT_NONE:
                return resultat
        except Exception:
            return resultat

        try:
            hit = self.HitTest(evt.GetPosition())
            if isinstance(hit, tuple):
                index = hit[0]
            else:
                index = hit
        except Exception:
            index = -1

        if index is None or index == wx.NOT_FOUND or index < 0:
            return resultat

        self._noethys_double_clic_index = index
        self._noethys_double_clic_limite = time.monotonic() + 0.35
        self._noethys_double_clic_handlers_vus = set()
        wx.CallAfter(_EmettreActivation, self, index)
        return resultat

    classe.Bind = Bind
    classe._HandleLeftClickOrDoubleClick = _HandleLeftClickOrDoubleClick
    classe._noethys_double_clic_corrige = True


# Compatibilité héritée ObjectListView ; à supprimer lorsque toutes les listes
# auront migré vers les contrôles Noethys explicites.
_InstallerDoubleClicObjectListView()


class Menu(wx.Menu):
    def __init__(self, *args, **kwds):
        wx.Menu.__init__(self, *args, **kwds)

    def AppendItem(self, item):
        if 'phoenix' in wx.PlatformInfo:
            super(Menu, self).Append(item)
        else:
            super(Menu, self).AppendItem(item)

    def AppendMenu(self, *args, **kwds):
        if 'phoenix' in wx.PlatformInfo:
            super(Menu, self).Append(*args, **kwds)
        else:
            super(Menu, self).AppendMenu(*args, **kwds)


class ToolBar(wx.ToolBar):
    """Toolbar native Noethys avec géométrie moderne et DPI-aware.

    Ce contrôle est le point commun historique des barres d'outils Noethys :
    on modernise donc son implémentation directement. Aucun monkey-patch de
    ``wx.ToolBar`` n'est nécessaire. Les écrans peuvent migrer leurs icônes une
    par une via :meth:`AddFluentTool` sans changer leur logique métier.
    """

    def __init__(self, *args, **kwds):
        style = kwds.get("style", 0)
        style |= wx.TB_FLAT | wx.TB_NODIVIDER
        kwds["style"] = style
        wx.ToolBar.__init__(self, *args, **kwds)
        self._noethys_base_bitmap = None
        self._AppliqueSurface()

    def _AppliqueSurface(self):
        try:
            from Utils import UTILS_Interface
            self.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container"))
            self.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
        except Exception:
            pass
        try:
            police = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
            self.SetFont(police)
        except Exception:
            pass

    def SetToolBitmapSize(self, size):
        try:
            largeur = int(size.GetWidth()) if hasattr(size, "GetWidth") else int(size[0])
            if largeur > 0:
                self._noethys_base_bitmap = largeur
        except Exception:
            pass
        return wx.ToolBar.SetToolBitmapSize(self, size)

    def _TailleBitmapResponsive(self):
        base = self._noethys_base_bitmap
        if not base:
            try:
                size = wx.ToolBar.GetToolBitmapSize(self)
                base = int(size.GetWidth()) if hasattr(size, "GetWidth") else int(size[0])
            except Exception:
                base = 24
        if base <= 0:
            base = 24
        try:
            from Utils import UTILS_Responsive
            return UTILS_Responsive.GetTailleIcone(base)
        except Exception:
            return base

    def AddFluentTool(self, tool_id, label, icon, tooltip="", kind=wx.ITEM_NORMAL, role="on_surface"):
        """Ajoute explicitement une commande basée sur le catalogue Fluent."""
        taille = self._TailleBitmapResponsive()
        try:
            from Utils import UTILS_FluentIcons
            bitmap = UTILS_FluentIcons.GetBitmap(icon, taille=taille, role=role)
        except Exception:
            bitmap = wx.NullBitmap

        try:
            return self.AddTool(tool_id, label, bitmap, wx.NullBitmap, kind, tooltip, "")
        except Exception:
            return self.AddLabelTool(tool_id, label, bitmap, wx.NullBitmap, kind, tooltip, "")

    def AddLabelTool(self, *args, **kw):
        if 'phoenix' in wx.PlatformInfo:
            if "longHelp" in kw:
                kw.pop("longHelp")
            return super(ToolBar, self).AddTool(*args, **kw)
        return super(ToolBar, self).AddLabelTool(*args, **kw)

    def AddSimpleTool(self, *args, **kw):
        if 'phoenix' in wx.PlatformInfo:
            if "longHelp" in kw:
                kw.pop("longHelp")
            return super(ToolBar, self).AddTool(*args, **kw)
        return super(ToolBar, self).AddSimpleTool(*args, **kw)

    def Realize(self):
        """Finalise la toolbar puis applique les métriques du design system."""
        resultat = wx.ToolBar.Realize(self)
        self._AppliqueSurface()
        try:
            from Utils import UTILS_UIMetrics
            from Utils import UTILS_Responsive

            taille = self._TailleBitmapResponsive()
            wx.ToolBar.SetToolBitmapSize(self, wx.Size(taille, taille))
            marge = UTILS_UIMetrics.spacing(1)
            try:
                self.SetMargins(marge, marge)
            except Exception:
                pass
            try:
                self.SetToolPacking(marge)
            except Exception:
                pass
            try:
                self.SetToolSeparation(max(UTILS_UIMetrics.spacing(1), 4))
            except Exception:
                pass

            avec_libelle = bool(self.GetWindowStyleFlag() & wx.TB_TEXT)
            hauteur = UTILS_UIMetrics.toolbar_height(avec_libelle=avec_libelle, icon_px=taille)
            hauteur = max(hauteur, UTILS_Responsive.GetTailleCibleAction(36))
            self.SetMinSize((-1, hauteur))
        except Exception:
            pass

        try:
            parent = self.GetParent()
            if parent is not None:
                parent.Layout()
        except Exception:
            pass
        return resultat


if __name__ == "__main__":
    pass
