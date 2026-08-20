# -*- coding: utf-8 -*-
"""Helpers explicites pour wxAUI.

Aucun contrôle wx/AGW n'est monkey-patché ici. Les écrans modernisés appellent
ces fonctions sur leurs propres managers/toolbars afin que le comportement
reste local, testable et prévisible.
"""

PERSPECTIVE_LAYOUT_VERSION = 2
PARAMETRE_PERSPECTIVE_VERSION = "aui_perspective_layout_version"


def VerifierVersionPerspective(manager):
    """Invalide proprement une ancienne génération de disposition AUI."""
    if manager is None:
        return False
    try:
        from Utils import UTILS_Config
        version = int(UTILS_Config.GetParametre(PARAMETRE_PERSPECTIVE_VERSION, 0) or 0)
    except Exception:
        version = 0

    if version == PERSPECTIVE_LAYOUT_VERSION:
        return True

    try:
        fenetre = manager.GetManagedWindow()
    except Exception:
        fenetre = None

    if fenetre is not None:
        try:
            fenetre.perspectives = []
            fenetre.perspective_active = None
        except Exception:
            pass

    try:
        UTILS_Config.SetParametre(PARAMETRE_PERSPECTIVE_VERSION, PERSPECTIVE_LAYOUT_VERSION)
    except Exception:
        pass
    return False


def _ConfigurerToolbarsDuManager(manager):
    """Configure uniquement les toolbars appartenant au manager fourni.

    C'est volontairement différent d'un monkey-patch : aucune classe wx n'est
    modifiée et une fenêtre qui n'appelle pas ``ConfigurerManager`` n'est pas
    affectée.
    """
    try:
        import wx.lib.agw.aui as aui
        panes = manager.GetAllPanes()
    except Exception:
        return

    for pane in panes:
        fenetre = getattr(pane, "window", None)
        if isinstance(fenetre, aui.AuiToolBar):
            ConfigurerToolBar(fenetre, taille_base=16, fond_uni=True)


def ConfigurerManager(manager):
    """Structure visuellement les panes et toolbars du manager fourni."""
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

    try:
        sash = max(5, min(9, int(round(5 * max(1.0, UTILS_Responsive.GetFacteurEcran())))))
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

    _ConfigurerToolbarsDuManager(manager)

    try:
        manager.Update()
    except Exception:
        pass
    return True


def ConfigurerToolBar(toolbar, taille_base=16, fond_uni=True):
    """Configure explicitement une toolbar déjà construite."""
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
    """Charge une perspective AUI avec repli sûr sur ``fallback``.

    Une perspective d'une génération antérieure n'est jamais restaurée : seul
    le fallback courant est alors chargé.
    """
    ConfigurerManager(manager)
    version_valide = VerifierVersionPerspective(manager)

    if version_valide:
        sources = (perspective, fallback)
    else:
        sources = (fallback,)

    candidates = []
    for candidate in sources:
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
