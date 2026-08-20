#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------
# Correctifs de layout pour le paramétrage des colonnes de commandes de repas.
#
# Les écrans historiques utilisent des FlexGridSizer extensibles mais ajoutent
# les contrôles principaux avec ALIGN_CENTER_VERTICAL | EXPAND et une hauteur
# minimale de seulement 50 px. Sur une fenêtre agrandie, la ligne grandit mais
# le contrôle reste visuellement tassé au milieu d'un grand espace vide.
#
# Ce module applique un correctif local et réversible sans modifier les données
# ni le fonctionnement métier des modèles de commandes.
# -----------------------------------------------------------

import wx

from Dlg import DLG_Saisie_commandes_colonne as legacy

_INSTALLE = False


def _RendSelectionExtensible(panel, controle, hauteur_min=220):
    """Donne réellement toute la cellule extensible au gros contrôle de choix."""
    try:
        controle.SetMinSize((100, hauteur_min))
    except Exception:
        pass

    try:
        sizer = panel.GetSizer()
        item = sizer.GetItem(controle) if sizer is not None else None
        if item is not None:
            # ALIGN_CENTER_VERTICAL est contradictoire avec le rôle de cette
            # zone : elle doit remplir la ligne déclarée GrowableRow.
            item.SetFlag(wx.EXPAND)
        if sizer is not None:
            sizer.Layout()
        panel.Layout()
    except Exception:
        pass


class PAGE_Unites(legacy.PAGE_Unites):
    def __init__(self, parent):
        super(PAGE_Unites, self).__init__(parent)

        # Dans un point de livraison repas, afficher d'abord les unités qui ont
        # explicitement le drapeau repas. L'utilisateur conserve la case à
        # cocher historique et peut donc réafficher toutes les activités si une
        # ancienne configuration atypique l'exige.
        try:
            if not self.check_repas.GetValue():
                self.check_repas.SetValue(True)
                self.ctrl_unites.MAJ()
        except Exception:
            pass

        _RendSelectionExtensible(self, self.ctrl_unites, hauteur_min=220)


class PAGE_Informations(legacy.PAGE_Informations):
    def __init__(self, parent):
        super(PAGE_Informations, self).__init__(parent)
        _RendSelectionExtensible(self, self.ctrl_groupes, hauteur_min=220)


class PAGE_Total(legacy.PAGE_Total):
    def __init__(self, parent):
        super(PAGE_Total, self).__init__(parent)
        _RendSelectionExtensible(self, self.ctrl_colonnes, hauteur_min=180)


def Installer():
    """Installe les pages corrigées dans le dialogue historique."""
    global _INSTALLE
    if _INSTALLE:
        return

    # CTRL_Parametres résout PAGE_* au moment où son __init__ est exécuté :
    # remplacer les références du module suffit donc à corriger les futurs
    # dialogues sans toucher aux modèles existants.
    legacy.PAGE_Unites = PAGE_Unites
    legacy.PAGE_Informations = PAGE_Informations
    legacy.PAGE_Total = PAGE_Total
    _INSTALLE = True
