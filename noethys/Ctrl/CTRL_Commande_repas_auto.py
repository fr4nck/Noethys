#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -----------------------------------------------------------
# Extension conservatrice du moteur historique de commandes de repas.
# Le fonctionnement manuel existant reste prioritaire. Lorsque le modèle
# ne contient aucun rattachement unité/groupe, les colonnes de suggestion
# sont construites à partir des réservations de repas réellement présentes.
# -----------------------------------------------------------

import ast
import datetime

import GestionDB
from Ctrl import CTRL_Commande_repas as CTRL_Commande_repas_legacy
from Utils import UTILS_Dates


AUTO_FLAG = "_noethys_auto_repas"
AUTO_SITE = "_noethys_auto_repas_site"
AUTO_ACTIVITY = "_noethys_auto_repas_activite"
AUTO_GROUP = "_noethys_auto_repas_groupe"


def _ParseParametres(parametres):
    if isinstance(parametres, dict):
        return parametres
    if parametres in (None, ""):
        return {}
    try:
        valeur = ast.literal_eval(parametres)
        return valeur if isinstance(valeur, dict) else {}
    except (ValueError, SyntaxError, TypeError):
        return {}


def _ConditionRepas(strict=True):
    if strict:
        return "unites.repas=1"
    # Repli destiné aux anciennes bases dans lesquelles le drapeau repas
    # n'aurait pas été renseigné alors que l'unité porte explicitement ce nom.
    return "(LOWER(unites.nom) LIKE '%repas%' OR LOWER(unites.nom) LIKE '%cantine%' OR LOWER(unites.nom) LIKE '%dejeuner%')"


def _RechercheReservations(date_debut, date_fin, strict=True):
    DB = GestionDB.DB()
    req = """SELECT consommations.IDactivite, activites.nom,
    consommations.IDgroupe, groupes.nom, consommations.IDunite
    FROM consommations
    LEFT JOIN unites ON unites.IDunite = consommations.IDunite
    LEFT JOIN activites ON activites.IDactivite = consommations.IDactivite
    LEFT JOIN groupes ON groupes.IDgroupe = consommations.IDgroupe
    WHERE consommations.date>='%s' AND consommations.date<='%s'
    AND consommations.etat IN ('reservation', 'present')
    AND %s
    GROUP BY consommations.IDactivite, activites.nom, consommations.IDgroupe, groupes.nom, consommations.IDunite
    ORDER BY activites.nom, groupes.ordre, groupes.nom, consommations.IDgroupe, consommations.IDunite;""" % (
        date_debut, date_fin, _ConditionRepas(strict=strict))
    DB.ExecuterReq(req)
    donnees = DB.ResultatReq()
    DB.Close()
    return donnees


def _CleGroupe(IDactivite, IDgroupe):
    return "activite:%s:groupe:%s" % (IDactivite, IDgroupe)


