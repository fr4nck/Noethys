#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Façade de style unique de Repens Design.

Ce module joue le rôle du « CSS Noethys » : les écrans métier ne doivent pas
connaître les RGB, rayons, tailles d'icônes, espacements ou détails de
fontes. Ils expriment uniquement une intention visuelle et consomment cette
API.

Les sources de vérité restent spécialisées :
- UTILS_DesignSystem : rôles sémantiques et palettes ;
- UTILS_UIMetrics    : métriques DPI / échelle ;
- UTILS_Interface    : préférences utilisateur et apparence active.

Cette façade est le point d'entrée recommandé pour les nouveaux composants et
les fenêtres migrées vers Repens Design.
"""

import wx

from Utils import UTILS_Interface
from Utils import UTILS_UIMetrics


RAYONS = {
    "compact": 5,
    "controle": 7,
    "surface": 9,
    "dialogue": 12,
}

# Gamme typographique commune avec Teamworks.
# Les écrans choisissent un rôle sémantique et jamais une taille locale.
# Les tailles de référence sont exprimées en points à 100 %. wx conserve la
# fonte système native de la plateforme et la préférence d'échelle utilisateur
# est appliquée ensuite de façon uniforme à toute la hiérarchie.
TYPOGRAPHIES = {
    "display": {"points": 18, "weight": wx.FONTWEIGHT_BOLD},
    "h1": {"points": 16, "weight": wx.FONTWEIGHT_BOLD},
    "h2": {"points": 14, "weight": wx.FONTWEIGHT_BOLD},
    "h3": {"points": 12, "weight": wx.FONTWEIGHT_BOLD},
    "h4": {"points": 11, "weight": wx.FONTWEIGHT_BOLD},
    "h5": {"points": 10, "weight": wx.FONTWEIGHT_NORMAL, "semibold": True},
    "h6": {"points": 9, "weight": wx.FONTWEIGHT_NORMAL, "semibold": True},
    "lead": {"points": 11, "weight": wx.FONTWEIGHT_NORMAL},
    "body_large": {"points": 10, "weight": wx.FONTWEIGHT_NORMAL},
    "body": {"points": 9, "weight": wx.FONTWEIGHT_NORMAL},
    "body_small": {"points": 8, "weight": wx.FONTWEIGHT_NORMAL},
    "label": {"points": 8, "weight": wx.FONTWEIGHT_NORMAL, "semibold": True},
    "caption": {"points": 7, "weight": wx.FONTWEIGHT_NORMAL},
    "micro": {"points": 7, "weight": wx.FONTWEIGHT_NORMAL},
    "data_large": {"points": 16, "weight": wx.FONTWEIGHT_NORMAL, "semibold": True},
    "body_emphasis": {"points": 9, "weight": wx.FONTWEIGHT_BOLD},
    "overline": {"alias": "label"},
    # Alias historiques : conservés pour compatibilité, à ne plus utiliser
    # dans les nouveaux écrans.
    "title": {"alias": "h1"},
    "section": {"alias": "h2"},
}

# Accepte les noms utilisés dans la documentation/Teamworks sans imposer la
# convention interne snake_case aux appelants.
ALIASES_TYPOGRAPHIE = {
    "bodylarge": "body_large",
    "body-large": "body_large",
    "bodysmall": "body_small",
    "body-small": "body_small",
    "datalarge": "data_large",
    "data-large": "data_large",
}


def couleur(role="surface"):
    """Retourne une couleur sémantique de l'apparence active."""
    return UTILS_Interface.GetCouleurRole(role)


def etat(nom="normal"):
    """Retourne background/foreground/outline pour un état interactif."""
    return UTILS_Interface.GetEtatCouleurs(nom)


def espace(niveau=2):
    return UTILS_UIMetrics.spacing(niveau)


def px(valeur, minimum=1):
    return UTILS_UIMetrics.px(valeur, minimum=minimum)


