#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply exact fixes for runtime regressions observed in the Windows portable.

The replacements are deliberately guarded: if the expected legacy source is no
longer present, the script aborts instead of making a speculative edit.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def replace_exact(path, old, new, expected=1):
    file_path = ROOT / path
    text = file_path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise RuntimeError(
            "%s: expected %d occurrence(s), found %d for %r"
            % (path, expected, count, old)
        )
    file_path.write_text(text.replace(old, new), encoding="utf-8")
    print("patched %s" % path)


def patch_transport_factories():
    path = ROOT / "noethys/Ctrl/CTRL_Saisie_transport.py"
    text = path.read_text(encoding="utf-8")

    marker = "lambda parent=self:"
    count = text.count(marker)
    if count < 1:
        raise RuntimeError("CTRL_Saisie_transport.py: legacy self-capturing factories not found")
    text = text.replace(marker, "lambda parent:")

    old_call = "            ctrl = constructeur()\n"
    if text.count(old_call) != 1:
        raise RuntimeError("CTRL_Saisie_transport.py: constructor call guard failed")
    text = text.replace(old_call, "            ctrl = constructeur(self)\n", 1)

    path.write_text(text, encoding="utf-8")
    print("patched noethys/Ctrl/CTRL_Saisie_transport.py (%d factories)" % count)


def main():
    # Import-time NameError blocking family sheets, consumption manager,
    # badge procedures and Connecthys request handling.
    patch_transport_factories()

    # Python 3 division returns floats; wx geometry/image APIs require ints.
    replace_exact(
        "noethys/Ol/OL_Modes_reglements.py",
        "TAILLE_IMAGE = (132/2.0, 72/2.0)",
        "TAILLE_IMAGE = (132 // 2, 72 // 2)",
    )
    replace_exact(
        "noethys/Dlg/DLG_Emetteurs.py",
        "TAILLE_IMAGE = (132/2.0, 72/2.0)",
        "TAILLE_IMAGE = (132 // 2, 72 // 2)",
    )

    replace_exact(
        "noethys/Utils/UTILS_Organisateur.py",
        """        if largeur > hauteur :
            hauteur = hauteur * tailleMaxi / largeur
            largeur = tailleMaxi
        else:
            largeur = largeur * tailleMaxi / hauteur
            hauteur = tailleMaxi
    img.Rescale(width=largeur, height=hauteur, quality=wx.IMAGE_QUALITY_HIGH)
    position = (((tailleImage[0]/2.0) - (largeur/2.0)), ((tailleImage[1]/2.0) - (hauteur/2.0)))
""",
        """        if largeur > hauteur :
            hauteur = int(round(hauteur * tailleMaxi / float(largeur)))
            largeur = tailleMaxi
        else:
            largeur = int(round(largeur * tailleMaxi / float(hauteur)))
            hauteur = tailleMaxi
    largeur = int(largeur)
    hauteur = int(hauteur)
    img.Rescale(width=largeur, height=hauteur, quality=wx.IMAGE_QUALITY_HIGH)
    position = (
        int(round((tailleImage[0] / 2.0) - (largeur / 2.0))),
        int(round((tailleImage[1] / 2.0) - (hauteur / 2.0))),
    )
""",
    )

    replace_exact(
        "noethys/Ctrl/CTRL_TaskBarIcon.py",
        """        hauteurRond = hauteurTexte + padding * 2
        largeurRond = largeurTexte + padding * 2 + hauteurRond/2.0
        if largeurRond < hauteurRond :
            largeurRond = hauteurRond

        if \"gauche\" in alignement : xRond = 1
        if \"droite\" in alignement : xRond = largeurImage - largeurRond - 1
        if \"haut\" in alignement : yRond = 1
        if \"bas\" in alignement : yRond = hauteurImage - hauteurRond - 1

        if 'phoenix' in wx.PlatformInfo:
            dc.DrawRoundedRectangle(wx.Rect(xRond, yRond, largeurRond, hauteurRond), hauteurRond / 2.0)
        else:
            dc.DrawRoundedRectangleRect(wx.Rect(xRond, yRond, largeurRond, hauteurRond), hauteurRond / 2.0)

        # Texte
        xTexte = xRond + largeurRond / 2.0 - largeurTexte / 2.0
        yTexte = yRond + hauteurRond / 2.0 - hauteurTexte / 2.0 - 1
        dc.DrawText(texte, xTexte, yTexte)
""",
        """        hauteurRond = int(round(hauteurTexte + padding * 2))
        largeurRond = int(round(largeurTexte + padding * 2 + hauteurRond / 2.0))
        if largeurRond < hauteurRond :
            largeurRond = hauteurRond

        if \"gauche\" in alignement : xRond = 1
        if \"droite\" in alignement : xRond = largeurImage - largeurRond - 1
        if \"haut\" in alignement : yRond = 1
        if \"bas\" in alignement : yRond = hauteurImage - hauteurRond - 1

        xRond = int(round(xRond))
        yRond = int(round(yRond))
        rayon = int(round(hauteurRond / 2.0))
        if 'phoenix' in wx.PlatformInfo:
            dc.DrawRoundedRectangle(wx.Rect(xRond, yRond, largeurRond, hauteurRond), rayon)
        else:
            dc.DrawRoundedRectangleRect(wx.Rect(xRond, yRond, largeurRond, hauteurRond), rayon)

        # Texte
        xTexte = int(round(xRond + largeurRond / 2.0 - largeurTexte / 2.0))
        yTexte = int(round(yRond + hauteurRond / 2.0 - hauteurTexte / 2.0 - 1))
        dc.DrawText(texte, xTexte, yTexte)
""",
    )

    # Phoenix no longer accepts six.MAXSIZE as an implicit append index.
    replace_exact(
        "noethys/Dlg/DLG_Utilisateurs_reseau.py",
        "                index = self.InsertItem(six.MAXSIZE, autorisationStr)",
        "                index = self.InsertItem(self.GetItemCount(), autorisationStr)",
    )

    # File-like stdout redirect must implement flush() on Python 3 shutdown.
    replace_exact(
        "noethys/Noethys.py",
        """    def write(self, text):
        if self.filename.closed:
            pass
        else:
            self.filename.write(text)
            self.filename.flush()



""",
        """    def write(self, text):
        if self.filename.closed:
            pass
        else:
            self.filename.write(text)
            self.filename.flush()

    def flush(self):
        if not self.filename.closed:
            self.filename.flush()



""",
    )


if __name__ == "__main__":
    main()
