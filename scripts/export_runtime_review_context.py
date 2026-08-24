#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exporte le contexte source des alertes runtime encore classées ``review``."""

from __future__ import annotations

import json
from pathlib import Path

from scripts import audit_runtime_hardening as hardening


def _context(relpath: str, line: int, before: int = 16, after: int = 8) -> dict:
    path = hardening.ROOT / relpath
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {"start": 0, "end": 0, "text": ""}
    start = max(1, line - before)
    end = min(len(lines), line + after)
    numbered = [f"{index:05d}: {lines[index - 1]}" for index in range(start, end + 1)]
    return {"start": start, "end": end, "text": "\n".join(numbered)}


def build_report() -> dict:
    report = hardening.build_report()
    reviews = []
    for kind in ("RESULT_UNGUARDED", "RESULT_ASSIGN"):
        for item in report["findings"][kind]:
            if item.get("classification") != "review":
                continue
            line = item.get("line") or item.get("line_access") or item.get("line_assign") or 1
            enriched = dict(item)
            enriched["kind"] = kind
            enriched["context"] = _context(item["file"], int(line))
            reviews.append(enriched)
    return {
        "count": len(reviews),
        "reviews": reviews,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", required=True, metavar="FILE")
    args = parser.parse_args()
    report = build_report()
    path = Path(args.json)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{report['count']} alerte(s) prioritaire(s) exportée(s) vers {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
