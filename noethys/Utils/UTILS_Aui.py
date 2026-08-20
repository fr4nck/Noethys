# -*- coding: utf-8 -*-
"""Helpers explicites pour wxAUI et les composants du shell Noethys.

La géométrie AUI est dérivée du design system commun. Aucun contrôle wx/AGW
n'est monkey-patché : les managers, toolbars, notebooks et grilles sont
configurés explicitement lorsqu'ils entrent dans le shell Noethys.
"""

PERSPECTIVE_LAYOUT_VERSION = 5
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
        try:
            police.SetWeight(wx.FONTWEIGHT_SEMIBOLD)
        except Exception:
            police.SetWeight(wx.FONTWEIGHT_BOLD)
        art.SetFont(aui.AUI_DOCKART_CAPTION_FONT, police)
    except Exception:
        pass


def _SetArtColour(art, aui, constante, role):
    identifiant = getattr(aui, constante, None)
    if identifiant is None:
        return
    try:
        from Utils import UTILS_Interface
        couleur = UTILS_Interface.GetCouleurRole(role)
    except Exception:
        return
    try:
        art.SetColour(identifiant, couleur)
    except Exception:
        try:
            art.SetColor(identifiant, couleur)
        except Exception:
            pass


def _SetArtMetric(art, aui, constante, valeur):
    identifiant = getattr(aui, constante, None)
    if identifiant is None:
        return
    try:
        art.SetMetric(identifiant, int(valeur))
    except Exception:
        pass


def _ConfigurerArtShell(art, aui):
    """Palette AUI plate et dense, inspirée de Fluent 2.

    Début et fin de gradient reçoivent volontairement la même surface : on
    conserve le moteur de rendu AUI mais on élimine son ancien effet 3D.
    """
    try:
        from Utils import UTILS_UIMetrics
        caption = UTILS_UIMetrics.px(30)
    except Exception:
        caption = 30

    _SetArtMetric(art, aui, "AUI_DOCKART_CAPTION_SIZE", caption)
    _SetArtMetric(art, aui, "AUI_DOCKART_PANE_BORDER_SIZE", 1)

    for constante, role in (
        ("AUI_DOCKART_BACKGROUND_COLOUR", "surface"),
        ("AUI_DOCKART_SASH_COLOUR", "outline_variant"),
        ("AUI_DOCKART_BORDER_COLOUR", "outline_variant"),
        ("AUI_DOCKART_GRIPPER_COLOUR", "outline_variant"),
        ("AUI_DOCKART_INACTIVE_CAPTION_COLOUR", "surface_container"),
        ("AUI_DOCKART_INACTIVE_CAPTION_GRADIENT_COLOUR", "surface_container"),
        ("AUI_DOCKART_INACTIVE_CAPTION_TEXT_COLOUR", "on_surface_variant"),
        ("AUI_DOCKART_ACTIVE_CAPTION_COLOUR", "surface_container_high"),
        ("AUI_DOCKART_ACTIVE_CAPTION_GRADIENT_COLOUR", "surface_container_high"),
        ("AUI_DOCKART_ACTIVE_CAPTION_TEXT_COLOUR", "on_surface"),
    ):
        _SetArtColour(art, aui, constante, role)


def _GetPane(manager, nom):
    try:
        pane = manager.GetPane(nom)
        if pane is not None and pane.IsOk():
            return pane
    except Exception:
        pass
    return None


def _AppelerPane(pane, nom, *args):
    if pane is None:
        return
    try:
        getattr(pane, nom)(*args)
    except Exception:
        pass


def _ConfigurerBarresSysteme(manager):
    """Fige les barres structurelles du shell sans interdire les barres perso."""
    for nom, position in (("barre_raccourcis", 0), ("barre_utilisateur", 1)):
        pane = _GetPane(manager, nom)
        if pane is None:
            continue
        for methode, args in (
            ("Top", ()),
            ("Layer", (0,)),
            ("Row", (0,)),
            ("Position", (position,)),
            ("ToolbarPane", ()),
            ("Gripper", (False,)),
            ("Floatable", (False,)),
            ("DockFixed", (True,)),
            ("CloseButton", (False,)),
            ("MaximizeButton", (False,)),
            ("MinimizeButton", (False,)),
        ):
            _AppelerPane(pane, methode, *args)


