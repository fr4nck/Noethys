#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit statique + runtime des usages wxPython historiques encore présents.

Le but n'est pas de réécrire automatiquement l'interface : un nom issu de
wxPython Classic n'est un problème que s'il n'est plus fourni par le runtime
Phoenix réellement utilisé. L'audit distingue donc inventaire statique et
compatibilité runtime.

Usage :
    python scripts/audit_wxphoenix_compat.py
    python scripts/audit_wxphoenix_compat.py --runtime
    python scripts/audit_wxphoenix_compat.py --runtime --fail-missing
    python scripts/audit_wxphoenix_compat.py --json tmp/wxphoenix-audit.json
"""
from __future__ import annotations

import argparse
import importlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"
THIRD_PARTY_DIRS = {"ObjectListView", "Outils"}

# Un match n'implique pas un bug. ``hooked`` indique qu'un repli existe dans
# packaging/runtime_wx_compat.py pour le portable PyInstaller.
PATTERNS = {
    "wx.EmptyBitmap": {"kind": "legacy_alias", "hooked": True, "modern": "wx.Bitmap", "runtime": "wx.EmptyBitmap"},
    "wx.EmptyIcon": {"kind": "legacy_alias", "hooked": True, "modern": "wx.Icon", "runtime": "wx.EmptyIcon"},
    "wx.EmptyImage": {"kind": "legacy_alias", "hooked": True, "modern": "wx.Image", "runtime": "wx.EmptyImage"},
    "wx.BitmapFromImage": {"kind": "legacy_alias", "hooked": True, "modern": "wx.Bitmap", "runtime": "wx.BitmapFromImage"},
    "wx.NewId": {"kind": "legacy_alias", "hooked": True, "modern": "wx.NewIdRef", "runtime": "wx.NewId"},
    "wx.PySimpleApp": {"kind": "legacy_alias", "hooked": False, "modern": "wx.App", "runtime": "wx.PySimpleApp"},
    "wx.NamedColour": {"kind": "legacy_alias", "hooked": False, "modern": "wx.Colour", "runtime": "wx.NamedColour"},
    "wx.StockCursor": {"kind": "legacy_api", "hooked": False, "modern": "wx.Cursor", "runtime": "wx.StockCursor"},
    "wx.SystemSettings_GetColour": {"kind": "legacy_api", "hooked": False, "modern": "wx.SystemSettings.GetColour", "runtime": "wx.SystemSettings_GetColour"},
    "wx.SystemSettings_GetFont": {"kind": "legacy_api", "hooked": False, "modern": "wx.SystemSettings.GetFont", "runtime": "wx.SystemSettings_GetFont"},
    "wx.SystemSettings_GetMetric": {"kind": "legacy_api", "hooked": False, "modern": "wx.SystemSettings.GetMetric", "runtime": "wx.SystemSettings_GetMetric"},
    ".SetToolTipString(": {"kind": "legacy_method", "hooked": False, "modern": ".SetToolTip(", "runtime": "wx.Window.SetToolTipString"},
    ".InsertStringItem(": {"kind": "legacy_method", "hooked": False, "modern": ".InsertItem(", "runtime": "wx.ListCtrl.InsertStringItem"},
    ".SetStringItem(": {"kind": "legacy_method", "hooked": False, "modern": ".SetItem(", "runtime": "wx.ListCtrl.SetStringItem"},
    "wx.InitAllImageHandlers": {"kind": "obsolete_noop", "hooked": False, "modern": "remove / no-op with Phoenix", "runtime": "wx.InitAllImageHandlers"},
    "from wx import gizmos": {"kind": "legacy_import", "hooked": False, "modern": "qualify replacement", "runtime": "module:wx.gizmos"},
    "import wx.gizmos": {"kind": "legacy_import", "hooked": False, "modern": "qualify replacement", "runtime": "module:wx.gizmos"},
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


def _resolve_runtime_target(wx, target: str) -> tuple[bool, str | None]:
    if target.startswith("module:"):
        module_name = target.split(":", 1)[1]
        try:
            importlib.import_module(module_name)
            return True, None
        except Exception as exc:  # pragma: no cover - dépend du build wx
            return False, f"{type(exc).__name__}: {exc}"

    parts = target.split(".")
    if not parts or parts[0] != "wx":
        return False, "cible runtime invalide"
    obj = wx
    for part in parts[1:]:
        if not hasattr(obj, part):
            return False, f"attribut absent: {part}"
        obj = getattr(obj, part)
    return True, None


def runtime_audit(findings: list[dict]) -> dict:
    try:
        import wx
    except Exception as exc:  # pragma: no cover - dépend de l'environnement CI
        return {"available": False, "error": f"{type(exc).__name__}: {exc}", "targets": {}}

    used_targets = sorted({f["runtime"] for f in findings if f["scope"] == "first_party"})
    targets = {}
    for target in used_targets:
        available, error = _resolve_runtime_target(wx, target)
        targets[target] = {"available": available}
        if error:
            targets[target]["error"] = error

    return {
        "available": True,
        "version": wx.version(),
        "PlatformInfo": list(wx.PlatformInfo),
        "targets": targets,
    }


def missing_first_party_runtime(runtime: dict | None) -> list[str]:
    if not runtime or not runtime.get("available"):
        return ["wx"]
    return [name for name, data in runtime.get("targets", {}).items() if not data.get("available")]


def print_report(findings: list[dict], runtime: dict | None) -> None:
    counts = Counter((f["scope"], f["kind"]) for f in findings)
    print("Audit wxPython Phoenix")
    print("=====================")
    print(f"Occurrences statiques : {len(findings)}")
    for (scope, kind), count in sorted(counts.items()):
        print(f"  {scope:11s} {kind:18s}: {count}")

    first_party = [f for f in findings if f["scope"] == "first_party"]
    print(f"\nOccurrences first-party : {len(first_party)}")
    for f in first_party:
        hook = "hook portable" if f["hooked"] else "runtime à vérifier"
        print(f"  {f['file']}:{f['line']}: {f['token']} -> {f['modern']} [{hook}]")

    third_count = sum(1 for f in findings if f["scope"] == "third_party")
    print(f"\nDépendances embarquées : {third_count} occurrence(s) historique(s).")

    if runtime is not None:
        print("\nRuntime Phoenix :")
        print(json.dumps(runtime, ensure_ascii=False, indent=2))
        missing = missing_first_party_runtime(runtime)
        if missing:
            print("\nAPI first-party réellement absentes du runtime :")
            for target in missing:
                print(f"  - {target}")
        else:
            print("\nToutes les API historiques first-party détectées sont fournies par ce runtime Phoenix.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", action="store_true", help="importe wx et vérifie les API effectivement utilisées")
    parser.add_argument("--fail-missing", action="store_true", help="échoue si une API first-party utilisée manque au runtime")
    parser.add_argument("--json", type=Path, help="écrit le rapport JSON")
    args = parser.parse_args()

    findings = static_audit()
    runtime = runtime_audit(findings) if args.runtime else None
    payload = {"findings": findings, "runtime": runtime}

    print_report(findings, runtime)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.fail_missing and missing_first_party_runtime(runtime):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
