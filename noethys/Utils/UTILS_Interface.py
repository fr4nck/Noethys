#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-16 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------

import sys
import wx

from Utils.UTILS_Traduction import _
from Utils import UTILS_Customize
from Utils import UTILS_Config


THEMES = [
    ("Vert", _(u"Vert (Par défaut)")),
    ("Bleu", _(u"Bleu")),
    ("Noir", _(u"Noir")),
]

APPARENCES = [
    ("systeme", _(u"Système")),
    ("clair", _(u"Clair")),
    ("sombre", _(u"Sombre")),
]

ECHELLES = (80, 90, 100, 110, 125, 150, 175, 200)

DONNEES = {

    "Vert" : {
        "couleur_tres_foncee" : wx.Colour(33, 104, 0), # Fond Astuces page d'accueil
        "couleur_claire" : wx.Colour(137, 206, 27), # Texte du splash screen
        "couleur_tres_claire" : wx.Colour(240, 251, 237), # Lignes des listes
        "couleur_tres_claire_2" : wx.Colour(214, 250, 199), # Cadre Contacts de la fiche famille
    },

    "Bleu" : {
        "couleur_tres_foncee" : wx.Colour(0, 50, 95),
        "couleur_claire" : wx.Colour(0, 121, 204),
        "couleur_tres_claire" : wx.Colour(234, 240, 255),
        "couleur_tres_claire_2" : wx.Colour(211, 224, 250),
    },

    "Noir" : {
        "couleur_tres_foncee" : wx.Colour(0, 0, 0),
        "couleur_claire" : wx.Colour(150, 150, 150),
        "couleur_tres_claire" : wx.Colour(240, 240, 240),
        "couleur_tres_claire_2" : wx.Colour(230, 230, 230),
    },

}

# Palette sombre inspirée des rôles de couleur Material Design 3.
# L'objectif n'est pas de transformer wxPython en Material, mais d'utiliser
# la même logique : surfaces hiérarchisées, texte non blanc pur, contours
# modérés et couleurs métier conservées comme des signaux sémantiques.
PALETTE_SOMBRE = {
    "surface": wx.Colour(20, 18, 24),
    "surface_container_lowest": wx.Colour(15, 13, 19),
    "surface_container_low": wx.Colour(29, 27, 32),
    "surface_container": wx.Colour(33, 31, 38),
    "surface_container_high": wx.Colour(43, 41, 48),
    "surface_container_highest": wx.Colour(54, 52, 59),
    "on_surface": wx.Colour(230, 224, 233),
    "on_surface_variant": wx.Colour(202, 196, 208),
    "outline": wx.Colour(147, 143, 153),
    "outline_variant": wx.Colour(73, 69, 79),
    "selection": wx.Colour(55, 74, 48),
    "selection_texte": wx.Colour(232, 247, 225),
    "metier_vert": wx.Colour(47, 72, 47),
    "metier_vert_texte": wx.Colour(204, 232, 201),
    "metier_jaune": wx.Colour(78, 68, 38),
    "metier_jaune_texte": wx.Colour(240, 224, 174),
    "metier_rouge": wx.Colour(82, 47, 49),
    "metier_rouge_texte": wx.Colour(245, 197, 199),
    "fond": wx.Colour(20, 18, 24),
    "fond_controle": wx.Colour(33, 31, 38),
    "texte": wx.Colour(230, 224, 233),
    "texte_secondaire": wx.Colour(202, 196, 208),
    "bordure": wx.Colour(73, 69, 79),
}

ACCENTS_SOMBRES = {
    "Vert": {
        "primary": wx.Colour(177, 214, 154),
        "on_primary": wx.Colour(34, 57, 23),
        "primary_container": wx.Colour(57, 81, 44),
        "on_primary_container": wx.Colour(205, 238, 181),
    },
    "Bleu": {
        "primary": wx.Colour(169, 199, 255),
        "on_primary": wx.Colour(0, 48, 92),
        "primary_container": wx.Colour(31, 71, 116),
        "on_primary_container": wx.Colour(213, 227, 255),
    },
    "Noir": {
        "primary": wx.Colour(202, 196, 208),
        "on_primary": wx.Colour(50, 47, 53),
        "primary_container": wx.Colour(73, 69, 79),
        "on_primary_container": wx.Colour(232, 222, 237),
    },
}

_GESTIONNAIRE_AFFICHAGE = None
_ID_MENU_AFFICHAGE = wx.Window.NewControlId()


def _normalise_echelle(valeur, defaut=100):
    try:
        valeur = int(valeur)
    except (TypeError, ValueError):
        valeur = defaut
    return min(ECHELLES, key=lambda item: abs(item - valeur))


