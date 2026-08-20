# -*- coding: utf-8 -*-
"""Helpers explicites pour wxAUI et les composants du shell Noethys.

La géométrie AUI est dérivée du design system commun. Aucun contrôle wx/AGW
n'est monkey-patché : les managers, toolbars, notebooks et grilles sont
configurés explicitement lorsqu'ils entrent dans le shell Noethys.
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


def ChargerBitmapToolBar(image, taille_base=24):
    """Charge un pictogramme à la taille réellement utilisée par une toolbar."""
    try:
        import wx
        import Chemins
        from Utils import UTILS_Responsive

        taille = UTILS_Responsive.GetTailleIcone(taille_base)
        chemin = Chemins.GetStaticIconPath(image, taille=taille)
        bitmap = wx.Bitmap(chemin, wx.BITMAP_TYPE_ANY)
        if bitmap.IsOk() and (bitmap.GetWidth() != taille or bitmap.GetHeight() != taille):
            source = bitmap.ConvertToImage()
            source = source.Scale(taille, taille, wx.IMAGE_QUALITY_HIGH)
            bitmap = wx.Bitmap(source)
        return bitmap
    except Exception:
        try:
            return wx.NullBitmap
        except Exception:
            return None


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


def _ItererDescendants(window):
    if window is None:
        return
    yield window
    try:
        enfants = window.GetChildren()
    except Exception:
        enfants = []
    for enfant in enfants:
        for descendant in _ItererDescendants(enfant):
            yield descendant


def ConfigurerGrille(grille):
    """Applique la grammaire visuelle commune à une wx.Grid existante.

    Les couleurs des cellules restent entièrement métier. Ici on ne définit que
    le squelette commun : traits, labels, surfaces et métriques de rangée.
    """
    if grille is None:
        return False
    try:
        import wx.grid as gridlib
        from Utils import UTILS_Interface
        from Utils import UTILS_UIMetrics
        if not isinstance(grille, gridlib.Grid):
            return False
    except Exception:
        return False

    try:
        grille.EnableGridLines(True)
        grille.SetGridLineColour(UTILS_Interface.GetCouleurRole("outline_variant"))
    except Exception:
        pass

    try:
        grille.SetLabelBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_high"))
        grille.SetLabelTextColour(UTILS_Interface.GetCouleurRole("on_surface"))
    except Exception:
        pass

    try:
        grille.SetDefaultCellBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_lowest"))
        grille.SetDefaultCellTextColour(UTILS_Interface.GetCouleurRole("on_surface"))
    except Exception:
        pass

    # On ne touche pas ici aux largeurs métier ni aux tailles explicitement
    # configurées par l'utilisateur. Seules les métriques génériques sont mises
    # à l'échelle à partir de leur valeur de référence initiale.
    try:
        if not hasattr(grille, "_noethys_default_row_base"):
            grille._noethys_default_row_base = grille.GetDefaultRowSize()
        grille.SetDefaultRowSize(
            max(UTILS_UIMetrics.row_height("table"), UTILS_UIMetrics.px(grille._noethys_default_row_base)),
            True,
        )
    except Exception:
        pass

    for getter, setter, attribut in (
        ("GetRowLabelSize", "SetRowLabelSize", "_noethys_row_label_base"),
        ("GetColLabelSize", "SetColLabelSize", "_noethys_col_label_base"),
    ):
        try:
            if not hasattr(grille, attribut):
                setattr(grille, attribut, getattr(grille, getter)())
            base = getattr(grille, attribut)
            getattr(grille, setter)(UTILS_UIMetrics.px(base))
        except Exception:
            pass

    try:
        grille.ForceRefresh()
    except Exception:
        try:
            grille.Refresh()
        except Exception:
            pass
    return True


def ConfigurerNotebook(notebook):
    """Donne aux onglets AUI une hauteur lisible et cohérente."""
    if notebook is None:
        return False
    try:
        import wx.lib.agw.aui as aui
        from Utils import UTILS_UIMetrics
        from Utils import UTILS_Interface
        if not isinstance(notebook, aui.AuiNotebook):
            return False
    except Exception:
        return False

    try:
        notebook.SetTabCtrlHeight(UTILS_UIMetrics.px(32))
    except Exception:
        pass
    try:
        notebook.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface"))
    except Exception:
        pass
    try:
        notebook.Refresh()
    except Exception:
        pass
    return True


def _ConfigurerComposantsDuManager(manager):
    """Configure les composants communs, y compris ceux imbriqués dans un pane."""
    try:
        import wx
        import wx.grid as gridlib
        import wx.lib.agw.aui as aui
        panes = manager.GetAllPanes()
    except Exception:
        return

    deja_vues = set()
    for pane in panes:
        racine = getattr(pane, "window", None)
        for fenetre in _ItererDescendants(racine):
            if id(fenetre) in deja_vues:
                continue
            deja_vues.add(id(fenetre))

            if isinstance(fenetre, (wx.ToolBar, aui.AuiToolBar)):
                taille_base = getattr(fenetre, "_noethys_toolbar_icon_base", None)
                if taille_base is None:
                    taille_base = _TailleBitmapExistante(fenetre, defaut=16)
                ConfigurerToolBar(fenetre, taille_base=taille_base, fond_uni=True)
                if fenetre is racine:
                    try:
                        hauteur = int(getattr(fenetre, "_noethys_toolbar_min_height", 0) or 0)
                        if hauteur > 0:
                            pane.MinSize((-1, hauteur)).BestSize((-1, hauteur))
                    except Exception:
                        pass
                continue

            if isinstance(fenetre, aui.AuiNotebook):
                ConfigurerNotebook(fenetre)
                continue

            if isinstance(fenetre, gridlib.Grid):
                ConfigurerGrille(fenetre)


def _ConfigurerPoliceCaptions(art):
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
    """Structure visuellement les panes et composants du manager fourni."""
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

    for role, constante in (
        ("outline_variant", aui.AUI_DOCKART_SASH_COLOUR),
        ("outline", aui.AUI_DOCKART_BORDER_COLOUR),
    ):
        try:
            art.SetColour(constante, UTILS_Interface.GetCouleurRole(role))
        except Exception:
            try:
                art.SetColor(constante, UTILS_Interface.GetCouleurRole(role))
            except Exception:
                pass

    _ConfigurerComposantsDuManager(manager)

    try:
        manager.Update()
        fenetre = manager.GetManagedWindow()
        if fenetre is not None:
            fenetre.Layout()
            fenetre.SendSizeEvent()
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

    try:
        taille_base = int(taille_base)
    except Exception:
        taille_base = 16
    toolbar._noethys_toolbar_icon_base = taille_base
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

    marge = UTILS_UIMetrics.spacing(1)
    for nom, args in (
        ("SetToolPacking", (marge,)),
        ("SetToolSeparation", (marge,)),
    ):
        try:
            getattr(toolbar, nom)(*args)
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
        hauteur = max(hauteur, int(toolbar.GetMinSize().GetHeight()))
    except Exception:
        pass

    try:
        toolbar.SetMinSize((-1, hauteur))
        toolbar._noethys_toolbar_min_height = hauteur
        toolbar.InvalidateBestSize()
    except Exception:
        pass

    try:
        parent = toolbar.GetParent()
        if parent is not None:
            parent.Layout()
    except Exception:
        pass
    return True


def ChargerPerspective(manager, perspective, fallback=None):
    """Charge une perspective AUI avec repli sûr sur ``fallback``."""
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
