#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPLACEMENTS = {
    "noethys/ObjectListView/ObjectListView.py": [
        ("self.stEmptyListMsg.SetSize(0, sz.GetHeight() / 3,", "self.stEmptyListMsg.SetSize(0, int(sz.GetHeight() / 3),"),
    ],
    "noethys/Outils/ultimatelistctrl.py": [
        ("wx.Rect(theX + HEADER_OFFSET_X, HEADER_OFFSET_Y + (h - 4 - iy)/2, ix, iy)", "wx.Rect(theX + HEADER_OFFSET_X, int(HEADER_OFFSET_Y + (h - 4 - iy)/2), ix, iy)"),
        ("wx.Rect(HEADER_OFFSET_X, self.GetLineY(line) + LH/2 - hcheck/2, wcheck, hcheck)", "wx.Rect(HEADER_OFFSET_X, int(self.GetLineY(line) + LH/2 - hcheck/2), wcheck, hcheck)"),
        ("wx.Rect(xOld, lineY + LH/2 - iy/2, ix, iy)", "wx.Rect(xOld, int(lineY + LH/2 - iy/2), ix, iy)"),
    ],
    "noethys/Outils/wxSchedulerPaint.py": [
        ("wx.Point(x + 1.0 * width * dayN / daysCount,", "wx.Point(int(x + 1.0 * width * dayN / daysCount),"),
        ("y + 1.0 * height * idx / nbHours),", "int(y + 1.0 * height * idx / nbHours)),"),
        ("wx.Point(x + 1.0 * width * (dayN + 1) / daysCount,", "wx.Point(int(x + 1.0 * width * (dayN + 1) / daysCount),"),
        ("y + 1.0 * height * (idx + 1) / nbHours)))", "int(y + 1.0 * height * (idx + 1) / nbHours))))"),
        ("wx.Point(x + 1.0 * width * (nbHours * dayN + idx) / (nbHours * daysCount),", "wx.Point(int(x + 1.0 * width * (nbHours * dayN + idx) / (nbHours * daysCount)),"),
        ("wx.Point(x + 1.0 * width * (nbHours * dayN + idx + 1) / (nbHours * daysCount),", "wx.Point(int(x + 1.0 * width * (nbHours * dayN + idx + 1) / (nbHours * daysCount)),"),
    ],
    "noethys/Utils/UTILS_TL_drawing_default.py": [
        ("west_rect   = wx.Rect(x + 1             , y, SIZE, SIZE)", "west_rect   = wx.Rect(int(x + 1)             , int(y), SIZE, SIZE)"),
        ("center_rect = wx.Rect(x + rect.Width / 2, y, SIZE, SIZE)", "center_rect = wx.Rect(int(x + rect.Width / 2), int(y), SIZE, SIZE)"),
        ("east_rect   = wx.Rect(x + rect.Width - 1, y, SIZE, SIZE)", "east_rect   = wx.Rect(int(x + rect.Width - 1), int(y), SIZE, SIZE)"),
    ],
}

changed = 0
for rel, replacements in REPLACEMENTS.items():
    path = ROOT / rel
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in replacements:
        if old not in text:
            raise SystemExit(f"Motif introuvable dans {rel}: {old}")
        text = text.replace(old, new, 1)
    if text != original:
        path.write_text(text, encoding="utf-8")
        changed += 1
        print(f"corrigé: {rel}")

print(f"{changed} fichier(s) modifié(s)")