def _ConfigurerPaneRecherche(manager, largeur, hauteur, largeur_gauche):
    """Convertit l'ancien CenterPane Individus en vrai pane AUI manipulable.

    ``CenterPane()`` neutralise historiquement plusieurs commandes AUI. Le
    panneau de recherche est désormais un dock droit normal : il conserve la
    grande zone de travail mais peut être réduit, maximisé, restauré ou fermé.
    Cette fonction ne rappelle jamais ``Show`` et respecte donc l'état choisi
    par l'utilisateur après la conversion initiale.
    """
    pane = _GetPane(manager, "recherche")
    if pane is None:
        return

    try:
        import wx.lib.agw.aui as aui
        est_centre = getattr(pane, "dock_direction", None) == aui.AUI_DOCK_CENTER
    except Exception:
        est_centre = False

    if est_centre:
        for methode, args in (
            ("Right", ()),
            ("Layer", (0,)),
            ("Row", (0,)),
            ("Position", (0,)),
        ):
            _AppelerPane(pane, methode, *args)

    for methode, args in (
        ("Caption", (u"Individus / Familles",)),
        ("CaptionVisible", (True,)),
        ("PaneBorder", (True,)),
        ("CloseButton", (True,)),
        ("MaximizeButton", (True,)),
        ("MinimizeButton", (True,)),
        ("Resizable", (True,)),
        ("Movable", (True,)),
        ("Floatable", (True,)),
        ("DockFixed", (False,)),
    ):
        _AppelerPane(pane, methode, *args)

    # Le pane occupe naturellement le reste du cockpit. On ne touche pas à sa
    # taille pendant un état maximisé/minimisé : sinon un resize système peut
    # annuler visuellement l'action de l'utilisateur.
    etat_special = False
    for methode in ("IsMaximized", "IsMinimized"):
        try:
            if getattr(pane, methode)():
                etat_special = True
        except Exception:
            pass
    if not etat_special:
        largeur_recherche = max(460, largeur - largeur_gauche - 24)
        _AppelerPane(pane, "MinSize", (420, 240))
        _AppelerPane(pane, "BestSize", (largeur_recherche, max(360, int(hauteur * 0.72))))


def _GetTailleClient(manager):
    try:
        fenetre = manager.GetManagedWindow()
        taille = fenetre.GetClientSize()
        largeur = int(taille.GetWidth())
        hauteur = int(taille.GetHeight())
        return fenetre, largeur, hauteur
    except Exception:
        return None, 0, 0


def _GetDimensionsResponsive(largeur, hauteur):
    """Retourne les métriques du cockpit à partir de la place réellement disponible."""
    try:
        from Utils import UTILS_Responsive
        facteur = min(1.30, max(1.0, float(UTILS_Responsive.GetFacteurEcran())))
    except Exception:
        facteur = 1.0

    if largeur >= 1800:
        ratio_gauche = 0.32
    elif largeur >= 1450:
        ratio_gauche = 0.34
    elif largeur >= 1150:
        ratio_gauche = 0.37
    else:
        ratio_gauche = 0.40

    minimum_gauche = int(round(390 * facteur))
    maximum_gauche = int(round(760 * facteur))
    largeur_gauche = max(minimum_gauche, min(maximum_gauche, int(round(largeur * ratio_gauche))))

    hauteur_info = max(
        int(round(104 * facteur)),
        min(int(round(176 * facteur)), int(round(hauteur * 0.15))),
    )
    hauteur_messages_min = max(96, int(round(110 * facteur)))

    return {
        "largeur_gauche": largeur_gauche,
        "hauteur_info": hauteur_info,
        "hauteur_messages_min": hauteur_messages_min,
    }


def _AjusterDocksLateraux(manager, largeur_gauche):
    """Ajuste la largeur du dock gauche existant sans imposer de pixels aux enfants."""
    try:
        import wx.lib.agw.aui as aui
        docks = manager.GetAllDocks()
    except Exception:
        return

    for dock in docks:
        try:
            if dock.dock_direction == aui.AUI_DOCK_LEFT:
                dock.size = largeur_gauche
        except Exception:
            pass