def RechercheReservationsRepas(date_debut, date_fin):
    """Construit les regroupements automatiques utiles aux commandes de repas.

    Noethys ne possède pas ici de notion générique de site physique. Une seule
    activité reste donc un regroupement suffisant tant qu'elle n'utilise qu'un
    groupe pour les repas. Lorsqu'une même activité comporte plusieurs groupes,
    on les sépare : c'est la donnée existante la plus fine avant l'unité et cela
    évite d'écraser plusieurs lieux/logiques d'accueil dans une seule colonne.
    """
    donnees = _RechercheReservations(date_debut, date_fin, strict=True)
    if not donnees:
        donnees = _RechercheReservations(date_debut, date_fin, strict=False)

    activites = {}
    ordre_activites = []
    for IDactivite, nom_activite, IDgroupe, nom_groupe, IDunite in donnees:
        if IDactivite is None or IDunite is None:
            continue
        if IDactivite not in activites:
            activites[IDactivite] = {
                "nom": nom_activite or "Repas",
                "groupes": {},
                "ordre_groupes": [],
            }
            ordre_activites.append(IDactivite)
        groupes = activites[IDactivite]["groupes"]
        if IDgroupe not in groupes:
            groupes[IDgroupe] = {
                "nom": nom_groupe,
                "unites": [],
            }
            activites[IDactivite]["ordre_groupes"].append(IDgroupe)
        couple = (IDgroupe, IDunite)
        if couple not in groupes[IDgroupe]["unites"]:
            groupes[IDgroupe]["unites"].append(couple)

    regroupements = []
    for IDactivite in ordre_activites:
        activite = activites[IDactivite]
        groupes_non_vides = [
            IDgroupe for IDgroupe in activite["ordre_groupes"]
            if activite["groupes"][IDgroupe]["unites"]
        ]
        if len(groupes_non_vides) <= 1:
            unites = []
            for IDgroupe in groupes_non_vides:
                unites.extend(activite["groupes"][IDgroupe]["unites"])
            regroupements.append({
                "cle": IDactivite,
                "IDactivite": IDactivite,
                "IDgroupe": groupes_non_vides[0] if groupes_non_vides else None,
                "nom": activite["nom"],
                "unites": unites,
            })
            continue

        for IDgroupe in groupes_non_vides:
            groupe = activite["groupes"][IDgroupe]
            nom_groupe = groupe["nom"] or ("Groupe %s" % IDgroupe)
            regroupements.append({
                "cle": _CleGroupe(IDactivite, IDgroupe),
                "IDactivite": IDactivite,
                "IDgroupe": IDgroupe,
                "nom": nom_groupe,
                "unites": groupe["unites"],
            })

    return regroupements


def GetProchainePeriodeRepas(nb_jours=14):
    """Cherche la prochaine réservation de repas et propose une courte période."""
    aujourd_hui = datetime.date.today()

    def recherche(strict=True):
        DB = GestionDB.DB()
        req = """SELECT MIN(consommations.date)
        FROM consommations
        LEFT JOIN unites ON unites.IDunite = consommations.IDunite
        WHERE consommations.date>='%s'
        AND consommations.etat IN ('reservation', 'present')
        AND %s;""" % (aujourd_hui, _ConditionRepas(strict=strict))
        DB.ExecuterReq(req)
        resultat = DB.ResultatReq()
        DB.Close()
        if resultat and resultat[0] and resultat[0][0]:
            return UTILS_Dates.DateEngEnDateDD(resultat[0][0])
        return None

    premiere_date = recherche(strict=True) or recherche(strict=False)
    if premiere_date is None:
        return None, None
    return premiere_date, premiere_date + datetime.timedelta(days=max(1, nb_jours) - 1)


