#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit statique + runtime des usages wxPython Classic encore présents.

L'objectif n'est pas de réécrire automatiquement l'interface. Le script dresse
un inventaire reproductible des API historiques, distingue celles déjà
couvertes par les hooks du portable PyInstaller et celles qui nécessitent une
qualification manuelle.

Usage :
    python scripts/audit_wxphoenix_compat.py
    python scripts/audit_wxphoenix_compat.py --runtime
    python scripts/audit_wxphoenix_compat.py --json tmp/wxphoenix-audit.json
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
THIRD_PARTY_DIRS = {"ObjectListView", "Outils"}

# Catégories volontairement conservatrices : un match n'implique pas un bug.
# ``hooked`` signifie qu'un alias de compatibilité existe déjà dans
# packaging/runtime_wx_compat.py pour le portable Windows.
PATTERNS = {
    "wx.EmptyBitmap": {"kind": "classic_alias", "hooked": True, "modern": "wx.Bitmap"},
    "wx.EmptyIcon": {"kind": "classic_alias", "hooked": True, "modern": "wx.Icon"},
    "wx.EmptyImage": {"kind": "classic_alias", "hooked": True, "modern": "wx.Image"},
    "wx.BitmapFromImage": {"kind": "classic_alias", "hooked": True, "modern": "wx.Bitmap"},
    "wx.NewId": {"kind": "classic_alias", "hooked": True, "modern": "wx.NewIdRef"},
    "wx.PySimpleApp": {"kind": "removed_classic", "hooked": False, "modern": "wx.App"},
    "wx.NamedColour": {"kind": "removed_classic", "hooked": False, "modern": "wx.Colour"},
    "wx.StockCursor": {"kind": "classic_api", "hooked": False, "modern": "wx.Cursor"},
    "wx.SystemSettings_GetColour": {"kind": "classic_api", "hooked": False, "modern": "wx.SystemSettings.GetColour"},
    "wx.SystemSettings_GetFont": {"kind": "classic_api", "hooked": False, "modern": "wx.SystemSettings.GetFont"},
    "wx.SystemSettings_GetMetric": {"kind": "classic_api", "hooked": False, "modern": "wx.SystemSettings.GetMetric"},
    ".SetToolTipString(": {"kind": "classic_method", "hooked": False, "modern": ".SetToolTip("},
    ".InsertStringItem(": {"kind": "classic_method", "hooked": False, "modern": ".InsertItem("},
    ".SetStringItem(": {"kind": "classic_method", "hooked": False, "modern": ".SetItem("},
    "wx.InitAllImageHandlers": {"kind": "obsolete_noop", "hooked": False, "modern": "remove / no-op with Phoenix"},
    "from wx import gizmos": {"kind": "classic_import", "hooked": False, "modern": "qualify replacement"},
    "import wx.gizmos": {"kind": "classic_import", "hooked": False, "modern": "qualify replacement"},
}


def scope_for(path: Path) -> str:
    rel = path.relative_to(NOETHYS)
    return "third_party" if rel.parts and rel.parts[0] in THIRD_PARTY_DIRS else "first_party"


def scan_file(path: Path) -> list[dict]:
    findings = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return findings

    rel = str(path.relative_to(ROOT)).replace("\\", "/")
    scope = scope_for(path)
    for lineno, raw in enumerate(lines, 1):
        code = raw.split("#", 1)[0]
        if not code.strip():
            continue
        for token, meta in PATTERNS.items():
            if token in code:
                findings.append({
                    "file": rel,
                    "line": lineno,
                    "token": token,
                    "scope": scope,
                    **meta,
                    "snippet": code.strip()[:180],
                })
    return findings


def static_audit() -> list[dict]:
    findings = []
    for path in sorted(NOETHYS.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        findings.extend(scan_file(path))
    return findings


def runtime_audit() -> dict:
    try:
        import wx
    except Exception as exc:  # pragma: no cover - dépend de l'environnement CI
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    attrs = {
        "version": wx.version(),
        "PlatformInfo": list(wx.PlatformInfo),
    }
    for name in (
        "EmptyBitmap", "EmptyIcon", "EmptyImage", "BitmapFromImage", "NewId",
        "PySimpleApp", "NamedColour", "StockCursor", "SystemSettings",
    ):
        attrs[name] = hasattr(wx, name)
    return {"available": True, "wx": attrs}


def print_report(findings: list[dict], runtime: dict | None) -> None:
    counts = Counter((f["scope"], f["kind"]) for f in findings)
    print("Audit wxPython Phoenix")
    print("=====================")
    print(f"Occurrences statiques : {len(findings)}")
    for (scope, kind), count in sorted(counts.items()):
        print(f"  {scope:11s} {kind:18s}: {count}")

    print("\nDétail first-party :")
    first_party = [f for f in findings if f["scope"] == "first_party"]
    if not first_party:
        print("  aucun motif Classic connu détecté")
    else:
        for f in first_party:
            hook = "hook portable" if f["hooked"] else "à qualifier"
            print(f"  {f['file']}:{f['line']}: {f['token']} -> {f['modern']} [{hook}]")

    third_count = sum(1 for f in findings if f["scope"] == "third_party")
    if third_count:
        print(f"\nDépendances embarquées : {third_count} occurrence(s) Classic inventoriée(s).")

    if runtime is not None:
        print("\nRuntime Phoenix :")
        print(json.dumps(runtime, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", action="store_true", help="importe wx et vérifie les attributs Phoenix")
    parser.add_argument("--json", type=Path, help="écrit le rapport JSON")
    args = parser.parse_args()

    findings = static_audit()
    runtime = runtime_audit() if args.runtime else None
    payload = {"findings": findings, "runtime": runtime}

    print_report(findings, runtime)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Audit informatif : on fige d'abord l'inventaire avant d'abaisser des seuils.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