def GetEchelle():
    return _normalise_echelle(UTILS_Config.GetParametre("interface_echelle_pct", 100))


def SetEchelle(valeur=100):
    valeur = _normalise_echelle(valeur)
    UTILS_Config.SetParametre("interface_echelle_pct", valeur)
    return valeur


def GetApparence():
    valeur = UTILS_Config.GetParametre("interface_apparence", "systeme")
    if valeur not in [code for code, label in APPARENCES]:
        valeur = "systeme"
    return valeur


def SetApparence(valeur="systeme"):
    if valeur not in [code for code, label in APPARENCES]:
        valeur = "systeme"
    UTILS_Config.SetParametre("interface_apparence", valeur)
    return valeur


def SystemeEstSombre():
    """Retourne le mode sombre choisi pour les applications par le système."""
    if sys.platform.startswith("win"):
        try:
            import winreg
            chemin = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, chemin) as cle:
                valeur, _type = winreg.QueryValueEx(cle, "AppsUseLightTheme")
            return int(valeur) == 0
        except Exception:
            pass

    try:
        apparence = wx.SystemSettings.GetAppearance()
        if hasattr(apparence, "AreAppsDark"):
            return bool(apparence.AreAppsDark())
        if hasattr(apparence, "IsDark"):
            return bool(apparence.IsDark())
    except Exception:
        pass
    return False


def EstSombre(apparence=None):
    if apparence is None:
        apparence = GetApparence()
    if apparence == "sombre":
        return True
    if apparence == "clair":
        return False
    return SystemeEstSombre()


def GetTheme():
    InstallerGestionAffichage()
    return UTILS_Customize.GetValeur("interface", "theme", "Vert")


def SetTheme(theme="Vert"):
    if theme not in [code for code, label in THEMES]:
        theme = "Vert"
    UTILS_Customize.SetValeur("interface", "theme", theme)


def GetValeur(cle="", defaut="", theme=None):
    InstallerGestionAffichage()
    if theme == None :
        theme = UTILS_Customize.GetValeur("interface", "theme", "Vert")

    if theme in DONNEES :
        if cle in DONNEES[theme]:
            return DONNEES[theme][cle]

    return defaut


def GetCouleurRole(role="surface", sombre=None, theme=None, defaut=None):
    """Retourne une couleur sémantique d'interface."""
    if sombre is None:
        sombre = EstSombre()
    if theme is None:
        theme = UTILS_Customize.GetValeur("interface", "theme", "Vert")

    if sombre:
        if role in PALETTE_SOMBRE:
            return PALETTE_SOMBRE[role]
        if role in ACCENTS_SOMBRES.get(theme, {}):
            return ACCENTS_SOMBRES[theme][role]

    if role in ("primary", "primary_container"):
        return GetValeur("couleur_claire", wx.Colour(137, 206, 27), theme=theme)
    if role in ("on_surface", "on_surface_variant", "selection_texte"):
        return wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)
    if role in ("outline", "outline_variant"):
        return wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DSHADOW)
    if role == "surface":
        return wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE)
    if role.startswith("surface_container"):
        return wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
    if role == "selection":
        return wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
    return defaut if defaut is not None else wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)


def _couleur_identique(couleur1, couleur2):
    try:
        return tuple(couleur1.Get())[:3] == tuple(couleur2.Get())[:3]
    except Exception:
        return False


def _couleur_proche(couleur, reference, tolerance=8):
    try:
        c1 = tuple(couleur.Get())[:3]
        c2 = tuple(reference.Get())[:3]
        return all(abs(a - b) <= tolerance for a, b in zip(c1, c2))
    except Exception:
        return False


def _memorise_base(window, attribut, valeur):
    if not hasattr(window, attribut):
        try:
            setattr(window, attribut, valeur)
        except Exception:
            pass
    return getattr(window, attribut, valeur)


def _appliquer_police(window, facteur):
    try:
        police = window.GetFont()
        if not police or not police.IsOk():
            return

        taille = police.GetFractionalPointSize() if hasattr(police, "GetFractionalPointSize") else float(police.GetPointSize())
        if taille <= 0:
            return

        parent = window.GetParent()
        base = getattr(window, "_noethys_taille_police_base", None)
        if base is None:
            if parent is not None and hasattr(parent, "_noethys_taille_police_base"):
                try:
                    taille_parent = parent.GetFont().GetFractionalPointSize() if hasattr(parent.GetFont(), "GetFractionalPointSize") else float(parent.GetFont().GetPointSize())
                    if abs(taille - taille_parent) < 0.05:
                        base = float(parent._noethys_taille_police_base)
                except Exception:
                    pass
            if base is None:
                base = float(taille)
            try:
                window._noethys_taille_police_base = base
            except Exception:
                pass

        cible = max(5.0, base * facteur)
        if abs(taille - cible) < 0.05:
            return

        nouvelle = wx.Font(police)
        if hasattr(nouvelle, "SetFractionalPointSize"):
            nouvelle.SetFractionalPointSize(cible)
        else:
            nouvelle.SetPointSize(max(5, int(round(cible))))
        window.SetFont(nouvelle)
        try:
            window.InvalidateBestSize()
        except Exception:
            pass
    except Exception:
        pass


