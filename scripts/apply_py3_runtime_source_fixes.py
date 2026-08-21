#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply the Python 3/wxPhoenix fixes proven by Windows runtime tracebacks."""

from importlib.util import find_spec
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def _replace_target(target, label, old, new, minimum=1):
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count >= minimum:
        text = text.replace(old, new)
        target.write_text(text, encoding="utf-8")
        print("patched %s (%d replacement(s))" % (label, count))
        return count
    if new in text:
        print("already fixed %s" % label)
        return 0
    raise RuntimeError("%s: expected source pattern not found: %r" % (label, old))


def replace(path, old, new, minimum=1):
    return _replace_target(ROOT / path, path, old, new, minimum=minimum)


def patch_transport():
    path = "noethys/Ctrl/CTRL_Saisie_transport.py"
    replace(path, "lambda parent=self:", "lambda parent:")
    replace(path, "            ctrl = constructeur()\n", "            ctrl = constructeur(self)\n")


def patch_images():
    replace(
        "noethys/Ol/OL_Modes_reglements.py",
        "TAILLE_IMAGE = (132/2.0, 72/2.0)",
        "TAILLE_IMAGE = (132 // 2, 72 // 2)",
    )
    replace(
        "noethys/Dlg/DLG_Emetteurs.py",
        "TAILLE_IMAGE = (132/2.0, 72/2.0)",
        "TAILLE_IMAGE = (132 // 2, 72 // 2)",
    )

    replace(
        "noethys/Utils/UTILS_Organisateur.py",
        "            hauteur = hauteur * tailleMaxi / largeur\n",
        "            hauteur = int(round(hauteur * tailleMaxi / float(largeur)))\n",
    )
    replace(
        "noethys/Utils/UTILS_Organisateur.py",
        "            largeur = largeur * tailleMaxi / hauteur\n",
        "            largeur = int(round(largeur * tailleMaxi / float(hauteur)))\n",
    )
    replace(
        "noethys/Utils/UTILS_Organisateur.py",
        "    position = (((tailleImage[0]/2.0) - (largeur/2.0)), ((tailleImage[1]/2.0) - (hauteur/2.0)))\n",
        "    position = (int(round((tailleImage[0] / 2.0) - (largeur / 2.0))), int(round((tailleImage[1] / 2.0) - (hauteur / 2.0))))\n",
    )


def _taskbar_repens_integer_safe(text):
    """Reconnaît la génération Repens qui n'a plus besoin du patch historique.

    Le correctif d'origine cherchait des lignes exactes de l'ancien TaskBar.
    La modernisation Repens calcule désormais directement rectangle, rayon et
    coordonnées texte avec des entiers ; tenter de réappliquer l'ancien patch
    doit donc être un no-op explicite et non une erreur fatale.
    """
    markers = (
        "hauteurRond = max(1, int(round(hauteurTexte + padding * 2)))",
        "int(round(largeurTexte + padding * 2 + hauteurRond / 2.0))",
        "rect = wx.Rect(int(xRond), int(yRond), int(largeurRond), int(hauteurRond))",
        "rayon = max(1, int(round(hauteurRond / 2.0)))",
        "xTexte = int(round(",
        "yTexte = int(round(",
        "dc.DrawText(texte, xTexte, yTexte)",
    )
    return all(marker in text for marker in markers)


def patch_taskbar():
    path = "noethys/Ctrl/CTRL_TaskBarIcon.py"
    target = ROOT / path
    text = target.read_text(encoding="utf-8")

    if _taskbar_repens_integer_safe(text):
        print("already fixed %s (Repens integer-safe)" % path)
        return

    replace(
        path,
        "        hauteurRond = hauteurTexte + padding * 2\n",
        "        hauteurRond = int(round(hauteurTexte + padding * 2))\n",
    )
    replace(
        path,
        "        largeurRond = largeurTexte + padding * 2 + hauteurRond/2.0\n",
        "        largeurRond = int(round(largeurTexte + padding * 2 + hauteurRond / 2.0))\n",
    )
    replace(
        path,
        "            dc.DrawRoundedRectangle(wx.Rect(xRond, yRond, largeurRond, hauteurRond), hauteurRond / 2.0)\n",
        "            dc.DrawRoundedRectangle(wx.Rect(int(round(xRond)), int(round(yRond)), int(round(largeurRond)), int(round(hauteurRond))), int(round(hauteurRond / 2.0)))\n",
    )
    replace(
        path,
        "            dc.DrawRoundedRectangleRect(wx.Rect(xRond, yRond, largeurRond, hauteurRond), hauteurRond / 2.0)\n",
        "            dc.DrawRoundedRectangleRect(wx.Rect(int(round(xRond)), int(round(yRond)), int(round(largeurRond)), int(round(hauteurRond))), int(round(hauteurRond / 2.0)))\n",
    )
    replace(
        path,
        "        dc.DrawText(texte, xTexte, yTexte)\n",
        "        dc.DrawText(texte, int(round(xTexte)), int(round(yTexte)))\n",
    )


