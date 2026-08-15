#!/usr/bin/env python3
import re
from pathlib import Path

path = Path("noethys/Noethys.py")
source = path.read_text(encoding="utf-8")

import_anchor = "from Utils import UTILS_Json\n"
import_line = "from Utils import UTILS_Aui\n"
if import_line not in source:
    if source.count(import_anchor) != 1:
        raise SystemExit("ancre import UTILS_Json inattendue")
    source = source.replace(import_anchor, import_anchor + import_line, 1)

pattern = re.compile(r"self\._mgr\.LoadPerspective\((.+)\)")
lines = source.splitlines(keepends=True)
changed = 0
for index, line in enumerate(lines):
    if line.lstrip().startswith("#") or "self._mgr.LoadPerspective(" not in line:
        continue
    match = pattern.search(line)
    if match is None:
        raise SystemExit(f"LoadPerspective actif non reconnu ligne {index + 1}")
    expression = match.group(1)
    replacement = f"UTILS_Aui.ChargerPerspective(self._mgr, {expression}, self.perspective_defaut)"
    lines[index] = line[:match.start()] + replacement + line[match.end():]
    changed += 1

if changed != 6:
    raise SystemExit(f"{changed} LoadPerspective actifs modifiés, 6 attendus")

updated = "".join(lines)
active_direct = [
    (i, line.strip())
    for i, line in enumerate(updated.splitlines(), 1)
    if not line.lstrip().startswith("#") and "self._mgr.LoadPerspective(" in line
]
if active_direct:
    raise SystemExit(f"LoadPerspective directs actifs restants: {active_direct}")

path.write_text(updated, encoding="utf-8", newline="")
print("Noethys.py raccordé au garde AUI : 6 appels actifs")
