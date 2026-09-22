# -*- coding: utf-8 -*-
"""Non-regression : Noethys Vanilla garde l'interface historique claire
(aucun theme sombre n'a jamais ete voulu). Une recette reelle Windows a
montre de larges bandes noires entre les panneaux du decoupage AUI
(grille consommations, calendrier, panneau reseau/Connecthys, liste
Individus, zone d'informations) sur un poste ou le mode sombre des
applications Windows est active.

Cause identifiee : wx.lib.agw.aui.ModernDockArt calcule tout le fond/
sash/gripper/bordure entre panneaux a partir d'une seule "couleur de
base" lue via les couleurs systeme Windows (SYS_COLOUR_3DFACE), qui
devient sombre/noire si Windows est en mode sombre -- Noethys n'a
jamais eu de logique de theme, c'est une consequence pure du reglage
systeme. Noethys.ForceApparenceClaireAUI() ne force une couleur claire
que si le systeme est reellement detecte en mode sombre (mecanisme
officiel wx.SystemSettings.GetAppearance().IsDark()) ; en mode clair
(cas normal), rien ne change.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

NOETHYS_DIR = Path(__file__).resolve().parents[1] / "noethys"
if str(NOETHYS_DIR) not in sys.path:
    sys.path.insert(0, str(NOETHYS_DIR))

import wx  # noqa: E402

_APP = wx.App(False)

import Noethys  # noqa: E402


class ForceApparenceClaireAUITests(unittest.TestCase):
    def test_ne_touche_a_rien_en_mode_clair(self):
        art = mock.Mock()
        with mock.patch.object(wx.SystemSettings, "GetAppearance") as faux_appearance:
            faux_appearance.return_value.IsDark.return_value = False
            Noethys.ForceApparenceClaireAUI(art)
        art.SetDefaultColours.assert_not_called()

    def test_force_une_couleur_claire_en_mode_sombre(self):
        art = mock.Mock()
        with mock.patch.object(wx.SystemSettings, "GetAppearance") as faux_appearance:
            faux_appearance.return_value.IsDark.return_value = True
            Noethys.ForceApparenceClaireAUI(art)
        art.SetDefaultColours.assert_called_once()
        _args, kwargs = art.SetDefaultColours.call_args
        couleur = kwargs["base_colour"]
        # La couleur forcée doit être réellement claire (composantes
        # hautes), pas une valeur sombre par erreur.
        self.assertGreater(couleur.Red(), 200)
        self.assertGreater(couleur.Green(), 200)
        self.assertGreater(couleur.Blue(), 200)

    def test_une_exception_de_lart_provider_ne_remonte_jamais(self):
        """ ForceApparenceClaireAUI est appelée depuis un bloc déjà
        try/except dans Noethys.py, mais elle ne doit de toute façon
        jamais lever -- une erreur ici ne doit jamais empêcher le
        démarrage de l'application. """
        art = mock.Mock()
        art.SetDefaultColours.side_effect = RuntimeError("erreur inattendue")
        with mock.patch.object(wx.SystemSettings, "GetAppearance") as faux_appearance:
            faux_appearance.return_value.IsDark.return_value = True
            Noethys.ForceApparenceClaireAUI(art)  # ne doit pas lever


if __name__ == "__main__":
    unittest.main()
