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
        # Compatibilité avec d'anciens ImportError qui n'exposent pas .name.
        return True
    return nom_absent == nom_module or nom_module.startswith(nom_absent + ".")


def Import(nom_module=""):
    """Importe un module en conservant le fallback historique par nom court.

    Le nom qualifié est toujours essayé en premier. Le nom court n'est tenté
    que si le module qualifié lui-même est absent ; les ImportError provenant
    d'une dépendance interne continuent à remonter immédiatement.
    """
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
    """Fiabilise l'activation par double-clic des ObjectListView sous Phoenix.

    L'ancienne version embarquée d'ObjectListView laisse le double-clic au
    contrôle natif lorsque l'édition de cellule est désactivée. Sur wxPython
    Phoenix/Windows, ``EVT_LIST_ITEM_ACTIVATED`` peut alors ne jamais être émis
    alors que les actions contextuelles (Modifier, Ouvrir...) fonctionnent.

    Le correctif reste volontairement au niveau de la couche commune :
    - le comportement natif est conservé ;
    - un événement d'activation de secours est émis après un double-clic sur
      une vraie ligne ;
    - les listes éditables gardent leur double-clic d'édition ;
    - si Windows émet aussi l'activation native, les handlers ne sont appelés
      qu'une seule fois pour ce double-clic.
    """
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
        """Déduplique uniquement l'activation liée au double-clic de secours."""
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

        # Laisse toujours ObjectListView exécuter son traitement historique
        # (notamment l'édition de cellule lorsqu'elle est activée).
        resultat = double_clic_original(self, evt)

        if not est_double:
            return resultat

        # Ne jamais détourner le double-clic des listes qui éditent leurs
        # cellules : leur comportement historique reste prioritaire.
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

        # Ouvre une courte fenêtre de déduplication : selon la version de
        # Windows/wx, l'activation native peut arriver avant ou après celle de
        # secours. Chaque handler n'est exécuté qu'une fois.
        self._noethys_double_clic_index = index
        self._noethys_double_clic_limite = time.monotonic() + 0.35
        self._noethys_double_clic_handlers_vus = set()
        wx.CallAfter(_EmettreActivation, self, index)
        return resultat

    classe.Bind = Bind
    classe._HandleLeftClickOrDoubleClick = _HandleLeftClickOrDoubleClick
    classe._noethys_double_clic_corrige = True


# Applique la compatibilité une seule fois au chargement de la couche wx.
_InstallerDoubleClicObjectListView()


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
