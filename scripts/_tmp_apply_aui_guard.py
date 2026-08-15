#!/usr/bin/env python3
from pathlib import Path

path = Path("noethys/Noethys.py")
source = path.read_text(encoding="utf-8")

import_anchor = "from Utils import UTILS_Json\n"
import_line = "from Utils import UTILS_Aui\n"
if import_line not in source:
    if source.count(import_anchor) != 1:
        raise SystemExit("ancre import UTILS_Json inattendue")
    source = source.replace(import_anchor, import_anchor + import_line, 1)

old = "self._mgr.LoadPerspective("
expected = 4
count = source.count(old)
if count != expected:
    raise SystemExit(f"{count} LoadPerspective directs détectés, {expected} attendus")
source = source.replace(old, "UTILS_Aui.ChargerPerspective(self._mgr, ")

# Chaque appel doit désormais recevoir la perspective par défaut comme fallback.
replacements = {
    'UTILS_Aui.ChargerPerspective(self._mgr, self.perspective_defaut)':
        'UTILS_Aui.ChargerPerspective(self._mgr, self.perspective_defaut, self.perspective_defaut)',
    'UTILS_Aui.ChargerPerspective(self._mgr, self.perspectives[self.perspective_active]["perspective"])':
        'UTILS_Aui.ChargerPerspective(self._mgr, self.perspectives[self.perspective_active]["perspective"], self.perspective_defaut)',
    'UTILS_Aui.ChargerPerspective(self._mgr, self.perspectives[index]["perspective"])':
        'UTILS_Aui.ChargerPerspective(self._mgr, self.perspectives[index]["perspective"], self.perspective_defaut)',
}
for before, after in replacements.items():
    if before not in source:
        raise SystemExit(f"motif absent: {before}")
    source = source.replace(before, after)

if "self._mgr.LoadPerspective(" in source:
    raise SystemExit("un LoadPerspective direct subsiste")

path.write_text(source, encoding="utf-8", newline="")
print("Noethys.py raccordé au garde AUI")
