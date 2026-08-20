#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Pictogrammes modernes des personnes et organisations de Noethys.

Cette couche est volontairement ciblée : elle remplace les anciennes petites
illustrations de civilité/structure par une famille visuelle homogène. Les
ressources métier non reconnues continuent d'utiliser leurs PNG historiques.
"""

import os
import re
import tempfile
import unicodedata


_CACHE_VERSION = "v1"
_FG = (53, 67, 63, 255)
_ACCENT = (50, 121, 86, 255)
_SOFT = (214, 229, 220, 255)


def _normaliser(texte):
    texte = unicodedata.normalize("NFKD", texte or "")
    texte = "".join(c for c in texte if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", texte.lower()).strip("_")


def _identite_pour_chemin(chemin):
    """Retourne (type, action) pour une ressource d'identité connue."""
    nom = _normaliser(os.path.splitext(os.path.basename(chemin or ""))[0])
    if not nom:
        return None

    action = None
    for suffixe, code in (
        ("_ajouter", "add"), ("_add", "add"),
        ("_modifier", "edit"), ("_edit", "edit"),
        ("_supprimer", "delete"), ("_delete", "delete"),
    ):
        if nom.endswith(suffixe):
            nom = nom[:-len(suffixe)]
            action = code
            break

    # Les civilités partagent désormais une silhouette neutre : on conserve
    # le sens « individu » sans réintroduire des stéréotypes homme/femme.
    if nom in ("homme", "femme", "personne", "individu", "identite"):
        return ("person", action)
    if nom in ("garcon", "fille", "enfant"):
        return ("child", action)
    if nom in ("personnes", "individus", "famille", "familles", "groupe", "groupes"):
        return ("family", action)
    if nom in ("association", "associations"):
        return ("association", action)
    if nom in ("ecole", "ecoles", "scolaire", "etablissement_scolaire"):
        return ("school", action)
    if nom in ("mairie", "mairies", "commune", "communes", "collectivite", "collectivites"):
        return ("civic", action)
    if nom in ("organisme", "organismes", "institution", "institutions", "organisateur"):
        return ("institution", action)
    if nom in ("entreprise", "entreprises", "societe", "societes"):
        return ("company", action)
    return None


def _taille_pour_chemin(chemin):
    normalise = (chemin or "").replace("\\", "/")
    match = re.search(r"/(16|20|24|32|40|48)x\1/", "/" + normalise)
    return int(match.group(1)) if match else 16