def AssureColonnesAutomatiques(IDmodele, date_debut, date_fin):
    """Complète un modèle non configuré à partir des réservations réelles.

    Une configuration historique explicite n'est jamais modifiée. Une colonne
    automatique créée par une version précédente (clé = IDactivité) est aussi
    conservée telle quelle et continue d'absorber tous les groupes de l'activité.
    """
    if IDmodele is None or date_debut is None or date_fin is None:
        return False

    DB = GestionDB.DB()
    req = """SELECT IDcolonne, ordre, nom, largeur, categorie, parametres
    FROM modeles_commandes_colonnes
    WHERE IDmodele=%d
    ORDER BY ordre;""" % IDmodele
    DB.ExecuterReq(req)
    colonnes = DB.ResultatReq()

    colonnes_auto = {}
    ordre_max = -1
    for IDcolonne, ordre, nom, largeur, categorie, parametres in colonnes:
        ordre_max = max(ordre_max, ordre if ordre is not None else -1)
        params = _ParseParametres(parametres)
        unites = params.get("unites", [])
        if unites and not params.get(AUTO_FLAG, False):
            DB.Close()
            return False
        if params.get(AUTO_FLAG, False) and params.get(AUTO_SITE) is not None:
            colonnes_auto[params[AUTO_SITE]] = {
                "IDcolonne": IDcolonne,
                "parametres": params,
            }

    regroupements = RechercheReservationsRepas(date_debut, date_fin)
    if not regroupements:
        DB.Close()
        return False

    # Compatibilité avec les premières colonnes automatiques : si une activité
    # dispose déjà d'une colonne auto historique, on ne la scinde pas après coup.
    regroupements_effectifs = []
    par_activite = {}
    for item in regroupements:
        par_activite.setdefault(item["IDactivite"], []).append(item)
    for IDactivite, items in par_activite.items():
        if IDactivite in colonnes_auto:
            unites = []
            for item in items:
                for couple in item["unites"]:
                    if couple not in unites:
                        unites.append(couple)
            regroupements_effectifs.append({
                "cle": IDactivite,
                "IDactivite": IDactivite,
                "IDgroupe": None,
                "nom": items[0]["nom"],
                "unites": unites,
            })
        else:
            regroupements_effectifs.extend(items)

    modifie = False
    prochain_ordre = ordre_max + 1
    for item in regroupements_effectifs:
        cle = item["cle"]
        unites = item["unites"]
        if not unites:
            continue
        if cle in colonnes_auto:
            colonne = colonnes_auto[cle]
            params = colonne["parametres"]
            anciennes_unites = [tuple(valeur) for valeur in params.get("unites", [])]
            nouvelles_unites = list(anciennes_unites)
            for couple in unites:
                if tuple(couple) not in nouvelles_unites:
                    nouvelles_unites.append(tuple(couple))
            if nouvelles_unites != anciennes_unites:
                params["unites"] = nouvelles_unites
                DB.ReqMAJ("modeles_commandes_colonnes", [("parametres", str(params)),], "IDcolonne", colonne["IDcolonne"])
                modifie = True
            continue

        params = {
            "unites": [tuple(valeur) for valeur in unites],
            AUTO_FLAG: True,
            AUTO_SITE: cle,
            AUTO_ACTIVITY: item["IDactivite"],
            AUTO_GROUP: item["IDgroupe"],
        }
        DB.ReqInsert("modeles_commandes_colonnes", [
            ("IDmodele", IDmodele),
            ("ordre", prochain_ordre),
            ("nom", item["nom"]),
            ("largeur", 100),
            ("categorie", "numerique_avec_suggestion"),
            ("parametres", str(params)),
        ])
        prochain_ordre += 1
        modifie = True

    DB.Close()
    return modifie


class CTRL(CTRL_Commande_repas_legacy.CTRL):
    """Contrôle repas historique avec découverte automatique en dernier recours."""

    def Importation(self):
        AssureColonnesAutomatiques(self.IDmodele, self.date_debut, self.date_fin)
        donnees = super(CTRL, self).Importation()

        # Le moteur historique compte une ligne de consommation comme une unité.
        # Certaines bases utilisent pourtant consommations.quantite. Corrige les
        # suggestions uniquement lorsque quantite est réellement > 1, afin de
        # conserver strictement le comportement historique dans les autres cas.
        if not donnees or not donnees.get("dict_conso"):
            return donnees
        DB = GestionDB.DB()
        req = """SELECT date, IDgroupe, IDunite, quantite
        FROM consommations
        WHERE date>='%s' AND date<='%s'
        AND consommations.etat IN ('reservation', 'present')
        AND quantite IS NOT NULL AND quantite>1;""" % (self.date_debut, self.date_fin)
        DB.ExecuterReq(req)
        lignes = DB.ResultatReq()
        DB.Close()
        for date, IDgroupe, IDunite, quantite in lignes:
            date = UTILS_Dates.DateEngEnDateDD(date)
            try:
                donnees["dict_conso"][date][IDgroupe][IDunite] += int(quantite) - 1
            except (KeyError, TypeError, ValueError):
                pass
        return donnees
