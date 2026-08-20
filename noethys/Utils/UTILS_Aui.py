# -*- coding: utf-8 -*-
"""Helpers explicites pour wxAUI.

La géométrie AUI est dérivée du design system commun. Aucun contrôle wx/AGW
n'est monkey-patché : les managers et toolbars sont configurés explicitement
lorsqu'ils entrent dans le shell Noethys.
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


def _TailleBitmapExistante(toolbar, defaut=16):
    try:
        taille = toolbar.GetToolBitmapSize()
        largeur = int(taille.GetWidth()) if hasattr(taille, "GetWidth") else int(taille[0])
        if largeur > 0:
            return largeur
    except Exception:
        pass
    return defaut


def _ToolbarAvecLibelle(toolbar):
    try:
        import wx
        import wx.lib.agw.aui as aui
        if isinstance(toolbar, aui.AuiToolBar):
            return bool(toolbar.GetAGWWindowStyleFlag() & aui.AUI_TB_TEXT)
        return bool(toolbar.GetWindowStyleFlag() & wx.TB_TEXT)
    except Exception:
        return True


def _ConfigurerToolbarsDuManager(manager):
    """Dimensionne les toolbars du manager à partir de leur contenu réel."""
    try:
        import wx.lib.agw.aui as aui
        panes = manager.GetAllPanes()
    except Exception:
        return

    for pane in panes:
        fenetre = getattr(pane, "window", None)
        if not isinstance(fenetre, aui.AuiToolBar):
            continue

        taille_base = _TailleBitmapExistante(fenetre, defaut=16)
        ConfigurerToolBar(fenetre, taille_base=taille_base, fond_uni=True)

        # AUI mémorise sa propre taille de pane : agrandir seulement le widget
        # ne suffit pas et produisait les libellés rognés observés à 120 %.
        try:
            hauteur = int(getattr(fenetre, "_noethys_toolbar_min_height", 0) or 0)
            if hauteur > 0:
                pane.MinSize((-1, hauteur)).BestSize((-1, hauteur))
        except Exception:
            pass


def _ConfigurerPoliceCaptions(art):
    """Met les titres AUI à la même échelle typographique que le contenu."""
    try:
        import wx
        import wx.lib.agw.aui as aui
        from Utils import UTILS_Interface

        police = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        base = max(7, police.GetPointSize())
        facteur = (UTILS_Interface.GetEchelle() / 100.0) * (UTILS_Interface.GetTailleTexte() / 100.0)
        police.SetPointSize(max(7, int(round(base * facteur))))
        art.SetFont(aui.AUI_DOCKART_CAPTION_FONT, police)
    except Exception:
        pass


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
        sash = max(5, min(10, int(round(5 * max(1.0, UTILS_Responsive.GetFacteurEcran())))))
        art.SetMetric(aui.AUI_DOCKART_SASH_SIZE, sash)
    except Exception:
        pass

    try:
        art.SetMetric(aui.AUI_DOCKART_PANE_BORDER_SIZE, 1)
    except Exception:
        pass

    _ConfigurerPoliceCaptions(art)

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
    """Configure une toolbar selon icônes, texte, DPI et échelle utilisateur."""
    if toolbar is None:
        return False
    try:
        import wx
        import wx.lib.agw.aui as aui
        from Utils import UTILS_Interface
        from Utils import UTILS_Responsive
        from Utils import UTILS_UIMetrics
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

    # Les marges font partie de la métrique de composant, pas de chaque écran.
    marge = UTILS_UIMetrics.spacing(1)
    try:
        toolbar.SetToolPacking(marge)
    except Exception:
        pass
    try:
        toolbar.SetToolSeparation(marge)
    except Exception:
        pass
    try:
        toolbar.SetMargins(marge, marge)
    except Exception:
        try:
            toolbar.SetMargins(marge, marge, marge, marge)
        except Exception:
            pass

    try:
        toolbar.Realize()
    except Exception:
        pass

    avec_libelle = _ToolbarAvecLibelle(toolbar)
    hauteur = UTILS_UIMetrics.toolbar_height(avec_libelle=avec_libelle, icon_px=taille)
    try:
        hauteur = max(hauteur, int(toolbar.GetBestSize().GetHeight()))
    except Exception:
        pass

    try:
        taille_min = toolbar.GetMinSize()
        hauteur = max(hauteur, int(taille_min.GetHeight()))
    except Exception:
        pass

    try:
        toolbar.SetMinSize((-1, hauteur))
        toolbar._noethys_toolbar_min_height = hauteur
    except Exception:
        pass

    try:
        toolbar.InvalidateBestSize()
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
