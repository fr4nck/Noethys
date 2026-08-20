#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Licence:          GNU GPL
#------------------------------------------------------------------------

"""Helpers purs pour les contenus dynamiques du portail Connecthys.

Noethys conserve une configuration enrichie localement mais exporte vers un
Connecthys historique un bloc texte HTML compatible. Les contenus RSS/Atom
sont transformés en HTML sûr par Noethys : aucun HTML provenant du flux n'est
injecté tel quel dans le portail.
"""

import datetime
import html
import json
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


CATEGORIE_CONTENU_EXTERNE = "bloc_contenu_externe"
CATEGORIE_CONNECTHYS_TEXTE = "bloc_texte"
MARQUEUR_CONTENU_EXTERNE = "noethys_portail_contenu_externe"

TYPE_IFRAME = "iframe"
TYPE_RSS = "rss"

HAUTEUR_MIN = 120
HAUTEUR_MAX = 3000
HAUTEUR_DEFAUT = 600

RSS_NOMBRE_MIN = 1
RSS_NOMBRE_MAX = 20
RSS_NOMBRE_DEFAUT = 5
RSS_TIMEOUT_DEFAUT = 5
RSS_TAILLE_MAX = 2 * 1024 * 1024
RSS_EXTRAIT_MAX = 600


class _TexteHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.fragments = []

    def handle_data(self, data):
        if data:
            self.fragments.append(data)

    def texte(self):
        return " ".join(" ".join(self.fragments).split())


def texte_sans_html(valeur):
    """Convertit un fragment HTML/XML externe en texte brut compact."""
    if valeur is None:
        return ""
    parser = _TexteHTMLParser()
    try:
        parser.feed(str(valeur))
        parser.close()
        return html.unescape(parser.texte())
    except Exception:
        return " ".join(str(valeur).split())


def normaliser_url(url):
    """Retourne une URL externe nettoyée sans tenter de la télécharger."""
    if url is None:
        return ""
    return str(url).strip()


def url_externe_valide(url):
    """Accepte uniquement les URL HTTP(S) absolues."""
    url = normaliser_url(url)
    if not url:
        return False
    try:
        parsed = urlparse(url)
    except (TypeError, ValueError):
        return False
    return parsed.scheme.lower() in ("http", "https") and bool(parsed.netloc)


def normaliser_hauteur(hauteur):
    """Normalise la hauteur d'un iframe dans une plage raisonnable."""
    try:
        valeur = int(hauteur)
    except (TypeError, ValueError):
        valeur = HAUTEUR_DEFAUT
    return max(HAUTEUR_MIN, min(HAUTEUR_MAX, valeur))


def normaliser_nombre_articles(nombre):
    try:
        valeur = int(nombre)
    except (TypeError, ValueError):
        valeur = RSS_NOMBRE_DEFAUT
    return max(RSS_NOMBRE_MIN, min(RSS_NOMBRE_MAX, valeur))


def normaliser_parametres(parametres=None):
    """Retourne la configuration canonique d'un bloc de contenu externe."""
    source = dict(parametres or {})
    type_contenu = source.get("type", TYPE_IFRAME)
    if type_contenu not in (TYPE_IFRAME, TYPE_RSS):
        type_contenu = TYPE_IFRAME
    return {
        "source": MARQUEUR_CONTENU_EXTERNE,
        "version": 1,
        "type": type_contenu,
        "url": normaliser_url(source.get("url", "")),
        "hauteur": normaliser_hauteur(source.get("hauteur", HAUTEUR_DEFAUT)),
        "defilement": bool(source.get("defilement", False)),
        "plein_ecran": bool(source.get("plein_ecran", True)),
        "titre": str(source.get("titre", "") or "").strip(),
        "nombre_articles": normaliser_nombre_articles(source.get("nombre_articles", RSS_NOMBRE_DEFAUT)),
        "afficher_date": bool(source.get("afficher_date", True)),
        "afficher_extrait": bool(source.get("afficher_extrait", True)),
        "liens_nouvel_onglet": bool(source.get("liens_nouvel_onglet", True)),
    }


