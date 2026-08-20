# -*- coding: utf-8 -*-
"""Extensions sémantiques du catalogue Fluent pour Repens Design.

Les pictogrammes supplémentaires suivent la même géométrie 24 px et la même
recoloration sémantique que ``UTILS_FluentIcons``. Les noms déjà couverts sont
délégués au catalogue central existant.
"""

_CACHE = {}

SVG = {
    "mail": '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M5.25 4H18.75C20.5449 4 22 5.45507 22 7.25V16.75C22 18.5449 20.5449 20 18.75 20H5.25C3.45507 20 2 18.5449 2 16.75V7.25C2 5.45507 3.45507 4 5.25 4ZM20.5 8.089L12.469 13.721C12.1875 13.9184 11.8125 13.9184 11.531 13.721L3.5 8.089V16.75C3.5 17.7165 4.2835 18.5 5.25 18.5H18.75C19.7165 18.5 20.5 17.7165 20.5 16.75V8.089ZM18.75 5.5H5.25C4.499 5.5 3.858 5.972 3.61 6.635L12 12.517L20.39 6.635C20.142 5.972 19.501 5.5 18.75 5.5Z" fill="#212121"/></svg>''',
    "chat": '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M6.25 3H17.75C19.5449 3 21 4.45507 21 6.25V14.75C21 16.5449 19.5449 18 17.75 18H11.31L6.23 21.41C5.731 21.745 5.06 21.387 5.06 20.786V17.789C3.855 17.311 3 16.135 3 14.75V6.25C3 4.45507 4.45507 3 6.25 3ZM17.75 4.5H6.25C5.2835 4.5 4.5 5.2835 4.5 6.25V14.75C4.5 15.7165 5.2835 16.5 6.25 16.5H6.56V19.379L10.666 16.622C10.79 16.542 10.934 16.5 11.081 16.5H17.75C18.7165 16.5 19.5 15.7165 19.5 14.75V6.25C19.5 5.2835 18.7165 4.5 17.75 4.5ZM7.75 9.25C8.164 9.25 8.5 9.586 8.5 10C8.5 10.414 8.164 10.75 7.75 10.75C7.336 10.75 7 10.414 7 10C7 9.586 7.336 9.25 7.75 9.25ZM12 9.25C12.414 9.25 12.75 9.586 12.75 10C12.75 10.414 12.414 10.75 12 10.75C11.586 10.75 11.25 10.414 11.25 10C11.25 9.586 11.586 9.25 12 9.25ZM16.25 9.25C16.664 9.25 17 9.586 17 10C17 10.414 16.664 10.75 16.25 10.75C15.836 10.75 15.5 10.414 15.5 10C15.5 9.586 15.836 9.25 16.25 9.25Z" fill="#212121"/></svg>''',
    "more": '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M5 10.5C5.82843 10.5 6.5 11.1716 6.5 12C6.5 12.8284 5.82843 13.5 5 13.5C4.17157 13.5 3.5 12.8284 3.5 12C3.5 11.1716 4.17157 10.5 5 10.5ZM12 10.5C12.8284 10.5 13.5 11.1716 13.5 12C13.5 12.8284 12.8284 13.5 12 13.5C11.1716 13.5 10.5 12.8284 10.5 12C10.5 11.1716 11.1716 10.5 12 10.5ZM19 10.5C19.8284 10.5 20.5 11.1716 20.5 12C20.5 12.8284 19.8284 13.5 19 13.5C18.1716 13.5 17.5 12.8284 17.5 12C17.5 11.1716 18.1716 10.5 19 10.5Z" fill="#212121"/></svg>''',
}


def _couleur_hex(role):
    try:
        from Utils import UTILS_Interface
        couleur = UTILS_Interface.GetCouleurRole(role)
        return "#%02X%02X%02X" % (couleur.Red(), couleur.Green(), couleur.Blue())
    except Exception:
        return "#212121"


def GetBitmap(nom, taille=24, role="on_surface"):
    if nom not in SVG:
        from Utils import UTILS_FluentIcons
        return UTILS_FluentIcons.GetBitmap(nom, taille=taille, role=role)

    try:
        taille = max(12, min(64, int(taille)))
    except Exception:
        taille = 24
    couleur = _couleur_hex(role)
    cle = (nom, taille, couleur)
    if cle in _CACHE:
        return _CACHE[cle]

    try:
        import wx.svg
        data = SVG[nom].replace("#212121", couleur).encode("utf-8")
        image = wx.svg.SVGimage.CreateFromBytes(data)
        try:
            bitmap = image.ConvertToBitmap(width=taille, height=taille)
        except TypeError:
            bitmap = image.ConvertToBitmap(scale=float(taille) / 24.0)
        if bitmap is not None and bitmap.IsOk():
            _CACHE[cle] = bitmap
            return bitmap
    except Exception:
        pass

    try:
        import wx
        return wx.NullBitmap
    except Exception:
        return None


def ViderCache():
    _CACHE.clear()
