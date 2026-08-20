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

PALETTE_SOMBRE = {
    "fond": wx.Colour(32, 32, 32),
    "fond_controle": wx.Colour(43, 43, 43),
    "texte": wx.Colour(238, 238, 238),
    "texte_secondaire": wx.Colour(190, 190, 190),
    "bordure": wx.Colour(74, 74, 74),
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
    # Windows : la valeur AppsUseLightTheme correspond au réglage
    # Paramètres > Personnalisation > Couleurs > mode d'application.
    if sys.platform.startswith("win"):
        try:
            import winreg
            chemin = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, chemin) as cle:
                valeur, _type = winreg.QueryValueEx(cle, "AppsUseLightTheme")
            return int(valeur) == 0
        except Exception:
            pass

    # Fallback wxWidgets, notamment macOS/Linux et versions récentes de wx.
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
    # lecture du thème
    if theme == None :
        theme = UTILS_Customize.GetValeur("interface", "theme", "Vert")

    # Lecture de la valeur
    if theme in DONNEES :
        if cle in DONNEES[theme]:
            return DONNEES[theme][cle]

    # Sinon renvoie la valeur par défaut
    return defaut


def _couleur_identique(couleur1, couleur2):
    try:
        return tuple(couleur1.Get())[:3] == tuple(couleur2.Get())[:3]
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

        # Si le contrôle vient d'être créé après son parent déjà agrandi,
        # il peut avoir hérité de la police agrandie. On réutilise alors la
        # taille de base mémorisée sur le parent pour éviter un double zoom.
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
    # wx.Grid et contrôles compatibles : hauteur des lignes.
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

    # Ne jamais écraser une couleur métier explicitement posée par Noethys
    # (cases vertes/rouges des effectifs, alertes, états, etc.).
    fond_est_standard = (
        _couleur_identique(fond_actuel, fond_bouton_systeme)
        or _couleur_identique(fond_actuel, fond_fenetre_systeme)
        or not fond_actuel.IsOk()
    )
    texte_est_standard = _couleur_identique(texte_actuel, texte_systeme) or not texte_actuel.IsOk()

    nom_classe = window.__class__.__name__.lower()
    controle_saisie = any(mot in nom_classe for mot in ("textctrl", "listctrl", "treectrl", "choice", "combobox", "spin", "grid"))

    if fond_est_standard:
        try:
            window.SetBackgroundColour(PALETTE_SOMBRE["fond_controle"] if controle_saisie else PALETTE_SOMBRE["fond"])
        except Exception:
            pass
    if texte_est_standard:
        try:
            window.SetForegroundColour(PALETTE_SOMBRE["texte"])
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
        # 20 est la valeur actuelle ; 19 couvre certaines versions antérieures.
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