def patch_network_access():
    replace(
        "noethys/Dlg/DLG_Utilisateurs_reseau.py",
        "                index = self.InsertItem(six.MAXSIZE, autorisationStr)\n",
        "                index = self.InsertItem(self.GetItemCount(), autorisationStr)\n",
    )


def patch_redirect():
    path = "noethys/Noethys.py"
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    marker = "class Redirect(object):"
    start = text.find(marker)
    if start == -1:
        raise RuntimeError("Noethys.py: Redirect class not found")
    tail = text[start:]
    if "    def flush(self):\n" in tail.split("\ndef main():", 1)[0]:
        print("already fixed %s Redirect.flush" % path)
        return
    old = "            self.filename.write(text)\n            self.filename.flush()\n\n\n\n"
    new = (
        "            self.filename.write(text)\n"
        "            self.filename.flush()\n\n"
        "    def flush(self):\n"
        "        if not self.filename.closed:\n"
        "            self.filename.flush()\n\n\n"
    )
    if old not in tail:
        raise RuntimeError("Noethys.py: Redirect.write tail not found")
    tail = tail.replace(old, new, 1)
    target.write_text(text[:start] + tail, encoding="utf-8")
    print("patched %s Redirect.flush" % path)


def patch_wx_agw_aui():
    """Fix wxMSW/Phoenix float caption coordinates in AGW AUI dockart.

    wxPython 4.2.5 / wxWidgets 3.2.9 on Windows still computes caption
    coordinates with ``/ 2`` in ``wx.lib.agw.aui.dockart``. Under Phoenix this
    yields floats, while ``wx.DC.DrawText`` and ``DrawRotatedText`` require
    integer pixel coordinates. The resulting paint exception can eventually
    end in a native Windows access violation.

    Linux distribution packages can live in read-only system paths and did not
    produce the reported wxMSW failure, so this source patch is intentionally
    Windows-only.
    """
    if not sys.platform.startswith("win"):
        print("skip wx AGW AUI Windows-only patch on %s" % sys.platform)
        return

    spec = find_spec("wx")
    if spec is None or not spec.origin:
        raise RuntimeError("wxPython package not found: cannot patch AGW AUI")

    target = Path(spec.origin).resolve().parent / "lib" / "agw" / "aui" / "dockart.py"
    if not target.exists():
        raise RuntimeError("wxPython AGW AUI dockart.py not found: %s" % target)

    label = "wx.lib.agw.aui.dockart.py"
    old_rotated = "dc.DrawRotatedText(draw_text, rect.x+(rect.width/2)-(h/2)-diff, rect.y+rect.height-3-caption_offset, 90)"
    new_rotated = "dc.DrawRotatedText(draw_text, int(round(rect.x+(rect.width/2)-(h/2)-diff)), int(round(rect.y+rect.height-3-caption_offset)), 90)"
    old_text = "dc.DrawText(draw_text, rect.x+3+caption_offset, rect.y+(rect.height/2)-(h/2)-diff)"
    new_text = "dc.DrawText(draw_text, int(round(rect.x+3+caption_offset)), int(round(rect.y+(rect.height/2)-(h/2)-diff)))"

    _replace_target(target, label, old_rotated, new_rotated)
    _replace_target(target, label, old_text, new_text)

    # Contract check: fail bootstrap/build immediately if the unsafe forms
    # survived because a future wxPython release changed the source layout.
    patched = target.read_text(encoding="utf-8")
    if old_rotated in patched or old_text in patched:
        raise RuntimeError("%s: unsafe float AUI coordinates still present" % label)
    if new_rotated not in patched or new_text not in patched:
        raise RuntimeError("%s: expected integer-coordinate patch is absent" % label)


def main():
    patch_transport()
    patch_images()
    patch_taskbar()
    patch_network_access()
    patch_redirect()
    patch_wx_agw_aui()


if __name__ == "__main__":
    main()
