# -*- coding: utf-8 -*-
"""Non-regression : Noethys SL 0.1.0 reste en apparence claire.

ModernDockArt derive les fonds, separations et bordures des couleurs
systeme Windows. Pendant la stabilisation de Noethys SL, l'application
force donc sa base AUI claire independamment du theme Windows et
neutralise les anciens profils ayant memorise l'accent Noir.
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
from Utils import UTILS_Interface  # noqa: E402


class ForceApparenceClaireAUITests(unittest.TestCase):
    def test_force_une_couleur_claire_meme_si_windows_est_clair(self):
        art = mock.Mock()
        Noethys.ForceApparenceClaireAUI(art)
        art.SetDefaultColours.assert_called_once()
        _args, kwargs = art.SetDefaultColours.call_args
        couleur = kwargs["base_colour"]
        self.assertGreater(couleur.Red(), 200)
        self.assertGreater(couleur.Green(), 200)
        self.assertGreater(couleur.Blue(), 200)

    def test_une_exception_de_lart_provider_ne_remonte_jamais(self):
        art = mock.Mock()
        art.SetDefaultColours.side_effect = RuntimeError("erreur inattendue")
        Noethys.ForceApparenceClaireAUI(art)  # ne doit pas lever


class ThemeNoethysSLTests(unittest.TestCase):
    def test_ancien_theme_noir_est_normalise_vers_vert(self):
        with mock.patch.object(
            UTILS_Interface.UTILS_Customize,
            "GetValeur",
            return_value="Noir",
        ):
            self.assertEqual(UTILS_Interface.GetTheme(), "Vert")

    def test_les_accents_clairs_restent_disponibles(self):
        self.assertEqual(UTILS_Interface._NormaliseThemeNoethysSL("Vert"), "Vert")
        self.assertEqual(UTILS_Interface._NormaliseThemeNoethysSL("Bleu"), "Bleu")


if __name__ == "__main__":
    unittest.main()
