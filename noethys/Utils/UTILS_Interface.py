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
from Utils import UTILS_DesignSystem


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

# Les anciens accès directs restent disponibles pendant la migration, mais la
# source de vérité est désormais UTILS_DesignSystem. Les alias historiques
# évitent de casser les écrans déjà migrés vers la première palette sombre.
PALETTE_CLAIRE = dict(UTILS_DesignSystem.PALETTE_CLAIRE)
PALETTE_SOMBRE = dict(UTILS_DesignSystem.PALETTE_SOMBRE)
PALETTE_SOMBRE.update({
    "selection_texte": PALETTE_SOMBRE["selection_text"],
    "metier_vert": PALETTE_SOMBRE["success"],
    "metier_vert_texte": PALETTE_SOMBRE["success_text"],
    "metier_jaune": PALETTE_SOMBRE["warning"],
    "metier_jaune_texte": PALETTE_SOMBRE["warning_text"],
    "metier_rouge": PALETTE_SOMBRE["danger"],
    "metier_rouge_texte": PALETTE_SOMBRE["danger_text"],
    "fond": PALETTE_SOMBRE["surface"],
    "fond_controle": PALETTE_SOMBRE["surface_container"],
    "texte": PALETTE_SOMBRE["on_surface"],
    "texte_secondaire": PALETTE_SOMBRE["on_surface_variant"],
    "bordure": PALETTE_SOMBRE["outline_variant"],
})
ACCENTS_CLAIRS = UTILS_DesignSystem.ACCENTS_CLAIRS
ACCENTS_SOMBRES = UTILS_DesignSystem.ACCENTS_SOMBRES

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
    """Retourne une couleur sémantique via le contrat UI/UX central."""
    if sombre is None:
        sombre = EstSombre()
    if theme is None:
        theme = UTILS_Customize.GetValeur("interface", "theme", "Vert")

    # Compatibilité avec les noms introduits avant la stabilisation du contrat.
    aliases = {
        "selection_texte": "selection_text",
        "metier_vert": "success",
        "metier_vert_texte": "success_text",
        "metier_jaune": "warning",
        "metier_jaune_texte": "warning_text",
        "metier_rouge": "danger",
        "metier_rouge_texte": "danger_text",
        "fond": "surface",
        "fond_controle": "surface_container",
        "texte": "on_surface",
        "texte_secondaire": "on_surface_variant",
        "bordure": "outline_variant",
    }
    role = aliases.get(role, role)
    couleur = UTILS_DesignSystem.GetCouleur(
        role=role,
        sombre=sombre,
        theme=theme,
        defaut=None,
    )
    if couleur is not None:
        return couleur
    return defaut if defaut is not None else wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)


def GetEtatCouleurs(etat="normal", sombre=None, theme=None):
    """Expose les états Fluent aux contrôles personnalisés Noethys."""
    if sombre is None:
        sombre = EstSombre()
    if theme is None:
        theme = UTILS_Customize.GetValeur("interface", "theme", "Vert")
    return UTILS_DesignSystem.GetEtatCouleurs(etat=etat, sombre=sombre, theme=theme)


def GetRoleComposant(window_ou_nom=""):
    """Retourne la surface sémantique recommandée pour un contrôle."""
    if isinstance(window_ou_nom, str):
        nom = window_ou_nom
    else:
        try:
            classe = window_ou_nom.__class__
            nom = "%s.%s" % (classe.__module__, classe.__name__)
        except Exception:
            nom = ""
    return UTILS_DesignSystem.GetRoleComposant(nom)


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


def _peut_remplacer_surface_liste(couleur):
    """Ne remplace que les surfaces neutres/legacy, jamais une couleur métier."""
    if couleur is None:
        return True
    try:
        if not couleur.IsOk():
            return True
    except Exception:
        return False
    return _fond_est_legacy_clair(couleur)


