#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
import datetime
from pathlib import Path


def _load_source():
    root = Path(__file__).resolve().parents[1]
    path = root / "noethys" / "Utils" / "UTILS_VacancesScolaires.py"
    texte = path.read_text(encoding="utf-8")
    ast.parse(texte)
    return texte


def test_zone_b_contains_ille_et_vilaine():
    texte = _load_source()
    assert '"35"' in texte
    assert '"B"' in texte


def test_2026_2027_zone_b_dates_are_bundled():
    texte = _load_source()
    assert '"2026-10-17", "2026-11-02"' in texte
    assert '"2026-12-19", "2027-01-04"' in texte
    assert '"2027-02-20", "2027-03-08"' in texte
    assert '"2027-04-17", "2027-05-03"' in texte
    assert '"2027-07-03", None' in texte


def test_dashboard_consumes_school_holiday_provider():
    root = Path(__file__).resolve().parents[1]
    texte = (root / "noethys" / "Ctrl" / "CTRL_Ephemeride.py").read_text(encoding="utf-8")
    ast.parse(texte)
    assert "UTILS_VacancesScolaires.GetZoneDepuisCodePostal" in texte
    assert "UTILS_VacancesScolaires.GetProchainePeriode" in texte