def _dessiner(type_identite, action, taille, destination):
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return False

    base = 96
    image = Image.new("RGBA", (base, base), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    u = base / 24.0
    w = max(5, int(round(1.6 * u)))

    def p(v):
        return int(round(v * u))

    def box(x1, y1, x2, y2):
        return (p(x1), p(y1), p(x2), p(y2))

    def line(points, fill=_FG, width=w):
        d.line([(p(x), p(y)) for x, y in points], fill=fill, width=width, joint="curve")

    def rr(coords, radius=1.8, outline=_FG, fill=None, width=w):
        d.rounded_rectangle(box(*coords), radius=p(radius), outline=outline, fill=fill, width=width)

    def personne(cx=12, cy=8, rayon=3.1, largeur=13, bas=20, accent=False):
        couleur = _ACCENT if accent else _FG
        d.ellipse(box(cx-rayon, cy-rayon, cx+rayon, cy+rayon), fill=couleur)
        # Épaules pleines : beaucoup plus lisibles à 16 px que l'ancien arc fin.
        gauche = cx - largeur / 2.0
        droite = cx + largeur / 2.0
        d.rounded_rectangle(box(gauche, 13, droite, bas), radius=p(3.2), fill=couleur)

    if type_identite == "person":
        personne(accent=True)

    elif type_identite == "child":
        personne(cx=12, cy=8.7, rayon=2.7, largeur=10.5, bas=19.5, accent=True)
        line(((7, 21), (17, 21)), fill=_FG, width=max(3, w // 2))

    elif type_identite == "family":
        d.ellipse(box(4.5, 6, 9.5, 11), fill=_FG)
        d.ellipse(box(14.5, 6, 19.5, 11), fill=_FG)
        d.ellipse(box(9.3, 4, 14.7, 9.4), fill=_ACCENT)
        d.rounded_rectangle(box(2.8, 13, 10.8, 19.5), radius=p(2.4), fill=_FG)
        d.rounded_rectangle(box(13.2, 13, 21.2, 19.5), radius=p(2.4), fill=_FG)
        d.rounded_rectangle(box(7.4, 10.8, 16.6, 20.5), radius=p(2.8), fill=_ACCENT)

    elif type_identite == "association":
        # Trois membres autour d'un centre commun : collectif, pas « entreprise ».
        d.ellipse(box(4, 5, 9, 10), fill=_FG)
        d.ellipse(box(15, 5, 20, 10), fill=_FG)
        d.ellipse(box(9.5, 3.5, 14.5, 8.5), fill=_ACCENT)
        line(((6.5, 12), (12, 18), (17.5, 12)), fill=_FG)
        d.ellipse(box(9.2, 15.2, 14.8, 20.8), fill=_SOFT, outline=_ACCENT, width=w)

    elif type_identite == "school":
        # Façade scolaire simple + fanion, lisible en petite taille.
        rr((4, 9, 20, 20), 1.2)
        line(((4, 9), (12, 4), (20, 9)), fill=_ACCENT)
        rr((10, 14, 14, 20), .6, outline=_ACCENT)
        line(((7, 12), (7, 16)), width=max(3, w // 2))
        line(((17, 12), (17, 16)), width=max(3, w // 2))
        line(((12, 4), (12, 1.8)), fill=_FG, width=max(3, w // 2))
        d.polygon([(p(12), p(2)), (p(17), p(3.4)), (p(12), p(5))], fill=_ACCENT)

    elif type_identite == "civic":
        # Hôtel de ville / collectivité : fronton et colonnes.
        d.polygon([(p(3), p(9)), (p(12), p(4)), (p(21), p(9))], fill=_SOFT, outline=_FG)
        line(((4, 10), (20, 10)), fill=_ACCENT)
        for x in (6.5, 10.3, 14.1, 17.9):
            line(((x, 11), (x, 18)), width=max(3, w // 2))
        line(((3, 20), (21, 20)), fill=_FG)
        line(((12, 4), (12, 1.8)), fill=_FG, width=max(3, w // 2))
        d.polygon([(p(12), p(2)), (p(17), p(3.2)), (p(12), p(4.5))], fill=_ACCENT)

    elif type_identite == "institution":
        d.polygon([(p(3), p(9)), (p(12), p(4)), (p(21), p(9))], fill=_SOFT, outline=_FG)
        line(((4, 10), (20, 10)), fill=_ACCENT)
        for x in (7, 12, 17):
            line(((x, 11), (x, 18)), width=max(3, w // 2))
        line(((3, 20), (21, 20)), fill=_FG)

    elif type_identite == "company":
        rr((5, 5, 19, 21), 1.0)
        for y in (9, 13, 17):
            for x in (9, 15):
                d.rounded_rectangle(box(x-1, y-1, x+1, y+1), radius=p(.3), fill=_ACCENT)
        rr((10, 17, 14, 21), .4, outline=_FG, fill=_SOFT, width=max(3, w // 2))

    else:
        return False

    # Petit badge d'action cohérent pour Famille_ajouter/modifier/supprimer.
    if action:
        d.ellipse(box(14, 14, 23, 23), fill=(248, 250, 249, 255), outline=_ACCENT, width=max(3, w // 2))
        if action == "add":
            line(((18.5, 16.3), (18.5, 20.7)), fill=_ACCENT, width=max(3, w // 2))
            line(((16.3, 18.5), (20.7, 18.5)), fill=_ACCENT, width=max(3, w // 2))
        elif action == "edit":
            line(((16.2, 20.4), (20.5, 16.1)), fill=_ACCENT, width=max(3, w // 2))
            line(((16, 20.8), (17.7, 20.4)), fill=_FG, width=max(2, w // 3))
        elif action == "delete":
            line(((16.4, 18.5), (20.6, 18.5)), fill=_ACCENT, width=max(3, w // 2))

    try:
        resampling = Image.Resampling.LANCZOS
    except AttributeError:
        resampling = Image.LANCZOS
    image = image.resize((int(taille), int(taille)), resampling)
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    image.save(destination, format="PNG", optimize=True)
    return True


def GetLegacyOverridePath(chemin, taille=None):
    identite = _identite_pour_chemin(chemin)
    if identite is None:
        return None
    type_identite, action = identite
    taille = int(taille or _taille_pour_chemin(chemin))
    if taille not in (16, 20, 24, 32, 40, 48):
        return None

    dossier = os.path.join(tempfile.gettempdir(), "noethys-modern-identities-%s" % _CACHE_VERSION)
    suffixe = "-%s" % action if action else ""
    destination = os.path.join(dossier, "%s%s-%d.png" % (type_identite, suffixe, taille))
    if os.path.isfile(destination):
        return destination
    try:
        if _dessiner(type_identite, action, taille, destination):
            return destination
    except Exception:
        pass
    return None