def rayon(contexte="surface"):
    return px(RAYONS.get(contexte, RAYONS["surface"]))


def taille_icone(contexte="toolbar"):
    return UTILS_UIMetrics.icon_size(contexte)


def hauteur_ligne(contexte="list"):
    return UTILS_UIMetrics.row_height(contexte)


def cible_action(contexte="standard"):
    return UTILS_UIMetrics.action_target(contexte)


def hauteur_toolbar(avec_libelle=True):
    return UTILS_UIMetrics.toolbar_height(avec_libelle=avec_libelle)


def hauteur_panneau(contexte="secondary"):
    """Hauteur minimale d'une surface fonctionnelle compacte."""
    return UTILS_UIMetrics.panel_min_height(contexte)


def normaliser_role_typographie(role):
    if role is None:
        return "body"
    role = str(role).strip().lower().replace(" ", "_")
    role = ALIASES_TYPOGRAPHIE.get(role, role)
    if role not in TYPOGRAPHIES:
        return "body"
    return role


def _definition_typographie(role):
    role = normaliser_role_typographie(role)
    definition = TYPOGRAPHIES.get(role, TYPOGRAPHIES["body"])
    alias = definition.get("alias")
    if alias:
        return TYPOGRAPHIES.get(alias, TYPOGRAPHIES["body"])
    return definition


def police(role="body"):
    """Construit une fonte système à partir d'un rôle typographique.

    La famille reste celle de l'OS ; seule la hiérarchie sémantique de taille
    et de graisse est pilotée par Repens Design.
    """
    definition = _definition_typographie(role)
    try:
        fonte = wx.Font(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
    except Exception:
        fonte = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)

    try:
        facteur_texte = UTILS_Interface.GetTailleTexte() / 100.0
        points = max(7, int(definition.get("points", 9)))
        taille = max(7, int(round(points * facteur_texte)))
        fonte.SetPointSize(taille)
        poids = definition.get("weight", wx.FONTWEIGHT_NORMAL)
        if definition.get("semibold") and hasattr(wx, "FONTWEIGHT_SEMIBOLD"):
            poids = wx.FONTWEIGHT_SEMIBOLD
        fonte.SetWeight(poids)
    except Exception:
        pass
    return fonte


def appliquer_fenetre(fenetre, role_fond="surface"):
    """Applique le socle visuel commun à un Frame/Dialog/Panel."""
    try:
        fenetre.SetBackgroundColour(couleur(role_fond))
        fenetre.SetForegroundColour(couleur("on_surface"))
        fenetre.SetFont(police("body"))
    except Exception:
        pass
    return fenetre


def appliquer_texte(ctrl, role="body", role_texte="on_surface", role_fond=None):
    try:
        ctrl.SetFont(police(normaliser_role_typographie(role)))
        ctrl.SetForegroundColour(couleur(role_texte))
        if role_fond is not None:
            ctrl.SetBackgroundColour(couleur(role_fond))
    except Exception:
        pass
    return ctrl


def appliquer_saisie(ctrl):
    """Style commun des champs de saisie natifs conservés."""
    try:
        ctrl.SetFont(police("body"))
        ctrl.SetForegroundColour(couleur("on_surface"))
        ctrl.SetBackgroundColour(couleur("surface_container_lowest"))
        ctrl.SetMinSize((-1, cible_action("compact")))
    except Exception:
        pass
    return ctrl


def appliquer_liste(ctrl):
    """Style de base des listes lorsque leur renderer reste natif."""
    try:
        ctrl.SetFont(police("body"))
        ctrl.SetForegroundColour(couleur("on_surface"))
        ctrl.SetBackgroundColour(couleur("surface_container_lowest"))
    except Exception:
        pass
    return ctrl