def _appliquer_palette_liste(window, sombre):
    """Modernise les listes communes sans écraser leurs couleurs métier."""
    surface_pair = GetCouleurRole("surface_container_lowest", sombre=sombre)
    surface_impair = GetCouleurRole("surface_container_low", sombre=sombre)
    surface_groupe = GetCouleurRole("surface_container_high", sombre=sombre)
    texte = GetCouleurRole("on_surface", sombre=sombre)
    texte_secondaire = GetCouleurRole("on_surface_variant", sombre=sombre)

    for attribut, valeur in (
        ("evenRowsBackColor", surface_pair),
        ("oddRowsBackColor", surface_impair),
    ):
        if hasattr(window, attribut):
            try:
                actuelle = getattr(window, attribut, None)
                if _peut_remplacer_surface_liste(actuelle):
                    setattr(window, attribut, valeur)
            except Exception:
                pass

    # Les GroupListView historiques imposaient un bleu fixe. On ne remplace que
    # ce défaut connu afin de préserver d'éventuelles couleurs personnalisées.
    try:
        if hasattr(window, "groupTextColour"):
            actuelle = window.groupTextColour
            if _couleur_proche(actuelle, wx.Colour(33, 33, 33), tolerance=8):
                window.groupTextColour = texte
        if hasattr(window, "groupBackgroundColour"):
            actuelle = window.groupBackgroundColour
            if _couleur_proche(actuelle, wx.Colour(159, 185, 250), tolerance=8):
                window.groupBackgroundColour = surface_groupe
    except Exception:
        pass

    try:
        fond_actuel = window.GetBackgroundColour()
        if _peut_remplacer_surface_liste(fond_actuel):
            window.SetBackgroundColour(surface_pair)
        texte_actuel = window.GetForegroundColour()
        if (
            not texte_actuel.IsOk()
            or _couleur_proche(texte_actuel, wx.Colour(0, 0, 0), tolerance=20)
            or _couleur_identique(texte_actuel, wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
        ):
            window.SetForegroundColour(texte)
    except Exception:
        pass

    try:
        if hasattr(window, "stEmptyListMsg"):
            try:
                est_active = window.IsEnabled()
            except Exception:
                est_active = True
            if est_active:
                fond_vide = surface_pair
                texte_vide = texte_secondaire
            else:
                fond_vide = GetCouleurRole("disabled", sombre=sombre)
                texte_vide = GetCouleurRole("disabled_text", sombre=sombre)
            window.stEmptyListMsg.SetBackgroundColour(fond_vide)
            window.stEmptyListMsg.SetForegroundColour(texte_vide)
            window.stEmptyListMsg.Refresh()
    except Exception:
        pass

    # Les lignes neutres deviennent réellement alternées en clair comme en
    # sombre. Les lignes portant une couleur métier explicite sont conservées.
    try:
        nbre = window.GetItemCount()
        if nbre <= 2000:
            for index in range(nbre):
                couleur = window.GetItemBackgroundColour(index)
                if _peut_remplacer_surface_liste(couleur):
                    window.SetItemBackgroundColour(index, surface_pair if index % 2 == 0 else surface_impair)
    except Exception:
        pass

    try:
        window.Refresh()
    except Exception:
        pass


def _appliquer_couleurs(window, sombre):
    nom_classe = window.__class__.__name__.lower()

    # Première migration visible en mode clair : les listes/tableaux communs
    # utilisent les surfaces sémantiques. Le reste de l'interface claire reste
    # historique tant que ses composants n'ont pas été migrés explicitement.
    if any(mot in nom_classe for mot in ("objectlistview", "listctrl", "listview")):
        _appliquer_palette_liste(window, sombre=sombre)
        return

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

    role_fond = GetRoleComposant(window)
    fond_cible = GetCouleurRole(role_fond, sombre=True)
    texte_cible = GetCouleurRole("on_surface", sombre=True)

    # L'état disabled possède désormais ses propres rôles, sans les imposer aux
    # panneaux complets pour éviter de créer de grands aplats désactivés.
    try:
        est_active = window.IsEnabled()
    except Exception:
        est_active = True
    if not est_active and role_fond not in ("surface", "surface_container"):
        fond_cible = GetCouleurRole("disabled", sombre=True)
        texte_cible = GetCouleurRole("disabled_text", sombre=True)

    if fond_est_standard:
        try:
            window.SetBackgroundColour(fond_cible)
        except Exception:
            pass
    if texte_est_standard and fond_est_standard:
        try:
            window.SetForegroundColour(texte_cible)
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
