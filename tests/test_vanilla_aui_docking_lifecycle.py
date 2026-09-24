# -*- coding: utf-8 -*-
"""Caractérisation wxAGW 4.2.5 : cycle de docking et minimisation AUI.

Ces tests figent deux défauts reproduits pendant la recette Windows de
Noethys SL wx avant leur correction locale :

- AuiManager.OnCaptureLost() annule le drag et masque le hint, mais laisse
  visibles les docking guides top-level ;
- LoadPerspective() peut laisser une toolbar automatique <pane>_min encore
  gérée, ce qui provoque un warning au prochain MinimizePane().

Ils ciblent volontairement le AuiManager wxAGW brut. Les tests de
non-régression du correctif Noethys SL seront ajoutés séparément.
"""
from __future__ import annotations

import sys
import unittest
import warnings
from pathlib import Path

NOETHYS_DIR = Path(__file__).resolve().parents[1] / "noethys"
if str(NOETHYS_DIR) not in sys.path:
    sys.path.insert(0, str(NOETHYS_DIR))

import wx  # noqa: E402
import wx.lib.agw.aui as aui  # noqa: E402
from wx.lib.agw.aui import framemanager as fm  # noqa: E402

_APP = wx.App(False)


class _FakeHost:
    def __init__(self):
        self._shown = True

    def IsShown(self):
        return self._shown

    def Hide(self):
        self._shown = False


class _FakeGuide:
    def __init__(self):
        self.host = _FakeHost()


class AuiAgw425CaracterisationTests(unittest.TestCase):

    def setUp(self):
        self.frame = wx.Frame(None)
        self.mgr = aui.AuiManager()
        self.mgr.SetManagedWindow(self.frame)

    def tearDown(self):
        try:
            self.mgr.UnInit()
        finally:
            self.frame.Destroy()

    def test_capture_lost_agw_brut_laisse_les_guides_visibles(self):
        guides = [_FakeGuide() for _ in range(5)]
        self.mgr._guides = guides
        self.mgr._action = fm.actionDragFloatingPane

        self.mgr.OnCaptureLost(None)

        self.assertEqual(self.mgr._action, fm.actionNone)
        self.assertTrue(
            all(guide.host.IsShown() for guide in guides),
            "wxAGW 4.2.5 brut devrait caractériser la fuite des docking guides",
        )

    def test_load_perspective_laisse_un_min_et_provoque_le_warning_suivant(self):
        panneau = wx.Panel(self.frame)
        self.mgr.AddPane(
            panneau,
            aui.AuiPaneInfo()
            .Name("ephemeride")
            .Caption("Ephéméride")
            .Left()
            .MinimizeButton(True)
            .BestSize((250, 150)),
        )
        self.mgr.Update()

        perspective_defaut = self.mgr.SavePerspective()
        pane = self.mgr.GetPane("ephemeride")

        self.mgr.MinimizePane(pane)
        self.assertTrue(self.mgr.GetPane("ephemeride_min").IsOk())

        self.mgr.LoadPerspective(perspective_defaut)
        self.assertTrue(
            self.mgr.GetPane("ephemeride_min").IsOk(),
            "wxAGW 4.2.5 laisse la toolbar automatique _min encore gérée",
        )

        with warnings.catch_warnings(record=True) as captures:
            warnings.simplefilter("always")
            self.mgr.MinimizePane(self.mgr.GetPane("ephemeride"))

        textes = [str(item.message) for item in captures]
        self.assertTrue(
            any("ephemeride_min" in texte and "already exists" in texte for texte in textes),
            "la seconde minimisation doit reproduire le warning observé en recette",
        )


if __name__ == "__main__":
    unittest.main()