def _AppliquerLayoutResponsive(manager, forcer=False):
    """Recalcule uniquement la géométrie structurelle du cockpit."""
    if manager is None:
        return False

    fenetre, largeur, hauteur = _GetTailleClient(manager)
    if fenetre is None or largeur < 500 or hauteur < 400:
        return False

    precedent = getattr(fenetre, "_noethys_aui_responsive_size", None)
    if not forcer and precedent is not None:
        if abs(largeur - precedent[0]) < 28 and abs(hauteur - precedent[1]) < 22:
            return False
    fenetre._noethys_aui_responsive_size = (largeur, hauteur)

    dimensions = _GetDimensionsResponsive(largeur, hauteur)
    _ConfigurerBarresSysteme(manager)

    try:
        manager.SetDockSizeConstraint(0.46, 0.32)
    except Exception:
        pass

    largeur_gauche = dimensions["largeur_gauche"]
    pane_effectifs = _GetPane(manager, "effectifs")
    if pane_effectifs is not None:
        _AppelerPane(pane_effectifs, "MinSize", (min(largeur_gauche, 430), 190))
        _AppelerPane(pane_effectifs, "BestSize", (largeur_gauche, max(320, int(hauteur * 0.66))))
        try:
            pane_effectifs.dock_proportion = 72000
        except Exception:
            pass
        _AjusterDocksLateraux(manager, largeur_gauche)

    pane_messages = _GetPane(manager, "messages")
    if pane_messages is not None:
        _AppelerPane(pane_messages, "MinSize", (260, dimensions["hauteur_messages_min"]))
        try:
            pane_messages.dock_proportion = 28000
        except Exception:
            pass

    pane_info = _GetPane(manager, "ephemeride")
    if pane_info is not None:
        hauteur_info = dimensions["hauteur_info"]
        _AppelerPane(pane_info, "Caption", u"Aujourd'hui / Échéancier")
        _AppelerPane(pane_info, "MinSize", (-1, max(96, int(hauteur_info * 0.80))))
        _AppelerPane(pane_info, "BestSize", (-1, hauteur_info))

    _ConfigurerPaneRecherche(manager, largeur, hauteur, largeur_gauche)

    try:
        manager.Update()
    except Exception:
        pass
    try:
        fenetre.Layout()
    except Exception:
        pass
    return True


def _InstallerResponsive(manager):
    """Installe un seul gestionnaire de resize, débouncé par CallAfter."""
    try:
        import wx
        fenetre = manager.GetManagedWindow()
    except Exception:
        return False
    if fenetre is None:
        return False
    if getattr(fenetre, "_noethys_aui_responsive_installe", False):
        return True

    fenetre._noethys_aui_responsive_installe = True
    fenetre._noethys_aui_responsive_pending = False

    def _AppliquerPlusTard():
        try:
            fenetre._noethys_aui_responsive_pending = False
            _AppliquerLayoutResponsive(manager, forcer=False)
        except Exception:
            fenetre._noethys_aui_responsive_pending = False

    def _OnSize(event):
        event.Skip()
        if getattr(fenetre, "_noethys_aui_responsive_pending", False):
            return
        fenetre._noethys_aui_responsive_pending = True
        wx.CallAfter(_AppliquerPlusTard)

    try:
        fenetre.Bind(wx.EVT_SIZE, _OnSize)
    except Exception:
        return False
    return True


def ConfigurerManager(manager):
    """Structure visuellement les panes et composants du manager fourni."""
    if manager is None:
        return False
    try:
        import wx.lib.agw.aui as aui
        from Utils import UTILS_Responsive
    except Exception:
        return False

    try:
        art = manager.GetArtProvider()
    except Exception:
        return False

    try:
        sash = max(5, min(10, int(round(5 * max(1.0, UTILS_Responsive.GetFacteurEcran())))))
        _SetArtMetric(art, aui, "AUI_DOCKART_SASH_SIZE", sash)
    except Exception:
        pass

    _ConfigurerPoliceCaptions(art)
    _ConfigurerArtShell(art, aui)
    _ConfigurerComposantsDuManager(manager)
    _InstallerResponsive(manager)
    _AppliquerLayoutResponsive(manager, forcer=True)

    try:
        manager.Update()
        fenetre = manager.GetManagedWindow()
        if fenetre is not None:
            fenetre.SetBackgroundColour(__import__("Utils.UTILS_Interface", fromlist=["UTILS_Interface"]).GetCouleurRole("surface"))
            fenetre.Layout()
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
        toolbar.SetBackgroundColour(UTILS_Interface.GetCouleurRole("surface_container_low"))
        toolbar.SetForegroundColour(UTILS_Interface.GetCouleurRole("on_surface"))
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