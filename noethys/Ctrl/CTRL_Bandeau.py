#!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-11 Ivan LUCAS
# Licence:          Licence GNU GPL
#-----------------------------------------------------------

import re

import Chemins
import wx
from Ctrl import CTRL_TexteRepens
from Utils import UTILS_StyleRepens as Style
from Utils.UTILS_Traduction import _


# Ne pas importer la stdlib ``html`` ici. Le bundle PyInstaller historique de
# Noethys est volontairement plat et contient aussi ``wx/html.py`` : sur Windows,
# un import absolu ``html`` peut alors être résolu contre wx.html et casser ses
# imports relatifs. Les bandeaux n'ont besoin que d'un sous-ensemble compact des
# entités HTML réellement rencontrées dans les anciens textes d'introduction.
_ENTITES_HTML = {
    "amp": "&", "lt": "<", "gt": ">", "quot": '"', "apos": "'", "nbsp": "\u00a0",
    "agrave": "à", "aacute": "á", "acirc": "â", "auml": "ä", "aring": "å", "aelig": "æ",
    "ccedil": "ç", "egrave": "è", "eacute": "é", "ecirc": "ê", "euml": "ë",
    "igrave": "ì", "iacute": "í", "icirc": "î", "iuml": "ï",
    "ograve": "ò", "oacute": "ó", "ocirc": "ô", "ouml": "ö", "oelig": "œ",
    "ugrave": "ù", "uacute": "ú", "ucirc": "û", "uuml": "ü", "yuml": "ÿ",
    "Agrave": "À", "Aacute": "Á", "Acirc": "Â", "Auml": "Ä", "Aring": "Å", "AElig": "Æ",
    "Ccedil": "Ç", "Egrave": "È", "Eacute": "É", "Ecirc": "Ê", "Euml": "Ë",
    "Igrave": "Ì", "Iacute": "Í", "Icirc": "Î", "Iuml": "Ï",
    "Ograve": "Ò", "Oacute": "Ó", "Ocirc": "Ô", "Ouml": "Ö", "OElig": "Œ",
    "Ugrave": "Ù", "Uacute": "Ú", "Ucirc": "Û", "Uuml": "Ü", "Yuml": "Ÿ",
    "laquo": "«", "raquo": "»", "lsquo": "‘", "rsquo": "’", "ldquo": "“", "rdquo": "”",
    "ndash": "–", "mdash": "—", "hellip": "…", "bull": "•", "middot": "·",
    "copy": "©", "reg": "®", "trade": "™", "euro": "€", "deg": "°",
}
_RE_ENTITE_HTML = re.compile(r"&(#(?:x[0-9A-Fa-f]+|[0-9]+)|[A-Za-z][A-Za-z0-9]+);")


def _decoder_entites_html(texte):
    """Décode les entités utiles sans dépendre d'un module nommé ``html``."""
    def remplacer(match):
        code = match.group(1)
        if code.startswith("#x"):
            try:
                return chr(int(code[2:], 16))
            except (TypeError, ValueError, OverflowError):
                return match.group(0)
        if code.startswith("#"):
            try:
                return chr(int(code[1:], 10))
            except (TypeError, ValueError, OverflowError):
                return match.group(0)
        return _ENTITES_HTML.get(code, match.group(0))

    return _RE_ENTITE_HTML.sub(remplacer, texte)


def _texte_simple(texte):
    """Convertit les quelques balises historiques en texte natif lisible."""
    if texte in (None, ""):
        return u""
    texte = str(texte)
    texte = re.sub(r"(?i)<\s*br\s*/?\s*>", "\n", texte)
    texte = re.sub(r"(?i)</\s*p\s*>", "\n", texte)
    texte = re.sub(r"<[^>]+>", "", texte)
    return _decoder_entites_html(texte).strip()


def _bitmap_adapte(chemin, taille):
    """Charge une illustration historique sans imposer son ancienne géométrie."""
    try:
        bitmap = wx.Bitmap(Chemins.GetStaticIconPath(chemin, taille=taille), wx.BITMAP_TYPE_ANY)
        if bitmap.IsOk() and (bitmap.GetWidth() != taille or bitmap.GetHeight() != taille):
            image = bitmap.ConvertToImage().Scale(taille, taille, wx.IMAGE_QUALITY_HIGH)
            bitmap = wx.Bitmap(image)
        return bitmap
    except Exception:
        return wx.NullBitmap


