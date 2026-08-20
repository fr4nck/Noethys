#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression contract for the wxPython AGW AUI runtime patch."""

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH_SCRIPT = ROOT / "scripts" / "apply_py3_runtime_source_fixes.py"


class WxAgwAuiRuntimePatchTest(unittest.TestCase):
    def test_patch_removes_float_caption_coordinates(self):
        spec = importlib.util.find_spec("wx")
        if spec is None or not spec.origin:
            self.skipTest("wxPython is not installed in this test environment")

        subprocess.run([sys.executable, str(PATCH_SCRIPT)], cwd=str(ROOT), check=True)

        dockart = Path(spec.origin).resolve().parent / "lib" / "agw" / "aui" / "dockart.py"
        source = dockart.read_text(encoding="utf-8")

        unsafe = [
            "dc.DrawRotatedText(draw_text, rect.x+(rect.width/2)-(h/2)-diff, rect.y+rect.height-3-caption_offset, 90)",
            "dc.DrawText(draw_text, rect.x+3+caption_offset, rect.y+(rect.height/2)-(h/2)-diff)",
        ]
        safe = [
            "dc.DrawRotatedText(draw_text, int(round(rect.x+(rect.width/2)-(h/2)-diff)), int(round(rect.y+rect.height-3-caption_offset)), 90)",
            "dc.DrawText(draw_text, int(round(rect.x+3+caption_offset)), int(round(rect.y+(rect.height/2)-(h/2)-diff)))",
        ]

        for pattern in unsafe:
            self.assertNotIn(pattern, source)
        for pattern in safe:
            self.assertIn(pattern, source)


if __name__ == "__main__":
    unittest.main()
