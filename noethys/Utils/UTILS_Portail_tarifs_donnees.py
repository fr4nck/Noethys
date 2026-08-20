#!/usr/bin/env python
# -*- coding: utf-8 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activités
# Site internet :  www.noethys.com
# Licence:          GNU GPL
#------------------------------------------------------------------------

"""Lecture des barèmes Noethys pour publication.

Cette couche lit les mêmes tables que le moteur historique de facturation mais
ne calcule aucun prix. Elle produit les dictionnaires attendus par
``UTILS_Portail_tarifs`` et garde l'accès SQL séparé du descripteur pur.

La connexion DB est fournie par l'appelant et n'est jamais fermée ici.
"""

from Data.DATA_Tables import DB_DATA


CHAMPS_TARIFS = (
    "IDtarif", "IDactivite", "IDnom_tarif", "nom_tarif", "date_debut", "date_fin",
    "condition_nbre_combi", "condition_periode", "condition_nbre_jours",
    "condition_conso_facturees", "condition_dates_continues", "methode",
    "categories_tarifs", "groupes", "etiquettes", "type", "forfait_duree",
    "forfait_beneficiaire", "cotisations", "caisses", "jours_scolaires",
    "jours_vacances", "code_compta", "code_produit_local", "tva",
    "date_facturation", "etats", "IDtype_quotient", "description",
    "label_prestation", "options", "IDevenement",
)

CHAMPS_LISTES_IDS = (
    "categories_tarifs",
    "groupes",
    "etiquettes",
    "cotisations",
    "caisses",
    "jours_scolaires",
    "jours_vacances",
)


def convertir_liste_ids(valeur, type_texte=False):
    """Reprend le format historique Noethys ``1;2;3`` sans dépendance GUI."""
    if valeur in (None, ""):
        return None
    if isinstance(valeur, (list, tuple)):
        return list(valeur)
    if isinstance(valeur, int):
        return [valeur]

    resultats = []
    for item in str(valeur).split(";"):
        item = item.strip()
        if not item:
            continue
        if type_texte:
            resultats.append(item)
        else:
            try:
                resultats.append(int(item))
            except (TypeError, ValueError):
                # Une donnée historique illisible ne doit pas faire échouer
                # toute la publication ; elle est conservée comme texte afin
                # d'être visible lors d'une recette réelle.
                resultats.append(item)
    return resultats or None


def _executer(DB, requete):
    if not DB.ExecuterReq(requete):
        raise RuntimeError("Lecture des barèmes impossible")
    return DB.ResultatReq()


def _charger_activites(DB):
    lignes = _executer(DB, """SELECT IDactivite, nom
    FROM activites
    ORDER BY nom;""")
    return {IDactivite: nom for IDactivite, nom in lignes}


def _charger_categories(DB):
    lignes = _executer(DB, """SELECT IDcategorie_tarif, IDactivite, nom
    FROM categories_tarifs
    ORDER BY IDactivite, nom;""")
    return {
        IDcategorie_tarif: {"IDactivite": IDactivite, "nom": nom}
        for IDcategorie_tarif, IDactivite, nom in lignes
    }


def _charger_lignes_calcul(DB):
    champs = [champ[0] for champ in DB_DATA["tarifs_lignes"]]
    requete = """SELECT %s
    FROM tarifs_lignes
    WHERE IDmodele IS NULL
    ORDER BY IDtarif, num_ligne;""" % ", ".join(champs)
    lignes = _executer(DB, requete)

    resultats = {}
    for valeurs in lignes:
        ligne = {}
        for index, valeur in enumerate(valeurs):
            if valeur == "None":
                valeur = None
            ligne[champs[index]] = valeur
        resultats.setdefault(ligne.get("IDtarif"), []).append(ligne)
    return resultats


def _charger_filtres(DB):
    """La présence d'un filtre suffit pour classer le barème comme contextuel."""
    lignes = _executer(DB, """SELECT IDfiltre, IDtarif
    FROM questionnaire_filtres
    WHERE IDtarif IS NOT NULL;""")
    resultats = {}
    for IDfiltre, IDtarif in lignes:
        resultats.setdefault(IDtarif, []).append({"IDfiltre": IDfiltre})
    return resultats


def _charger_tarifs(DB):
    lignes = _executer(DB, """SELECT
    tarifs.IDtarif, tarifs.IDactivite, tarifs.IDnom_tarif, noms_tarifs.nom,
    tarifs.date_debut, tarifs.date_fin,
    tarifs.condition_nbre_combi, tarifs.condition_periode,
    tarifs.condition_nbre_jours, tarifs.condition_conso_facturees,
    tarifs.condition_dates_continues, tarifs.methode,
    tarifs.categories_tarifs, tarifs.groupes, tarifs.etiquettes, tarifs.type,
    tarifs.forfait_duree, tarifs.forfait_beneficiaire, tarifs.cotisations,
    tarifs.caisses, tarifs.jours_scolaires, tarifs.jours_vacances,
    tarifs.code_compta, tarifs.code_produit_local, tarifs.tva,
    tarifs.date_facturation, tarifs.etats, tarifs.IDtype_quotient,
    tarifs.description, tarifs.label_prestation, tarifs.options,
    tarifs.IDevenement
    FROM tarifs
    LEFT JOIN noms_tarifs ON noms_tarifs.IDnom_tarif = tarifs.IDnom_tarif
    ORDER BY tarifs.IDactivite, tarifs.date_debut, tarifs.IDtarif;""")

    resultats = []
    for valeurs in lignes:
        tarif = dict(zip(CHAMPS_TARIFS, valeurs))
        for champ in CHAMPS_LISTES_IDS:
            tarif[champ] = convertir_liste_ids(tarif.get(champ))
        tarif["etats"] = convertir_liste_ids(tarif.get("etats"), type_texte=True)
        resultats.append(tarif)
    return resultats


def charger_baremes(DB, IDsactivites=None):
    """Charge et enrichit les barèmes, puis les développe par catégorie tarifaire."""
    activites = _charger_activites(DB)
    categories = _charger_categories(DB)
    lignes_calcul = _charger_lignes_calcul(DB)
    filtres = _charger_filtres(DB)
    tarifs = _charger_tarifs(DB)

    filtre_activites = set(IDsactivites) if IDsactivites else None
    resultats = []

    for tarif in tarifs:
        IDactivite = tarif.get("IDactivite")
        if filtre_activites is not None and IDactivite not in filtre_activites:
            continue

        base = dict(tarif)
        base["nom_activite"] = activites.get(IDactivite, "")
        base["lignes_calcul"] = list(lignes_calcul.get(base.get("IDtarif"), []))
        base["filtres"] = list(filtres.get(base.get("IDtarif"), []))

        IDs_categories = base.get("categories_tarifs") or [None]
        for IDcategorie_tarif in IDs_categories:
            item = dict(base)
            item["IDcategorie_tarif"] = IDcategorie_tarif
            categorie = categories.get(IDcategorie_tarif, {})
            if categorie and categorie.get("IDactivite") != IDactivite:
                # Donnée historique incohérente : ne pas attribuer le nom d'une
                # catégorie appartenant à une autre activité.
                item["nom_categorie_tarif"] = ""
            else:
                item["nom_categorie_tarif"] = categorie.get("nom", "")
            resultats.append(item)

    return resultats