def appliquer_liste_riche(ctrl):
    """Réapplique la palette prudente des ObjectListView historiques.

    Le moteur global d'apparence sait déjà distinguer les surfaces neutres des
    couleurs métier explicites. Ce point d'entrée ne redéfinit donc pas une
    seconde règle : il réutilise exactement cette politique au moment où les
    anciens écrans ont fini d'assigner leurs zebra et leurs groupes.
    """
    try:
        ctrl.SetFont(police("body"))
    except Exception:
        pass

    try:
        UTILS_Interface._appliquer_palette_liste(
            ctrl,
            sombre=UTILS_Interface.EstSombre(),
        )
    except Exception:
        # Repli minimal lorsque le contrôle est utilisé hors du runtime complet.
        appliquer_liste(ctrl)
    return ctrl


def appliquer_groupes_liste(ctrl):
    """Compatibilité : les groupes suivent la même politique prudente que la liste."""
    return appliquer_liste_riche(ctrl)


def appliquer_grille(ctrl):
    """Style sémantique commun d'une ``wx.grid.Grid`` existante.

    Repens ne touche ni aux renderers métier, ni aux éditeurs, ni aux dimensions
    de colonnes. Seuls la typographie, les surfaces, la sélection, les traits et
    les métriques de ligne communes sont harmonisés.
    """
    try:
        import wx.grid as gridlib
        if not isinstance(ctrl, gridlib.Grid):
            return ctrl
    except Exception:
        return ctrl

    appliquer_liste(ctrl)

    for methode, valeur in (
        ("SetDefaultCellFont", police("body")),
        ("SetLabelFont", police("label")),
        ("SetGridLineColour", couleur("outline_variant")),
        ("SetLabelBackgroundColour", couleur("surface_container_low")),
        ("SetLabelTextColour", couleur("on_surface_variant")),
        ("SetDefaultCellBackgroundColour", couleur("surface_container_lowest")),
        ("SetDefaultCellTextColour", couleur("on_surface")),
        ("SetSelectionBackground", couleur("selection")),
        ("SetSelectionForeground", couleur("selection_text")),
    ):
        try:
            getattr(ctrl, methode)(valeur)
        except Exception:
            pass

    try:
        ctrl.EnableGridLines(True)
    except Exception:
        pass

    try:
        if not hasattr(ctrl, "_noethys_default_row_base"):
            ctrl._noethys_default_row_base = ctrl.GetDefaultRowSize()
        ctrl.SetDefaultRowSize(
            max(hauteur_ligne("table"), px(ctrl._noethys_default_row_base)),
            True,
        )
    except Exception:
        pass

    for getter, setter, attribut in (
        ("GetRowLabelSize", "SetRowLabelSize", "_noethys_row_label_base"),
        ("GetColLabelSize", "SetColLabelSize", "_noethys_col_label_base"),
    ):
        try:
            if not hasattr(ctrl, attribut):
                setattr(ctrl, attribut, getattr(ctrl, getter)())
            getattr(ctrl, setter)(px(getattr(ctrl, attribut)))
        except Exception:
            pass

    return ctrl


def tokens():
    """Expose les tokens utiles pour diagnostic/tests sans dépendre d'un écran."""
    return {
        "surface": couleur("surface"),
        "surface_container": couleur("surface_container"),
        "surface_container_low": couleur("surface_container_low"),
        "on_surface": couleur("on_surface"),
        "outline_variant": couleur("outline_variant"),
        "primary": couleur("primary"),
        "spacing_1": espace(1),
        "spacing_2": espace(2),
        "spacing_3": espace(3),
        "radius_control": rayon("controle"),
        "radius_surface": rayon("surface"),
        "action_compact": cible_action("compact"),
        "action_standard": cible_action("standard"),
        "icon_toolbar": taille_icone("toolbar"),
        "panel_secondary": hauteur_panneau("secondary"),
        "font_display": police("display"),
        "font_h1": police("h1"),
        "font_h2": police("h2"),
        "font_h3": police("h3"),
        "font_body": police("body"),
        "font_data_large": police("data_large"),
    }