def serialiser_parametres(parametres=None):
    """Sérialise la configuration locale dans le champ parametres existant."""
    return json.dumps(
        normaliser_parametres(parametres),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _charger_json(valeur):
    if not valeur:
        return {}
    if isinstance(valeur, bytes):
        valeur = valeur.decode("utf-8")
    try:
        donnees = json.loads(valeur)
    except (TypeError, ValueError):
        return {}
    return donnees if isinstance(donnees, dict) else {}


def est_configuration_contenu_externe(valeur):
    """Détecte uniquement les paramètres écrits par ce moteur, sans faux positif."""
    return _charger_json(valeur).get("source") == MARQUEUR_CONTENU_EXTERNE


def est_configuration_dynamique(valeur):
    """Indique si le bloc doit être régénéré à chaque synchronisation."""
    if not est_configuration_contenu_externe(valeur):
        return False
    return deserialiser_parametres(valeur)["type"] == TYPE_RSS


def deserialiser_parametres(valeur):
    """Lit une configuration sauvegardée et retombe sur les valeurs par défaut."""
    return normaliser_parametres(_charger_json(valeur))


def construire_iframe(parametres=None):
    """Construit le HTML compatible avec un bloc texte Connecthys historique."""
    config = normaliser_parametres(parametres)
    if config["type"] != TYPE_IFRAME:
        raise ValueError("Type de contenu externe non pris en charge par l'iframe : %s" % config["type"])
    if not url_externe_valide(config["url"]):
        raise ValueError("URL externe invalide")

    attributs = [
        ("src", config["url"]),
        ("width", "100%"),
        ("height", "%d" % config["hauteur"]),
        ("loading", "lazy"),
        ("scrolling", "yes" if config["defilement"] else "no"),
        ("frameborder", "0"),
    ]
    if config["titre"]:
        attributs.append(("title", config["titre"]))

    texte_attributs = " ".join(
        '%s="%s"' % (nom, html.escape(str(valeur), quote=True))
        for nom, valeur in attributs
    )
    if config["plein_ecran"]:
        texte_attributs += " allowfullscreen"

    return '<iframe %s></iframe>' % texte_attributs


def _nom_local(tag):
    return str(tag).rsplit("}", 1)[-1].lower()


def _enfant_texte(element, noms):
    noms = set(x.lower() for x in noms)
    for enfant in list(element):
        if _nom_local(enfant.tag) in noms:
            return "".join(enfant.itertext()).strip()
    return ""


def _lien_atom(entry):
    repli = ""
    for enfant in list(entry):
        if _nom_local(enfant.tag) != "link":
            continue
        href = normaliser_url(enfant.attrib.get("href", ""))
        rel = enfant.attrib.get("rel", "alternate").lower()
        if href and rel in ("", "alternate"):
            return href
        if href and not repli:
            repli = href
    return repli


def _date_affichable(valeur):
    valeur = (valeur or "").strip()
    if not valeur:
        return ""
    date = None
    try:
        date = parsedate_to_datetime(valeur)
    except (TypeError, ValueError, OverflowError):
        pass
    if date is None:
        try:
            date = datetime.datetime.fromisoformat(valeur.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return ""
    return date.strftime("%d/%m/%Y")


def _article(titre="", lien="", extrait="", date=""):
    titre = texte_sans_html(titre).strip() or "Actualité"
    extrait = texte_sans_html(extrait).strip()
    if len(extrait) > RSS_EXTRAIT_MAX:
        extrait = extrait[:RSS_EXTRAIT_MAX].rstrip() + "…"
    lien = normaliser_url(lien)
    if not url_externe_valide(lien):
        lien = ""
    return {
        "titre": titre,
        "lien": lien,
        "extrait": extrait,
        "date": _date_affichable(date),
    }


def parser_flux_rss_atom(contenu):
    """Parse RSS 2.0 ou Atom et retourne une liste d'articles normalisés."""
    if isinstance(contenu, str):
        contenu = contenu.encode("utf-8")
    try:
        racine = ET.fromstring(contenu)
    except (ET.ParseError, TypeError, ValueError) as err:
        raise ValueError("Flux XML invalide : %s" % err)

    nom_racine = _nom_local(racine.tag)
    articles = []

    if nom_racine == "rss":
        channel = None
        for enfant in list(racine):
            if _nom_local(enfant.tag) == "channel":
                channel = enfant
                break
        if channel is None:
            raise ValueError("Flux RSS sans canal")
        for item in list(channel):
            if _nom_local(item.tag) != "item":
                continue
            articles.append(_article(
                titre=_enfant_texte(item, ("title",)),
                lien=_enfant_texte(item, ("link",)),
                extrait=_enfant_texte(item, ("description", "summary", "content")),
                date=_enfant_texte(item, ("pubdate", "date", "updated", "published")),
            ))

    elif nom_racine == "feed":
        for entry in list(racine):
            if _nom_local(entry.tag) != "entry":
                continue
            articles.append(_article(
                titre=_enfant_texte(entry, ("title",)),
                lien=_lien_atom(entry),
                extrait=_enfant_texte(entry, ("summary", "content", "description")),
                date=_enfant_texte(entry, ("updated", "published", "date")),
            ))
    else:
        raise ValueError("Format de flux non pris en charge")

    if not articles:
        raise ValueError("Le flux ne contient aucune actualité exploitable")
    return articles


def telecharger_flux(url, timeout=RSS_TIMEOUT_DEFAUT, taille_max=RSS_TAILLE_MAX, ouvreur=None):
    """Télécharge un flux avec délai et taille bornés."""
    if not url_externe_valide(url):
        raise ValueError("URL de flux invalide")
    ouvreur = ouvreur or urlopen
    requete = Request(url, headers={"User-Agent": "Noethys/Connecthys RSS"})
    reponse = ouvreur(requete, timeout=timeout)
    try:
        contenu = reponse.read(taille_max + 1)
    finally:
        try:
            reponse.close()
        except Exception:
            pass
    if len(contenu) > taille_max:
        raise ValueError("Flux trop volumineux")
    return contenu


def construire_flux_html(parametres=None, contenu=None, ouvreur=None):
    """Construit un rendu HTML sûr à partir d'un flux RSS/Atom."""
    config = normaliser_parametres(parametres)
    if config["type"] != TYPE_RSS:
        raise ValueError("Ce bloc n'est pas un flux RSS/Atom")
    if not url_externe_valide(config["url"]):
        raise ValueError("URL de flux invalide")

    if contenu is None:
        contenu = telecharger_flux(config["url"], ouvreur=ouvreur)
    articles = parser_flux_rss_atom(contenu)[:config["nombre_articles"]]

    rendu = ['<div class="noethys-rss">']
    for article in articles:
        rendu.append('<article style="padding:10px 0;border-bottom:1px solid #ddd;">')
        titre = html.escape(article["titre"], quote=True)
        if article["lien"]:
            cible = ' target="_blank" rel="noopener noreferrer"' if config["liens_nouvel_onglet"] else ""
            rendu.append('<div style="font-weight:600;"><a href="%s"%s>%s</a></div>' % (
                html.escape(article["lien"], quote=True), cible, titre))
        else:
            rendu.append('<div style="font-weight:600;">%s</div>' % titre)

        if config["afficher_date"] and article["date"]:
            rendu.append('<div style="font-size:0.9em;opacity:0.75;">%s</div>' % html.escape(article["date"], quote=True))
        if config["afficher_extrait"] and article["extrait"]:
            rendu.append('<div style="margin-top:4px;">%s</div>' % html.escape(article["extrait"], quote=True))
        rendu.append('</article>')
    rendu.append('</div>')
    return "".join(rendu)


def construire_placeholder_flux():
    return '<div class="noethys-rss"><p>Le flux d’actualités sera chargé lors de la prochaine synchronisation.</p></div>'


def construire_html(parametres=None, contenu=None, ouvreur=None):
    """Point d'entrée commun pour fabriquer le HTML d'un contenu externe."""
    config = normaliser_parametres(parametres)
    if config["type"] == TYPE_IFRAME:
        return construire_iframe(config)
    if config["type"] == TYPE_RSS:
        return construire_flux_html(config, contenu=contenu, ouvreur=ouvreur)
    raise ValueError("Type de contenu externe non pris en charge")


def categorie_pour_connecthys(categorie):
    """Mappe les catégories enrichies locales vers le vocabulaire Connecthys stable."""
    if categorie == CATEGORIE_CONTENU_EXTERNE:
        return CATEGORIE_CONNECTHYS_TEXTE
    return categorie
