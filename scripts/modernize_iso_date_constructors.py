#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOETHYS = ROOT / "noethys"

# Ne transforme que le motif strict : datetime.date(int(x[:4]), int(x[5:7]), int(x[8:10]))
# avec exactement la même expression x dans les trois tranches.
PATTERN = re.compile(
    r"datetime\.date\(int\((?P<expr>[A-Za-z_][A-Za-z0-9_\.\[\]'\"]*)\[:4\]\),\s*"
    r"int\((?P=expr)\[5:7\]\),\s*int\((?P=expr)\[8:10\]\)\)"
)

changed_files = 0
replacements = 0
for path in sorted(NOETHYS.rglob("*.py")):
    text = path.read_text(encoding="utf-8", errors="strict")
    new_text, count = PATTERN.subn(r"datetime.date.fromisoformat(\g<expr>[:10])", text)
    if count:
        path.write_text(new_text, encoding="utf-8")
        print(f"corrigé: {path.relative_to(ROOT)} ({count})")
        changed_files += 1
        replacements += count

print(f"{replacements} remplacement(s) dans {changed_files} fichier(s)")
