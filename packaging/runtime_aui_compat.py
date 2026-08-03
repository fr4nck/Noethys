"""Compatibilité défensive pour wx.lib.agw.aui.

Les perspectives AUI persistées par d'anciennes versions peuvent devenir
incompatibles après une mise à jour de wxPython. Ce hook empêche une perspective
invalide ou un double arrêt du manager de faire planter Noethys.

Il ne modifie pas les perspectives enregistrées ni les données métier.
"""
from __future__ import annotations

import wx.lib.agw.aui as aui


_original_load_perspective = aui.AuiManager.LoadPerspective
_original_uninit = aui.AuiManager.UnInit


def _load_perspective_compat(self, perspective, update=True, restorecaption=False):
    if not isinstance(perspective, str) or not perspective.strip():
        return False
    try:
        return _original_load_perspective(
            self,
            perspective,
            update=bool(update),
            restorecaption=bool(restorecaption),
        )
    except (AssertionError, TypeError, ValueError, RuntimeError):
        # La perspective par défaut construite par l'application reste active.
        return False


def _uninit_compat(self):
    try:
        return _original_uninit(self)
    except (AssertionError, RuntimeError):
        # Un second appel pendant la fermeture ne doit pas interrompre wx.
        return None


aui.AuiManager.LoadPerspective = _load_perspective_compat
aui.AuiManager.UnInit = _uninit_compat