def _appliquer_dimensions_speciales(window, facteur):
    """Agrandit les métriques verticales utiles sans gonfler toutes les colonnes."""
    if hasattr(window, "GetDefaultRowSize") and hasattr(window, "SetDefaultRowSize"):
        try:
            valeur = _memorise_base(window, "_noethys_hauteur_ligne_base", window.GetDefaultRowSize())
            cible = max(1, int(round(valeur * facteur)))
            try:
                window.SetDefaultRowSize(cible, True)
            except TypeError:
                window.SetDefaultRowSize(cible)
        except Exception:
            pass


def _fond_est_legacy_clair(couleur):
    theme = UTILS_Customize.GetValeur("interface", "theme", "Vert")
    references = [
        wx.Colour(255, 255, 255),
        wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE),
        wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW),
    ]
    if theme in DONNEES:
        references.extend([
            DONNEES[theme].get("couleur_tres_claire"),
            DONNEES[theme].get("couleur_tres_claire_2"),
        ])
    for reference in references:
        if reference is not None and _couleur_proche(couleur, reference):
            return True
    return False


def _appliquer_palette_liste(window):
    surface_pair = PALETTE_SOMBRE["surface_container_lowest"]
    surface_impair = PALETTE_SOMBRE["surface_container_low"]

    for attribut, valeur in (
        ("evenRowsBackColor", surface_pair),
        ("oddRowsBackColor", surface_impair),
    ):
        if hasattr(window, attribut):
            try:
                setattr(window, attribut, valeur)
            except Exception:
                pass

    try:
        window.SetBackgroundColour(surface_pair)
        window.SetForegroundColour(PALETTE_SOMBRE["on_surface"])
    except Exception:
        pass

    try:
        if hasattr(window, "stEmptyListMsg"):
            window.stEmptyListMsg.SetBackgroundColour(surface_pair)
            window.stEmptyListMsg.SetForegroundColour(PALETTE_SOMBRE["on_surface_variant"])
            window.stEmptyListMsg.Refresh()
    except Exception:
        pass

    try:
        nbre = window.GetItemCount()
        if nbre <= 2000:
            for index in range(nbre):
                couleur = window.GetItemBackgroundColour(index)
                if not couleur.IsOk() or _fond_est_legacy_clair(couleur):
                    window.SetItemBackgroundColour(index, surface_pair if index % 2 == 0 else surface_impair)
    except Exception:
        pass


def _appliquer_couleurs(window, sombre):
    if not sombre:
        return

    try:
        fond_actuel = window.GetBackgroundColour()
        texte_actuel = window.GetForegroundColour()
    except Exception:
        return

    fond_bouton_systeme = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE)
    fond_fenetre_systeme = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
    texte_systeme = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)

    fond_est_standard = (
        _couleur_identique(fond_actuel, fond_bouton_systeme)
        or _couleur_identique(fond_actuel, fond_fenetre_systeme)
        or _fond_est_legacy_clair(fond_actuel)
        or not fond_actuel.IsOk()
    )
    texte_est_standard = (
        _couleur_identique(texte_actuel, texte_systeme)
        or _couleur_proche(texte_actuel, wx.Colour(0, 0, 0), tolerance=20)
        or not texte_actuel.IsOk()
    )

    nom_classe = window.__class__.__name__.lower()

    if any(mot in nom_classe for mot in ("objectlistview", "listctrl", "listview")):
        _appliquer_palette_liste(window)
        return

    if any(mot in nom_classe for mot in ("textctrl", "treectrl", "choice", "combobox", "spin", "checklist", "grid")):
        role_fond = "surface_container_low"
    elif any(mot in nom_classe for mot in ("button", "togglebutton", "bitmapbutton")):
        role_fond = "surface_container_high"
    elif any(mot in nom_classe for mot in ("toolbar", "auitoolbar", "notebook", "choicebook", "listbook")):
        role_fond = "surface_container"
    elif any(mot in nom_classe for mot in ("dialog", "frame", "panel", "scrolledwindow", "staticbox")):
        role_fond = "surface"
    else:
        role_fond = "surface"

    if fond_est_standard:
        try:
            window.SetBackgroundColour(PALETTE_SOMBRE[role_fond])
        except Exception:
            pass
    if texte_est_standard and fond_est_standard:
        try:
            window.SetForegroundColour(PALETTE_SOMBRE["on_surface"])
        except Exception:
            pass


