#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Shell stable des préférences pour les écrans Windows mis à l'échelle.

Les treize panneaux et toute leur logique de validation/sauvegarde restent dans
``DLG_Preferences``. Cet adaptateur remplace uniquement la disposition à deux
colonnes par une pile verticale scrollable, ce qui laisse chaque vieux sizer à
sa taille naturelle.
"""

import importlib
import sys

import wx

from Utils import UTILS_StyleRepens as Style


Legacy = importlib.import_module("Dlg.DLG_Preferences")


class Dialog(Legacy.Dialog):
    def __init__(self, parent):
        Legacy.Dialog.__init__(self, parent)
        self._InstallerColonneStable()

    def _InstallerColonneStable(self):
        espace = Style.espace(2)
        try:
            self.contenu.Freeze()
        except Exception:
            pass

        ancien = self.contenu.GetSizer()
        if ancien is not None:
            try:
                ancien.Clear(delete_windows=False)
            except Exception:
                try:
                    ancien.Clear(False)
                except Exception:
                    pass

        colonne = wx.BoxSizer(wx.VERTICAL)
        for ctrl in (
            self.ctrl_interface,
            self.ctrl_interface_mysql,
            self.ctrl_dates,
            self.ctrl_telephones,
            self.ctrl_codesPostaux,
            self.ctrl_adresses,
        ):
            colonne.Add(ctrl, 0, wx.EXPAND | wx.BOTTOM, espace)

        colonne.Add(self.label_redemarrage, 0, wx.TOP | wx.BOTTOM, Style.espace(1))

        for ctrl in (
            self.ctrl_propose_maj,
            self.ctrl_rapport_bugs,
            self.ctrl_derniers_fichiers,
            self.ctrl_monnaie,
            self.ctrl_autodeconnect,
            self.ctrl_comptes_internet,
            self.ctrl_email,
        ):
            colonne.Add(ctrl, 0, wx.EXPAND | wx.BOTTOM, espace)

        try:
            self.contenu.SetSizer(colonne, deleteOld=True)
        except TypeError:
            self.contenu.SetSizer(colonne)

        self.contenu.SetScrollRate(max(8, espace), max(8, espace))
        self.contenu.Layout()
        self.contenu.FitInside()

        # Une colonne n'a plus besoin de la largeur de l'ancien double panneau.
        ecran = wx.GetClientDisplayRect()
        largeur = min(Style.px(860), max(Style.px(620), int(ecran.width * 0.62)))
        hauteur = min(Style.px(780), max(Style.px(540), int(ecran.height * 0.78)))
        self.SetMinSize((min(largeur, Style.px(600)), min(hauteur, Style.px(500))))
        self.SetSize((largeur, hauteur))
        self.Layout()
        self.CenterOnParent()

        try:
            self.contenu.Thaw()
        except Exception:
            pass
        self.Refresh()


try:
    setattr(sys.modules["Dlg"], "DLG_Preferences", sys.modules[__name__])
except Exception:
    pass
