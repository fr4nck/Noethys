#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply the Python 3/wxPhoenix fixes proven by Windows runtime tracebacks."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace(path, old, new, minimum=1):
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count >= minimum:
        text = text.replace(old, new)
        target.write_text(text, encoding="utf-8")
        print("patched %s (%d replacement(s))" % (path, count))
        return
    if new in text:
        print("already fixed %s" % path)
        return
    raise RuntimeError("%s: expected source pattern not found: %r" % (path, old))


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


def patch_taskbar():
    path = "noethys/Ctrl/CTRL_TaskBarIcon.py"
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


def main():
    patch_transport()
    patch_images()
    patch_taskbar()
    patch_network_access()
    patch_redirect()


if __name__ == "__main__":
    main()