class TexteIntro(CTRL_TexteRepens.CTRL):
    """Texte d'introduction sémantique, reflow automatique."""

    def __init__(self, parent, texte=u""):
        self.texte_original = _texte_simple(texte)
        CTRL_TexteRepens.CTRL.__init__(
            self,
            parent,
            label=self.texte_original,
            role="lead",
            role_texte="on_surface_variant",
            role_fond="surface_container",
            wrap=True,
        )
        self.SetMinSize((-1, Style.hauteur_ligne("compact")))

    def AppliquerTheme(self):
        self.AppliquerStyle()

    def SetTexte(self, texte):
        self.texte_original = _texte_simple(texte)
        self.SetLabel(self.texte_original)


class Bandeau(wx.Panel):
    """En-tête commun : illustration, H1 et introduction Lead reflow."""

    def __init__(self, parent, titre="", texte="", hauteurHtml=25, nomImage=None):
        wx.Panel.__init__(self, parent, id=-1, style=wx.TAB_TRAVERSAL | wx.BORDER_NONE)
        self.nomImage = nomImage
        self.image = None
        # Compatibilité API historique uniquement : aucune hauteur n'est figée.
        self.hauteurHtml = hauteurHtml

        if self.nomImage is not None:
            taille = Style.taille_icone("hero")
            self.image = wx.StaticBitmap(self, -1, _bitmap_adapte(self.nomImage, taille))

        self.ctrl_titre = CTRL_TexteRepens.H1(
            self,
            label=titre,
            role_texte="on_surface",
            role_fond="surface_container",
            wrap=True,
        )
        self.ctrl_intro = TexteIntro(self, texte)
        self.ligne = wx.StaticLine(self, -1)

        self.AppliquerTheme()
        self.__do_layout()
        self.Bind(wx.EVT_SIZE, self.OnSize)

    def AppliquerTheme(self):
        Style.appliquer_fenetre(self, "surface_container")
        self.ctrl_titre.AppliquerStyle()
        self.ctrl_intro.AppliquerTheme()
        bordure = Style.couleur("outline_variant")
        try:
            self.ligne.SetForegroundColour(bordure)
            self.ligne.SetBackgroundColour(bordure)
        except Exception:
            pass
        if self.image is not None:
            try:
                self.image.SetBackgroundColour(Style.couleur("surface_container"))
            except Exception:
                pass

    def __do_layout(self):
        marge_x = Style.espace(3)

        contenu = wx.BoxSizer(wx.HORIZONTAL)
        if self.image is not None:
            contenu.Add(self.image, 0, wx.ALIGN_TOP | wx.RIGHT, marge_x)

        textes = wx.BoxSizer(wx.VERTICAL)
        textes.Add(self.ctrl_titre, 0, wx.EXPAND | wx.BOTTOM, max(2, Style.espace(1)))
        textes.Add(self.ctrl_intro, 0, wx.EXPAND)
        contenu.Add(textes, 1, wx.EXPAND)

        principal = wx.BoxSizer(wx.VERTICAL)
        principal.Add(contenu, 0, wx.EXPAND | wx.ALL, marge_x)
        principal.Add(self.ligne, 0, wx.EXPAND)
        self.SetSizer(principal)
        self.Layout()

    def OnSize(self, event):
        event.Skip()
        wx.CallAfter(self.ctrl_titre.Reflow)
        wx.CallAfter(self.ctrl_intro.Reflow)


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self, -1)
        Style.appliquer_fenetre(panel, "surface")
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(panel, 1, wx.EXPAND)
        self.SetSizer(sizer_1)
        self.ctrl = Bandeau(panel, _(u"COUCOU"), _(u"coincoin"), nomImage="Images/32x32/Femme.png")
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.ctrl, 1, wx.EXPAND)
        panel.SetSizer(sizer_2)
        self.Layout()
        self.CentreOnScreen()


if __name__ == '__main__':
    app = wx.App(0)
    frame_1 = MyFrame(None, -1, "TEST", size=(800, 200))
    app.SetTopWindow(frame_1)
    frame_1.Show()
    app.MainLoop()
