#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fournisseur de champs pour la catégorie de document Convention.

Sépare strictement :
- l'accès aux données Noethys (représentant, planning, tarifs), qui
  réutilise les mêmes mécanismes que le reste de l'application
  (UTILS_Infos_individus, UTILS_Impression_reservations.GetDonnees) ;
- le calcul pur (détection de tarif, résumé de planning), testable sans
  base de données ni wx.

Ne modifie jamais aucune donnée Noethys : les valeurs calculées ici ne
servent qu'à préremplir des champs de convention, jamais à corriger des
prestations existantes. Aucune saison, aucune structure, aucun taux
n'est jamais rendu obligatoire : ce qui ne peut pas être déterminé
automatiquement reste vide, à saisir manuellement.
"""

from __future__ import annotations

import datetime
from decimal import Decimal, InvalidOperation

from Utils.UTILS_Traduction import _

JOURS_SEMAINE = [
    _(u"Lundi"), _(u"Mardi"), _(u"Mercredi"), _(u"Jeudi"),
    _(u"Vendredi"), _(u"Samedi"), _(u"Dimanche"),
]


# ---------------------------------------------------------------------------
# Représentant : réutilise le mécanisme historique {REPRESENTANT_RATTACHE_x_*}
# ---------------------------------------------------------------------------

def GetRepresentant(IDfamille, informations=None):
    """ Retourne {"nom", "prenom", "nom_complet"} du premier représentant
    rattaché réellement nommé (une personne physique, donc avec un
    prénom), en réutilisant le dict {REPRESENTANT_RATTACHE_x_*} déjà
    calculé par UTILS_Infos_individus.Informations pour la fiche Famille.

    Renvoie None si aucun représentant nommé n'est rattaché : c'est le
    cas, par exemple, d'une famille qui ne représente qu'une structure
    (titulaire sans prénom, aucun contact secondaire) -- l'identité du
    représentant doit alors être saisie manuellement, elle n'existe nulle
    part dans Noethys pour cette famille.
    """
    if informations is None:
        from Utils import UTILS_Infos_individus
        informations = UTILS_Infos_individus.Informations(
            qf=False, inscriptions=False, messages=False, infosMedicales=False,
            cotisationsManquantes=False, piecesManquantes=False,
            questionnaires=False, scolarite=False, cotisations=False,
        )
    dictValeurs = informations.GetDictValeurs(mode="famille", ID=IDfamille, formatChamp=True)
    try:
        nbre = int(dictValeurs.get("{NBRE_REPRESENTANTS_RATTACHES}", 0) or 0)
    except (TypeError, ValueError):
        nbre = 0

    for index in range(1, nbre + 1):
        prefixe = "REPRESENTANT_RATTACHE_%d" % index
        prenom = (dictValeurs.get("{%s_PRENOM}" % prefixe) or u"").strip()
        if not prenom:
            # Entrée institutionnelle (la structure elle-même) : pas une
            # personne à présenter comme représentant.
            continue
        nom = (dictValeurs.get("{%s_NOM}" % prefixe) or u"").strip()
        nom_complet = (dictValeurs.get("{%s_NOM_COMPLET}" % prefixe) or u"").strip()
        return {"nom": nom, "prenom": prenom, "nom_complet": nom_complet}
    return None


# ---------------------------------------------------------------------------
# Tarifs : automatique si déterministe, manuel sinon
# ---------------------------------------------------------------------------

def _duree_heures(heure_debut, heure_fin):
    try:
        h1, m1 = (int(x) for x in str(heure_debut).split(":")[:2])
        h2, m2 = (int(x) for x in str(heure_fin).split(":")[:2])
    except (ValueError, TypeError, AttributeError):
        return None
    minutes = (h2 * 60 + m2) - (h1 * 60 + m1)
    if minutes <= 0:
        return None
    return minutes / 60.0


def _montant_decimal(montant):
    try:
        return Decimal(str(montant))
    except (InvalidOperation, TypeError):
        return None


def _iter_consommations(dictDonnees):
    for dictIndividu in dictDonnees.values():
        for IDactivite, dictActivite in dictIndividu["activites"].items():
            for date, dictDate in dictActivite["dates"].items():
                for IDunite, listeConso in dictDate["unites"].items():
                    for conso in listeConso:
                        yield IDactivite, date, conso


def DetecterTarifs(dictDonnees):
    """ Analyse les prestations et durées réellement enregistrées pour
    proposer un ou plusieurs taux horaires. Ne modifie jamais les
    prestations Noethys : le résultat ne sert qu'à préremplir des champs
    Convention, toujours modifiables avant génération.

    Retourne un dict :
    - mode="unique"  : un seul taux horaire ressort, sans ambiguïté,
      quelle que soit l'activité -> {CONVENTION_TARIF_HORAIRE} ;
    - mode="detail"  : chaque activité a son propre taux stable, mais les
      activités ont des taux différents entre elles (ex. adulte/enfant) ;
    - mode="manuel"  : au moins une activité présente des taux
      incohérents pour une même durée -> aucune valeur fiable à
      proposer automatiquement pour elle.
    """
    tauxParActivite = {}
    for IDactivite, date, conso in _iter_consommations(dictDonnees):
        prestation = conso.get("prestation")
        if not prestation or prestation.get("montant") is None:
            continue
        duree = _duree_heures(conso.get("heure_debut"), conso.get("heure_fin"))
        if not duree:
            continue
        montant = _montant_decimal(prestation["montant"])
        if montant is None:
            continue
        taux = (montant / Decimal(str(duree))).quantize(Decimal("0.01"))
        tauxParActivite.setdefault(IDactivite, set()).add(taux)

    tauxRetenus = {}
    ambigu = False
    for IDactivite, ensembleTaux in tauxParActivite.items():
        if len(ensembleTaux) == 1:
            tauxRetenus[IDactivite] = next(iter(ensembleTaux))
        else:
            ambigu = True

    if ambigu or not tauxRetenus:
        return {"mode": "manuel", "taux_par_activite": tauxRetenus}

    valeursDistinctes = set(tauxRetenus.values())
    if len(valeursDistinctes) == 1:
        return {"mode": "unique", "taux": next(iter(valeursDistinctes)), "taux_par_activite": tauxRetenus}

    return {"mode": "detail", "taux_par_activite": tauxRetenus}


# ---------------------------------------------------------------------------
# Résumé du planning : déterministe, factuel, sans invention
# ---------------------------------------------------------------------------

def _jour_semaine(date):
    try:
        if isinstance(date, datetime.date):
            return date.weekday()
        return datetime.datetime.strptime(str(date)[:10], "%Y-%m-%d").date().weekday()
    except (ValueError, TypeError):
        return None


def _formate_heure(heure):
    if not heure:
        return u"?"
    return str(heure)[:5].replace(":", "h")


def GetResumePlanning(dictDonnees):
    """ Construit un résumé textuel déterministe du planning, individu
    (groupe/cycle) par individu, à partir du même dict que
    UTILS_Impression_reservations.GetDonnees()/Impression().

    Ne fabrique aucune information absente des données fournies : les
    libellés utilisés sont ceux réellement enregistrés dans Noethys
    (nom d'activité, nom/prénom de l'individu représentant le
    créneau/cycle). Si une information figurant dans un ancien document
    papier (discipline précise, lieu de pratique, ...) n'existe dans
    aucune de ces données, elle n'apparaît pas ici : elle reste du
    contenu manuel du modèle ou de la saisie ponctuelle.
    """
    total_minutes = 0
    total_montant = Decimal("0")
    total_seances = 0
    blocs = []

    for dictIndividu in dictDonnees.values():
        label_individu = u" ".join(
            partie for partie in (dictIndividu.get("nom"), dictIndividu.get("prenom")) if partie
        ).strip()

        creneaux = {}
        for IDactivite, dictActivite in dictIndividu["activites"].items():
            for date, dictDate in dictActivite["dates"].items():
                for listeConso in dictDate["unites"].values():
                    for conso in listeConso:
                        total_seances += 1
                        duree = _duree_heures(conso.get("heure_debut"), conso.get("heure_fin"))
                        if duree:
                            total_minutes += int(round(duree * 60))
                        prestation = conso.get("prestation")
                        if prestation and prestation.get("montant") is not None:
                            montant = _montant_decimal(prestation["montant"])
                            if montant is not None:
                                total_montant += montant

                        jour = _jour_semaine(date)
                        cle = (jour, conso.get("heure_debut"), conso.get("heure_fin"))
                        creneaux.setdefault(cle, {"nom_activite": set(), "dates": []})
                        creneaux[cle]["nom_activite"].add(dictActivite.get("nom") or u"")
                        creneaux[cle]["dates"].append(date)

        lignes_individu = []
        for (jour, heure_debut, heure_fin), info in sorted(
            creneaux.items(),
            key=lambda item: (item[0][0] if item[0][0] is not None else 7, item[0][1] or u""),
        ):
            nb = len(info["dates"])
            texte_activites = u", ".join(sorted(n for n in info["nom_activite"] if n))
            if jour is not None and heure_debut and heure_fin:
                ligne = _(u"%s de %s à %s") % (
                    JOURS_SEMAINE[jour], _formate_heure(heure_debut), _formate_heure(heure_fin))
            else:
                ligne = _(u"%d séance(s)") % nb
            if texte_activites:
                ligne += u" : %s" % texte_activites
            if nb > 1:
                dates_triees = sorted(info["dates"])
                ligne += _(u" (%d séances, du %s au %s)") % (
                    nb, _formate_date_fr(dates_triees[0]), _formate_date_fr(dates_triees[-1]))
            lignes_individu.append(ligne)

        if lignes_individu:
            if label_individu:
                blocs.append(label_individu + u" :\n" + u"\n".join(u"- " + l for l in lignes_individu))
            else:
                blocs.extend(lignes_individu)

    return {
        "detail": u"\n\n".join(blocs),
        "nbre_seances": total_seances,
        "total_heures_minutes": total_minutes,
        "total_montant": total_montant,
    }


def _formate_date_fr(date):
    try:
        if isinstance(date, datetime.date):
            d = date
        else:
            d = datetime.datetime.strptime(str(date)[:10], "%Y-%m-%d").date()
        return u"%02d/%02d/%04d" % (d.day, d.month, d.year)
    except (ValueError, TypeError):
        return str(date)


def FormateDureeHeures(minutes):
    return u"%dh%02d" % (minutes // 60, minutes % 60)


# ---------------------------------------------------------------------------
# Assemblage final du dictionnaire de champs {CODE} -> valeur
# ---------------------------------------------------------------------------

def GetChampsConvention(
    IDfamille, date_debut=None, date_fin=None, saison=None,
    listeIDindividus=None, DB=None, informations=None,
):
    """ Construit le dict {"{CODE}": valeur} pour la catégorie Convention.

    listeIDindividus : individus (créneaux/cycles/personnes) rattachés à
    la famille à prendre en compte pour le planning ; si None, tous les
    individus rattachés à la famille sont utilisés.

    Ne rend jamais aucun champ obligatoire : un représentant, une saison
    ou un tarif introuvables automatiquement donnent simplement un champ
    vide, à compléter manuellement avant génération.
    """
    from Utils import UTILS_Impression_reservations

    if listeIDindividus is None:
        listeIDindividus = _GetIndividusRattaches(IDfamille, DB=DB)

    dictDonnees = UTILS_Impression_reservations.GetDonnees(
        listeIDindividus=listeIDindividus, date_debut=date_debut, date_fin=date_fin, DB=DB,
    )

    champs = {"{IDFAMILLE}": IDfamille}

    representant = GetRepresentant(IDfamille, informations=informations)
    if representant is not None:
        champs["{CONVENTION_REPRESENTANT_NOM}"] = representant["nom"]
        champs["{CONVENTION_REPRESENTANT_PRENOM}"] = representant["prenom"]
        champs["{CONVENTION_REPRESENTANT_NOM_COMPLET}"] = representant["nom_complet"]

    if saison:
        champs["{CONVENTION_SAISON}"] = saison
    if date_debut:
        champs["{CONVENTION_DATE_DEBUT}"] = date_debut
    if date_fin:
        champs["{CONVENTION_DATE_FIN}"] = date_fin

    resume = GetResumePlanning(dictDonnees)
    champs["{CONVENTION_PLANNING_DETAIL}"] = resume["detail"]
    champs["{CONVENTION_PLANNING_NBRE_SEANCES}"] = resume["nbre_seances"]
    champs["{CONVENTION_PLANNING_TOTAL_HEURES}"] = FormateDureeHeures(resume["total_heures_minutes"])
    champs["{CONVENTION_PLANNING_TOTAL_MONTANT}"] = float(resume["total_montant"])

    tarifs = DetecterTarifs(dictDonnees)
    if tarifs["mode"] == "unique":
        champs["{CONVENTION_TARIF_HORAIRE}"] = float(tarifs["taux"])
    elif tarifs["mode"] == "detail":
        _CompleterTarifsAdulteEnfant(champs, tarifs["taux_par_activite"], dictDonnees)

    return champs, dictDonnees


def _CompleterTarifsAdulteEnfant(champs, tauxParActivite, dictDonnees):
    """ Quand plusieurs taux cohérents existent (mode="detail"), les
    exposer sous {CONVENTION_TARIF_ADULTE}/{CONVENTION_TARIF_ENFANT}
    uniquement si le nom réel de l'activité (tel qu'enregistré dans
    Noethys) permet de le déterminer sans ambiguïté -- jamais en
    devinant. Sinon, taux_par_activite reste disponible dans le résultat
    de DetecterTarifs() pour un usage plus générique par l'appelant. """
    nomsActivites = {}
    for dictIndividu in dictDonnees.values():
        for IDactivite, dictActivite in dictIndividu["activites"].items():
            nomsActivites[IDactivite] = dictActivite.get("nom") or u""

    for IDactivite, taux in tauxParActivite.items():
        nom = nomsActivites.get(IDactivite, u"").lower()
        if "enfant" in nom and "{CONVENTION_TARIF_ENFANT}" not in champs:
            champs["{CONVENTION_TARIF_ENFANT}"] = float(taux)
        elif "adulte" in nom and "{CONVENTION_TARIF_ADULTE}" not in champs:
            champs["{CONVENTION_TARIF_ADULTE}"] = float(taux)


def _GetIndividusRattaches(IDfamille, DB=None):
    fermer = DB is None
    if DB is None:
        import GestionDB
        DB = GestionDB.DB()
    DB.ExecuterReq(
        "SELECT IDindividu FROM rattachements WHERE IDfamille=%d;" % int(IDfamille)
    )
    listeIndividus = [row[0] for row in DB.ResultatReq()]
    if fermer:
        DB.Close()
    return listeIndividus
