#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Adaptateur d'icônes PMSL Style B pour les interfaces wxPython.

Le code métier peut demander un rôle sémantique (``action.add``) tandis que
les écrans historiques continuent à demander leurs PNG habituels. Si l'asset
SVG PMSL correspondant est présent, il est rendu en PNG dans un cache local.
Sinon, l'appelant conserve sa ressource historique : cette couche ne doit
jamais empêcher le démarrage de l'application.
"""

import os
import re
import tempfile
import unicodedata

_CACHE_VERSION = "style-b-v2"
_SUPPORTED_SIZES = (16, 20, 24, 32)
_DEFAULT_WX_COLOR = "#3D4E48"


def _normaliser(texte):
    try:
        texte = unicodedata.normalize("NFKD", texte or "")
        texte = "".join(car for car in texte if not unicodedata.combining(car))
    except Exception:
        pass
    return re.sub(r"[^a-z0-9]+", "_", (texte or "").lower()).strip("_")


def _disabled():
    for name in ("PMSL_LEGACY_ICONS", "NOETHYS_LEGACY_ICONS"):
        if os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "oui"):
            return True
    return False


def _taille_depuis_chemin(chemin, taille=None):
    if taille is not None:
        try:
            value = int(taille)
        except (TypeError, ValueError):
            value = 20
    else:
        normalise = (chemin or "").replace("\\", "/")
        match = re.search(r"Images/(16|20|24|32|40|48)x\1/", normalise)
        value = int(match.group(1)) if match else 20
    return min(_SUPPORTED_SIZES, key=lambda candidate: abs(candidate - value))


# Le lot pilote ne remplace que les pictogrammes dont le sens est univoque.
# Les composites restent volontairement sur l'ancienne ressource en attendant
# leur rôle dédié (ex. calendrier+ajout, aperçu+email).
_EXACT = {
    "ajouter": "action.add",
    "modifier": "action.edit",
    "supprimer": "action.delete",
    "sauvegarder": "action.save",
    "enregistrer": "action.save",
    "valider": "action.validate",
    "annuler": "action.cancel",
    "recherche": "action.search",
    "rechercher": "action.search",
    "actualiser": "action.refresh",
    "actualiser2": "action.refresh",
    "apercu": "action.preview",
    "imprimante": "action.print",
    "imprimer": "action.print",
    "aide": "action.help",
    "aide_2": "action.help",
    "suivant": "action.next",
    "suivante": "action.next",
    "calendrier": "planning.calendar",
    "cadenas": "security.locked",
    "cadenas_ferme": "security.locked",
    "personne": "entity.person",
    "homme": "entity.person",
    "femme": "entity.person",
    "individus": "entity.people",
    "famille": "entity.people",
    "familles": "entity.people",
    "document": "entity.document",
    "attention": "state.warning",
    "information": "state.info",
    "info": "state.info",
    "attente": "state.waiting",
    "attente2": "state.waiting",
    "erreur": "state.error",
    "valide": "state.valid",
}


def RoleDepuisLegacy(chemin):
    nom = _normaliser(os.path.splitext(os.path.basename(chemin or ""))[0])
    if not nom:
        return None
    return _EXACT.get(nom)


def _app_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _svg_path(role, taille):
    filename = "pmsl_%s_%s_filled.svg" % (role.replace(".", "_"), taille)
    return os.path.join(_app_root(), "Static", "Images", "PMSL", "svg", str(taille), filename)


def _cache_path(role, taille):
    root = os.path.join(tempfile.gettempdir(), "pmsl-icons", _CACHE_VERSION, str(taille))
    if not os.path.isdir(root):
        try:
            os.makedirs(root)
        except OSError:
            if not os.path.isdir(root):
                return None
    filename = "pmsl_%s_%s_filled.png" % (role.replace(".", "_"), taille)
    return os.path.join(root, filename)


def _render_svg(svg_path, png_path, taille):
    try:
        import wx
        import wx.svg
        with open(svg_path, "rb") as stream:
            data = stream.read()
        try:
            texte = data.decode("utf-8").replace("currentColor", _DEFAULT_WX_COLOR)
            data = texte.encode("utf-8")
        except Exception:
            pass

        create_from_bytes = getattr(wx.svg.SVGimage, "CreateFromBytes", None)
        if create_from_bytes is not None:
            svg = create_from_bytes(data)
        else:
            svg = wx.svg.SVGimage.CreateFromFile(svg_path)
        bitmap = svg.ConvertToBitmap(width=taille, height=taille)
        image = bitmap.ConvertToImage()
        return bool(image.SaveFile(png_path, wx.BITMAP_TYPE_PNG))
    except Exception:
        return False


def GetRolePath(role, taille=20):
    """Retourne un PNG rendu pour un rôle PMSL, ou ``None`` si indisponible."""
    if _disabled() or not role:
        return None
    taille = _taille_depuis_chemin("", taille=taille)
    source = _svg_path(role, taille)
    if not os.path.isfile(source):
        return None

    cache = _cache_path(role, taille)
    if not cache:
        return None
    try:
        if os.path.isfile(cache) and os.path.getmtime(cache) >= os.path.getmtime(source):
            return cache
    except OSError:
        pass

    if _render_svg(source, cache, taille):
        return cache
    return None


def GetLegacyOverridePath(chemin, taille=None):
    """Résout une ancienne ressource vers le lot Style B lorsqu'il est sûr."""
    role = RoleDepuisLegacy(chemin)
    if role is None:
        return None
    return GetRolePath(role, _taille_depuis_chemin(chemin, taille=taille))
