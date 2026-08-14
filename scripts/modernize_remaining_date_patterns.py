#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1] / "noethys"

patterns = [
    (
        re.compile(r"datetime\.date\(\s*int\((?P<v>[A-Za-z_][A-Za-z0-9_\.]*)\[:4\]\),\s*int\((?P=v)\[5:7\]\),\s*int\((?P=v)\[8:10\]\),?\s*\)", re.S),
        lambda m: f"datetime.date.fromisoformat({m.group('v')}[:10])",
    ),
    (
        re.compile(r"datetime\.date\(\s*year=int\((?P<v>[A-Za-z_][A-Za-z0-9_\.]*)\[:4\]\),\s*month=int\((?P=v)\[5:7\]\),\s*day=int\((?P=v)\[8:10\]\)\s*\)"),
        lambda m: f"datetime.date.fromisoformat({m.group('v')}[:10])",
    ),
    (
        re.compile(r"datetime\.date\(\s*year=int\((?P<v>[A-Za-z_][A-Za-z0-9_\.]*)\[6:10\]\),\s*month=int\((?P=v)\[3:5\]\),\s*day=int\((?P=v)\[:2\]\)\s*\)"),
        lambda m: f"datetime.datetime.strptime({m.group('v')}[:10], '%d/%m/%Y').date()",
    ),
    (
        re.compile(r"datetime\.date\(\s*int\((?P<v>[A-Za-z_][A-Za-z0-9_\.]*)\[6:10\]\),\s*int\((?P=v)\[3:5\]\),\s*int\((?P=v)\[:2\]\)\s*\)"),
        lambda m: f"datetime.datetime.strptime({m.group('v')}[:10], '%d/%m/%Y').date()",
    ),
]

changed_files = 0
replacements = 0
for path in ROOT.rglob("*.py"):
    text = path.read_text(encoding="utf-8", errors="replace")
    original = text
    for pattern, repl in patterns:
        text, count = pattern.subn(repl, text)
        replacements += count
    if text != original:
        path.write_text(text, encoding="utf-8")
        changed_files += 1
        print(f"corrigé: {path.relative_to(ROOT.parent)}")

print(f"{replacements} remplacement(s) dans {changed_files} fichier(s)")
