#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Icônes modernes pour les ressources d'interface historiques de Noethys.

Le module reste volontairement indépendant de wx : les PNG sont générés à la
volée avec Pillow dans un cache temporaire. Si Pillow n'est pas disponible, ou
si une icône n'est pas reconnue, l'appelant conserve simplement la ressource
historique.
"""

import os
import re
import tempfile
import unicodedata


_CACHE_VERSION = "v2"
_COULEUR = (61, 78, 72, 255)
_ACCENT = (55, 126, 91, 255)


def _normaliser(texte):
    texte = unicodedata.normalize("NFKD", texte or "")
    texte = "".join(car for car in texte if not unicodedata.combining(car))
    return re.sub(r"[^a-z0-9]+", "_", texte.lower()).strip("_")


# Les noms composés très courants sont associés explicitement avant l'analyse
# par tokens. Cela évite de transformer par hasard un pictogramme métier dont
# le nom contiendrait simplement une courte sous-chaîne connue.
_MAPPINGS_EXACTS = {
    "calendrier_jour": "calendar_day",
    "calendrier_semaine": "calendar_week",
    "calendrier_mois": "calendar_month",
    "calendrier_horizontal": "layout_horizontal",
    "calendrier_vertical": "layout_vertical",
    "calendrier_zoom": "calendar_search",
    "date_actuelle": "today",
    "date_precedente": "previous",
    "date_suivante": "next",
    "jour": "today",
    "precedent": "previous",
    "precedente": "previous",
    "suivant": "next",
    "suivante": "next",
    "zoom_moins": "zoom_out",
    "zoom_plus": "zoom_in",
    "apercu": "preview",
    "mecanisme": "settings",
    "cocher": "check",
    "decocher": "close",
    "interdit": "warning",
}

_MAPPINGS_TOKENS = (
    (("calendrier", "calendar", "agenda", "date"), "calendar"),
    (("imprimante", "imprimer", "printer", "print"), "printer"),
    (("badgeage", "badge"), "badge"),
    (("reglement", "paiement", "payment", "facture", "euro"), "payment"),
    (("calculatrice", "calculator", "calcul"), "calculator"),
    (("utilisateur", "homme", "femme", "personne", "user"), "user"),
    (("individus", "individu", "familles", "famille", "groupe", "groupes"), "users"),
    (("ajouter", "nouveau", "nouvelle", "add", "plus"), "add"),
    (("modifier", "editer", "edition", "crayon", "edit"), "edit"),
    (("supprimer", "effacer", "corbeille", "delete", "trash"), "delete"),
    (("recherche", "rechercher", "loupe", "search"), "search"),
    (("actualiser", "rafraichir", "refresh", "reload"), "refresh"),
    (("configuration", "parametres", "parametre", "options", "outils", "settings"), "settings"),
    (("email", "emails", "mail", "courriel"), "mail"),
    (("valider", "validation", "ok", "check"), "check"),
    (("annuler", "fermer", "close", "cancel"), "close"),
    (("sauvegarder", "sauvegarde", "enregistrer", "save"), "save"),
    (("dossier", "folder", "repertoire"), "folder"),
    (("accueil", "home", "maison"), "home"),
    (("statistiques", "statistique", "graphique", "graph", "chart"), "chart"),
    (("aide", "help"), "help"),
    (("internet", "portail", "web", "globe"), "globe"),
    (("cadenas", "verrou", "lock"), "lock"),
    (("attention", "alerte", "warning"), "warning"),
    (("information", "info"), "info"),
    (("document", "fichier", "file"), "document"),
    (("telephone", "phone", "tel"), "phone"),
)


def _icone_pour_chemin(chemin):
    nom = _normaliser(os.path.splitext(os.path.basename(chemin or ""))[0])
    if not nom:
        return None

    icone = _MAPPINGS_EXACTS.get(nom)
    if icone is not None:
        return icone

    morceaux = set(nom.split("_"))
    for mots, icone in _MAPPINGS_TOKENS:
        for mot in mots:
            if _normaliser(mot) in morceaux:
                return icone
    return None


def _taille_pour_chemin(chemin):
    normalise = (chemin or "").replace("\\", "/")
    match = re.search(r"/(16|20|24|32|48)x\1/", "/" + normalise)
    if match:
        return int(match.group(1))
    return 16


def _dessiner(icone, taille, destination):
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return False

    base = 96
    image = Image.new("RGBA", (base, base), (0, 0, 0, 0))
    d = ImageDraw.Draw(image)
    u = base / 24.0
    w = max(5, int(round(1.65 * u)))
    fg = _COULEUR
    accent = _ACCENT

    def p(x):
        return int(round(x * u))

    def box(x1, y1, x2, y2):
        return (p(x1), p(y1), p(x2), p(y2))

    def line(points, fill=fg, width=w):
        d.line([(p(x), p(y)) for x, y in points], fill=fill, width=width)

    def rr(coords, radius=2.0, outline=fg, fill=None, width=w):
        d.rounded_rectangle(box(*coords), radius=p(radius), outline=outline, fill=fill, width=width)

    def calendar_frame():
        rr((4, 5, 20, 20), 2.2)
        line(((4, 9), (20, 9)))
        line(((8, 3.5), (8, 7)), accent)
        line(((16, 3.5), (16, 7)), accent)

    if icone == "calendar":
        calendar_frame()
        for x, y in ((8, 13), (12, 13), (16, 13), (8, 17), (12, 17)):
            d.ellipse(box(x - .7, y - .7, x + .7, y + .7), fill=accent)
    elif icone == "calendar_day":
        calendar_frame()
        rr((8, 12, 16, 17), 1.0, outline=accent)
    elif icone == "calendar_week":
        calendar_frame()
        for x in (8, 12, 16):
            line(((x, 12), (x, 17)), accent)
    elif icone == "calendar_month":
        calendar_frame()
        for x in (8, 12, 16):
            for y in (12.5, 16.5):
                d.ellipse(box(x - .55, y - .55, x + .55, y + .55), fill=accent)
    elif icone == "layout_horizontal":
        rr((4, 5, 20, 19), 1.8)
        line(((5, 12), (19, 12)), accent)
    elif icone == "layout_vertical":
        rr((4, 5, 20, 19), 1.8)
        line(((12, 6), (12, 18)), accent)
    elif icone == "previous":
        line(((15, 5), (8, 12), (15, 19)), accent, max(w, p(2.0)))
    elif icone == "next":
        line(((9, 5), (16, 12), (9, 19)), accent, max(w, p(2.0)))
    elif icone == "zoom_out":
        d.ellipse(box(4, 4, 15, 15), outline=fg, width=w)
        line(((7, 9.5), (12, 9.5)), accent)
        line(((14, 14), (20, 20)), fg)
    elif icone == "zoom_in":
        d.ellipse(box(4, 4, 15, 15), outline=fg, width=w)
        line(((7, 9.5), (12, 9.5)), accent)
        line(((9.5, 7), (9.5, 12)), accent)
        line(((14, 14), (20, 20)), fg)
    elif icone == "today":
        calendar_frame()
        d.ellipse(box(10, 12, 14, 16), fill=accent)
    elif icone == "calendar_search":
        calendar_frame()
        d.ellipse(box(11.5, 12, 17.5, 18), outline=accent, width=max(4, w - 1))
        line(((17, 17.5), (20, 20.5)), accent, max(4, w - 1))
    elif icone == "preview":
        d.ellipse(box(3, 7, 21, 17), outline=fg, width=w)
        d.ellipse(box(9, 9, 15, 15), outline=accent, width=w)
        d.ellipse(box(11.2, 11.2, 12.8, 12.8), fill=accent)
    elif icone == "printer":
        rr((6, 3, 18, 10), 1.2)
        rr((3, 8, 21, 17), 2.0)
        rr((6, 14, 18, 21), 1.0, fill=(255, 255, 255, 0))
        d.ellipse(box(17, 11, 18.5, 12.5), fill=accent)
    elif icone == "badge":
        rr((4, 4, 20, 20), 2.2)
        d.ellipse(box(9, 7, 15, 13), outline=accent, width=w)
        d.arc(box(7, 11, 17, 19), 200, 340, fill=accent, width=w)
        line(((7, 4), (7, 2.5)), accent)
        line(((17, 4), (17, 2.5)), accent)
    elif icone == "payment":
        rr((3, 5, 21, 19), 2.2)
        line(((3, 9), (21, 9)))
        line(((7, 15), (10, 17), (15, 12)), accent)
    elif icone == "calculator":
        rr((5, 3, 19, 21), 2.2)
        rr((7, 5, 17, 9), 1.0, outline=accent)
        for x in (8, 12, 16):
            for y in (13, 17):
                d.ellipse(box(x - .65, y - .65, x + .65, y + .65), fill=fg)
    elif icone == "user":
        d.ellipse(box(8, 4, 16, 12), outline=accent, width=w)
        d.arc(box(5, 10, 19, 23), 195, 345, fill=fg, width=w)
    elif icone == "users":
        d.ellipse(box(5, 6, 11, 12), outline=fg, width=w)
        d.ellipse(box(13, 5, 19, 11), outline=accent, width=w)
        d.arc(box(2, 10, 14, 22), 200, 335, fill=fg, width=w)
        d.arc(box(10, 9, 22, 21), 205, 340, fill=accent, width=w)
    elif icone == "add":
        line(((12, 5), (12, 19)), accent)
        line(((5, 12), (19, 12)), accent)
    elif icone == "edit":
        line(((5, 19), (7, 14), (16, 5), (19, 8), (10, 17), (5, 19)), fg)
        line(((15, 6), (18, 9)), accent)
    elif icone == "delete":
        rr((6, 7, 18, 20), 1.7)
        line(((4, 6), (20, 6)), accent)
        line(((9, 3.5), (15, 3.5)), accent)
        line(((10, 10), (10, 17)))
        line(((14, 10), (14, 17)))
    elif icone == "search":
        d.ellipse(box(4, 4, 15, 15), outline=fg, width=w)
        line(((14, 14), (20, 20)), accent)
    elif icone == "refresh":
        d.arc(box(4, 4, 20, 20), 35, 300, fill=fg, width=w)
        d.polygon([(p(18), p(5)), (p(21), p(5)), (p(20), p(9))], fill=accent)
    elif icone == "settings":
        for y, x in ((7, 9), (12, 15), (17, 11)):
            line(((4, y), (20, y)))
            d.ellipse(box(x - 1.4, y - 1.4, x + 1.4, y + 1.4), fill=accent)
    elif icone == "mail":
        rr((3, 5, 21, 19), 2.0)
        line(((4, 7), (12, 13), (20, 7)), accent)
    elif icone == "check":
        line(((5, 12), (10, 17), (19, 7)), accent, max(w, p(2.0)))
    elif icone == "close":
        line(((6, 6), (18, 18)), fg, max(w, p(1.8)))
        line(((18, 6), (6, 18)), fg, max(w, p(1.8)))
    elif icone == "save":
        line(((12, 4), (12, 15)), accent)
        line(((8, 11), (12, 15), (16, 11)), accent)
        line(((5, 18), (5, 20), (19, 20), (19, 18)), fg)
    elif icone == "folder":
        points = ((3, 7), (9, 7), (11, 9), (21, 9), (20, 19), (4, 19), (3, 7))
        line(points, fg)
        line(((4, 10), (20, 10)), accent)
    elif icone == "home":
        line(((4, 11), (12, 4), (20, 11)), accent)
        rr((6, 10, 18, 20), 1.0)
        line(((11, 20), (11, 14), (15, 14), (15, 20)))
    elif icone == "chart":
        line(((4, 4), (4, 20), (20, 20)))
        for x, y, h in ((7, 14, 5), (11, 10, 9), (15, 7, 12)):
            rr((x, y, x + 2.5, y + h), .6, outline=accent, fill=accent, width=1)
    elif icone == "help":
        d.ellipse(box(4, 4, 20, 20), outline=fg, width=w)
        d.arc(box(8, 7, 16, 14), 195, 530, fill=accent, width=w)
        line(((12, 13), (12, 15)), accent)
        d.ellipse(box(11.2, 17, 12.8, 18.6), fill=accent)
    elif icone == "globe":
        d.ellipse(box(4, 4, 20, 20), outline=fg, width=w)
        d.ellipse(box(8, 4, 16, 20), outline=accent, width=w)
        line(((4.5, 12), (19.5, 12)))
    elif icone == "lock":
        rr((6, 10, 18, 20), 1.7)
        d.arc(box(8, 4, 16, 14), 180, 360, fill=accent, width=w)
    elif icone == "warning":
        points = ((12, 3), (21, 20), (3, 20), (12, 3))
        line(points, fg)
        line(((12, 8), (12, 14)), accent)
        d.ellipse(box(11.2, 16.2, 12.8, 17.8), fill=accent)
    elif icone == "info":
        d.ellipse(box(4, 4, 20, 20), outline=fg, width=w)
        line(((12, 10), (12, 17)), accent)
        d.ellipse(box(11.2, 6.5, 12.8, 8.1), fill=accent)
    elif icone == "document":
        points = ((6, 3), (15, 3), (19, 7), (19, 21), (6, 21), (6, 3))
        line(points, fg)
        line(((15, 3), (15, 8), (19, 8)), accent)
        line(((9, 12), (16, 12)))
        line(((9, 16), (16, 16)))
    elif icone == "phone":
        line(((7, 5), (5, 7), (7, 13), (11, 17), (17, 19), (19, 17)), fg)
        line(((6, 6), (9, 10)), accent)
        line(((15, 15), (18, 18)), accent)
    else:
        return False

    try:
        resampling = Image.Resampling.LANCZOS
    except AttributeError:
        resampling = Image.LANCZOS
    image = image.resize((int(taille), int(taille)), resampling)
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    image.save(destination, format="PNG", optimize=True)
    return True


def GetLegacyOverridePath(chemin):
    """Retourne un PNG moderne en cache, ou None pour conserver l'ancien."""
    icone = _icone_pour_chemin(chemin)
    if icone is None:
        return None

    taille = _taille_pour_chemin(chemin)
    if taille not in (16, 20, 24, 32, 48):
        return None

    dossier = os.path.join(tempfile.gettempdir(), "noethys-modern-icons-%s" % _CACHE_VERSION)
    destination = os.path.join(dossier, "%s-%d.png" % (icone, taille))
    if os.path.isfile(destination):
        return destination

    try:
        if _dessiner(icone, taille, destination):
            return destination
    except Exception:
        pass
    return None
