#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Outils de recherche utilisateur tolérante.

Ce module ne modifie jamais les données enregistrées. Il construit uniquement
un index de recherche normalisé pour les interfaces de recherche rapide.
"""

import re
import unicodedata


_RE_NON_ALNUM = re.compile(r"[^0-9a-z]+")
_RE_CHIFFRES = re.compile(r"\D+")


def NormaliserTexte(valeur):
    """Retourne une forme comparable, sans accents, casse ni ponctuation.

    Exemples : ``Noé`` -> ``noe``, ``Noë`` -> ``noe``,
    ``La-Guerche`` -> ``la guerche``.
    """
    if valeur is None:
        return ""
    texte = str(valeur).casefold()
    texte = unicodedata.normalize("NFKD", texte)
    texte = "".join(car for car in texte if not unicodedata.combining(car))
    texte = _RE_NON_ALNUM.sub(" ", texte)
    return " ".join(texte.split())


def NormaliserNumero(valeur):
    if valeur is None:
        return ""
    return _RE_CHIFFRES.sub("", str(valeur))


def DistanceDamerauLimitee(a, b, limite=1):
    """Distance d'édition avec transposition, interrompue au-delà de ``limite``.

    L'usage UI actuel limite volontairement la tolérance à une seule erreur.
    """
    if a == b:
        return 0
    if abs(len(a) - len(b)) > limite:
        return limite + 1
    if not a or not b:
        return max(len(a), len(b))

    precedent_precedent = None
    precedent = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        courant = [i]
        minimum_ligne = i
        for j, cb in enumerate(b, 1):
            cout = 0 if ca == cb else 1
            valeur = min(
                courant[j - 1] + 1,
                precedent[j] + 1,
                precedent[j - 1] + cout,
            )
            if (
                precedent_precedent is not None
                and i > 1
                and j > 1
                and ca == b[j - 2]
                and a[i - 2] == cb
            ):
                valeur = min(valeur, precedent_precedent[j - 2] + 1)
            courant.append(valeur)
            minimum_ligne = min(minimum_ligne, valeur)
        if minimum_ligne > limite:
            return limite + 1
        precedent_precedent, precedent = precedent, courant
    return precedent[-1]


def ConstruireIndex(objet, attributs=(), attributs_telephones=()):
    morceaux = []
    for attribut in attributs:
        morceaux.append(NormaliserTexte(getattr(objet, attribut, "")))
    texte = " ".join(morceau for morceau in morceaux if morceau)
    mots = tuple(dict.fromkeys(texte.split()))
    telephones = tuple(
        numero
        for numero in (NormaliserNumero(getattr(objet, attribut, "")) for attribut in attributs_telephones)
        if numero
    )
    return {"texte": texte, "mots": mots, "telephones": telephones}


def _CorrespondanceExacte(index, recherche):
    recherche = NormaliserTexte(recherche)
    if not recherche:
        return True
    termes = recherche.split()

    # Un numéro tapé sans espaces doit retrouver 06 12 34 56 78.
    chiffres = NormaliserNumero(recherche)
    if chiffres and len(chiffres) >= 4 and chiffres == recherche.replace(" ", ""):
        if any(chiffres in numero for numero in index.get("telephones", ())):
            return True

    return all(terme in index.get("texte", "") for terme in termes)


def _TermeApproximatif(terme, mots):
    # Sur trois lettres (Léa/Léo, Tom/Tim...), une substitution est trop
    # ambiguë. Une faute comme ``nhoe`` reste couverte car le terme saisi
    # comporte quatre lettres et peut matcher ``noe`` à distance 1.
    if len(terme) < 4 or not terme.isalpha():
        return False
    for mot in mots:
        if not mot.isalpha():
            continue
        if terme in mot or mot in terme:
            return True
        if abs(len(terme) - len(mot)) <= 1 and DistanceDamerauLimitee(terme, mot, 1) <= 1:
            return True
    return False


def Correspond(index, recherche, approximatif=False):
    """Teste une recherche contre un index.

    Le fuzzy est volontairement opt-in. L'UI doit d'abord tenter une recherche
    exacte normalisée puis seulement, si aucun résultat n'existe, recommencer
    avec ``approximatif=True``.
    """
    if _CorrespondanceExacte(index, recherche):
        return True
    if not approximatif:
        return False

    recherche_norm = NormaliserTexte(recherche)
    if not recherche_norm:
        return True

    for terme in recherche_norm.split():
        if terme in index.get("texte", ""):
            continue
        if terme.isdigit():
            if not any(terme in numero for numero in index.get("telephones", ())):
                return False
            continue
        if not _TermeApproximatif(terme, index.get("mots", ())):
            return False
    return True
