# -*- coding: utf-8 -*-
"""Helpers explicites pour wxAUI.

Aucun contrôle wx/AGW n'est monkey-patché ici. Les écrans modernisés appellent
ces fonctions sur leurs propres managers/toolbars afin que le comportement
reste local, testable et prévisible.
"""


def ConfigurerManager(manager):
    """Applique une séparation de panes plus lisible au manager fourni."""
    if manager is None:
        return False
    try:
        import wx.lib.agw.aui as aui
        from Utils import UTILS_Interface
        from Utils import UTILS_Responsive
    except Exception:
        return False

    try:
        art = manager.GetArtProvider()
    except Exception:
        return False

    # Un séparateur suffisamment présent structure l'écran bien mieux qu'une
    # colonne de pictogrammes décoratifs. La valeur reste dense et suit le DPI.
    try:
        sash = max(5, min(9, int(round(5 * max(1.0, UTILS_Responsive._facteur_ecran())))))
        art.SetMetric(aui.AUI_DOCKART_SASH_SIZE, sash)
    except Exception:
        pass

    try:
        art.SetMetric(aui.AUI_DOCKART_PANE_BORDER_SIZE, 1)
    except Exception:
        pass

    try:
        art.SetColour(
            aui.AUI_DOCKART_SASH_COLOUR,
            UTILS_Interface.GetCouleurRole("outline_variant"),
        )
    except Exception:
        try:
            art.SetColor(
                aui.AUI_DOCKART_SASH_COLOUR,
                UTILS_Interface.GetCouleurRole("outline_variant"),
            )
        except Exception:
            pass

    try:
        art.SetColour(
            aui.AUI_DOCKART_BORDER_COLOUR,
            UTILS_Interface.GetCouleurRole("outline"),
        )
    except Exception:
        try:
            art.SetColor(
                aui.AUI_DOCKART_BORDER_COLOUR,
                UTILS_Interface.GetCouleurRole("outline"),
            )
        except Exception:
            pass

    try:
        manager.Update()
    except Exception:
        pass
    return True


def ConfigurerToolBar(toolbar, taille_base=16, fond_uni=True):
    """Configure explicitement une toolbar déjà construite.

    Cette fonction n'intercepte jamais ``__init__`` ni ``SetToolBitmapSize`` :
    l'écran propriétaire choisit de l'appeler.
    """
    if toolbar is None:
        return False
    try:
        import wx
        import wx.lib.agw.aui as aui
        from Utils import UTILS_Interface
        from Utils import UTILS_Responsive
    except Exception:
        return False

    taille = UTILS_Responsive.GetTailleIcone(taille_base)
    try:
        toolbar.SetToolBitmapSize(wx.Size(taille, taille))
    except Exception:
        try:
            toolbar.SetToolBitmapSize((taille, taille))
        except Exception:
            pass

    if fond_uni and isinstance(toolbar, aui.AuiToolBar):
        try:
            style = toolbar.GetAGWWindowStyleFlag()
            style |= getattr(aui, "AUI_TB_PLAIN_BACKGROUND", 0)
            toolbar.SetAGWWindowStyleFlag(style)
        except Exception:
            pass

    try:
        toolbar.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container"))
    except Exception:
        pass

    try:
        toolbar.Realize()
    except Exception:
        pass
    return True


def ChargerPerspective(manager, perspective, fallback=None):
    """Charge une perspective AUI avec repli sûr sur ``fallback``."""
    ConfigurerManager(manager)

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
            ConfigurerManager(manager)
            return result

    ConfigurerManager(manager)
    return False
