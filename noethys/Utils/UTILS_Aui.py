# -*- coding: utf-8 -*-
"""Helpers de compatibilité et de présentation pour wxAUI.

Les perspectives sont persistées dans Config.json et peuvent provenir d'une
ancienne version de wxPython. Ce module installe aussi deux adaptations
transversales très limitées : fond uni des AuiToolBar et taille des pictos par
paliers DPI/écran.
"""


def InstallerStyleToolbars():
    """Modernise les toolbars sans modifier leurs actions ni leur structure."""
    try:
        import wx
        import wx.lib.agw.aui as aui
        from Utils import UTILS_Responsive
    except Exception:
        return False

    # AGW : supprimer le vieux fond en dégradé/segmenté. Le flag est natif à
    # AuiToolBar et conserve le comportement de docking/overflow historique.
    if not getattr(aui.AuiToolBar, "_noethys_plain_toolbar", False):
        try:
            original_init = aui.AuiToolBar.__init__

            def _init_noethys(self, *args, **kwargs):
                flag = getattr(aui, "AUI_TB_PLAIN_BACKGROUND", 0)
                if flag:
                    kwargs["agwStyle"] = kwargs.get("agwStyle", getattr(aui, "AUI_TB_DEFAULT_STYLE", 0)) | flag
                original_init(self, *args, **kwargs)
                try:
                    self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
                except Exception:
                    pass

            aui.AuiToolBar.__init__ = _init_noethys
            aui.AuiToolBar._noethys_plain_toolbar = True
        except Exception:
            pass

    # Paliers responsive des toolbars AGW.
    if not getattr(aui.AuiToolBar, "_noethys_responsive_icons", False):
        try:
            original_set_size = aui.AuiToolBar.SetToolBitmapSize

            def _set_size_noethys(self, taille):
                return original_set_size(self, UTILS_Responsive.AdapterTailleWx(taille))

            aui.AuiToolBar.SetToolBitmapSize = _set_size_noethys
            aui.AuiToolBar._noethys_responsive_icons = True
        except Exception:
            pass

    # Les barres d'actions classiques (par ex. Individus) utilisent wx.ToolBar.
    if not getattr(wx.ToolBar, "_noethys_responsive_icons", False):
        try:
            original_wx_set_size = wx.ToolBar.SetToolBitmapSize

            def _wx_set_size_noethys(self, taille):
                return original_wx_set_size(self, UTILS_Responsive.AdapterTailleWx(taille))

            wx.ToolBar.SetToolBitmapSize = _wx_set_size_noethys
            wx.ToolBar._noethys_responsive_icons = True
        except Exception:
            pass

    return True


# Noethys importe UTILS_Aui avant de construire ses toolbars communes.
InstallerStyleToolbars()


def ChargerPerspective(manager, perspective, fallback=None):
    """Charge une perspective AUI avec repli sûr sur ``fallback``.

    Retourne le résultat de ``LoadPerspective``. Les erreurs de parsing ou
    assertions liées à une ancienne perspective sont considérées comme un
    échec de chargement, sans masquer les autres exceptions inattendues.
    """
    candidates = []
    for candidate in (perspective, fallback):
        if isinstance(candidate, str) and candidate.strip() and candidate not in candidates:
            candidates.append(candidate)

    for candidate in candidates:
        try:
            result = manager.LoadPerspective(candidate)
        except (AssertionError, TypeError, ValueError, RuntimeError):
            result = False
        if result is not False:
            return result

    return False