def _appliquer_barre_titre_sombre(window, sombre):
    """Active la barre de titre sombre sous Windows 10/11 quand disponible."""
    if not sombre or not sys.platform.startswith("win"):
        return
    if not isinstance(window, wx.TopLevelWindow):
        return
    try:
        import ctypes
        hwnd = int(window.GetHandle())
        valeur = ctypes.c_int(1)
        for attribut in (20, 19):
            resultat = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attribut, ctypes.byref(valeur), ctypes.sizeof(valeur)
            )
            if resultat == 0:
                break
    except Exception:
        pass


def AppliquerAffichage(window, recursif=True):
    if window is None:
        return
    facteur = GetEchelle() / 100.0
    sombre = EstSombre()

    _appliquer_police(window, facteur)
    _appliquer_dimensions_speciales(window, facteur)
    _appliquer_couleurs(window, sombre)
    _appliquer_barre_titre_sombre(window, sombre)

    if recursif:
        try:
            enfants = window.GetChildren()
        except Exception:
            enfants = []
        for enfant in enfants:
            AppliquerAffichage(enfant, recursif=True)

    if isinstance(window, wx.TopLevelWindow):
        try:
            window.Layout()
            window.Refresh()
        except Exception:
            pass


def AppliquerAffichageGlobal():
    try:
        fenetres = wx.GetTopLevelWindows()
    except Exception:
        fenetres = []
    for fenetre in fenetres:
        AppliquerAffichage(fenetre, recursif=True)


def _ouvrir_reglages_affichage(parent):
    from Dlg import DLG_Echelle_interface
    valeur = DLG_Echelle_interface.Ouvrir(parent)
    if valeur is not None:
        dlg = wx.MessageDialog(
            parent,
            _(u"Les nouveaux réglages d'affichage seront appliqués complètement au prochain démarrage de Noethys."),
            _(u"Affichage"),
            wx.OK | wx.ICON_INFORMATION,
        )
        dlg.ShowModal()
        dlg.Destroy()


def _installer_menu_affichage():
    try:
        app = wx.GetApp()
        parent = app.GetTopWindow() if app else None
        if parent is None:
            return
        if getattr(parent, "_noethys_menu_affichage_installe", False):
            return
        barre = parent.GetMenuBar()
        if barre is None:
            return

        menu_cible = None
        for index in range(barre.GetMenuCount()):
            label = barre.GetMenuLabel(index).replace("&", "").lower()
            if "affichage" in label:
                menu_cible = barre.GetMenu(index)
                break
        if menu_cible is None:
            return

        menu_cible.AppendSeparator()
        menu_cible.Append(
            _ID_MENU_AFFICHAGE,
            _(u"Échelle et apparence…\tCtrl+Alt+Z"),
            _(u"Ajuster la taille de l'interface et le mode clair/sombre."),
        )
        parent.Bind(
            wx.EVT_MENU,
            lambda event: _ouvrir_reglages_affichage(parent),
            id=_ID_MENU_AFFICHAGE,
        )
        parent._noethys_menu_affichage_installe = True
    except Exception as err:
        print("Impossible d'ajouter le menu d'affichage : %s" % err)


class _GestionnaireAffichage(wx.EventFilter):
    """Applique l'affichage aux fenêtres créées après le démarrage."""
    def __init__(self):
        wx.EventFilter.__init__(self)
        self.type_creation = wx.EVT_WINDOW_CREATE.typeId
        wx.EvtHandler.AddFilter(self)

    def FilterEvent(self, event):
        if event.GetEventType() == self.type_creation:
            try:
                window = event.GetWindow()
                if window is not None:
                    wx.CallAfter(AppliquerAffichage, window, False)
                    if isinstance(window, wx.TopLevelWindow):
                        wx.CallLater(150, AppliquerAffichage, window, True)
            except Exception:
                pass
        return self.Event_Skip


def InstallerGestionAffichage():
    global _GESTIONNAIRE_AFFICHAGE
    try:
        app = wx.GetApp()
    except Exception:
        app = None
    if app is None:
        return

    if _GESTIONNAIRE_AFFICHAGE is None:
        try:
            _GESTIONNAIRE_AFFICHAGE = _GestionnaireAffichage()
            wx.CallAfter(AppliquerAffichageGlobal)
            wx.CallAfter(_installer_menu_affichage)
        except Exception as err:
            print("Initialisation de l'affichage impossible : %s" % err)


if __name__ == '__main__':
    print(GetValeur("couleur_tres_fonce", wx.Colour(255, 0, 0)))
