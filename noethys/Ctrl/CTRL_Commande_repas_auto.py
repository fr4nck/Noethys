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
    consommations.IDgroupe, consommations.IDunite
    FROM consommations
    LEFT JOIN unites ON unites.IDunite = consommations.IDunite
    LEFT JOIN activites ON activites.IDactivite = consommations.IDactivite
    WHERE consommations.date>='%s' AND consommations.date<='%s'
    AND consommations.etat IN ('reservation', 'present')
    AND %s
    GROUP BY consommations.IDactivite, activites.nom, consommations.IDgroupe, consommations.IDunite
    ORDER BY activites.nom, consommations.IDgroupe, consommations.IDunite;""" % (
        date_debut, date_fin, _ConditionRepas(strict=strict))
    DB.ExecuterReq(req)
    donnees = DB.ResultatReq()
    DB.Close()
    return donnees


def RechercheReservationsRepas(date_debut, date_fin):
    """Retourne les couples groupe/unité de repas regroupés par activité.

    L'activité sert ici de regroupement administratif, pas de notion de site
    physique. Le drapeau unites.repas est la référence ; le nom de l'unité
    n'est utilisé qu'en repli pour les anciennes bases incomplètement réglées.
    """
    donnees = _RechercheReservations(date_debut, date_fin, strict=True)
    if not donnees:
        donnees = _RechercheReservations(date_debut, date_fin, strict=False)

    sites = {}
    ordre = []
    for IDactivite, nom_activite, IDgroupe, IDunite in donnees:
        if IDactivite is None or IDunite is None:
            continue
        if IDactivite not in sites:
            sites[IDactivite] = {
                "IDactivite": IDactivite,
                "nom": nom_activite or "Repas",
                "unites": [],
            }
            ordre.append(IDactivite)
        couple = (IDgroupe, IDunite)
        if couple not in sites[IDactivite]["unites"]:
            sites[IDactivite]["unites"].append(couple)

    return [sites[IDactivite] for IDactivite in ordre]


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

    Une configuration historique explicite (au moins une colonne avec des
    unités sélectionnées manuellement) n'est jamais modifiée.
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

    sites = RechercheReservationsRepas(date_debut, date_fin)
    if not sites:
        DB.Close()
        return False

    modifie = False
    prochain_ordre = ordre_max + 1
    for site in sites:
        IDsite = site["IDactivite"]
        unites = site["unites"]
        if not unites:
            continue
        if IDsite in colonnes_auto:
            colonne = colonnes_auto[IDsite]
            params = colonne["parametres"]
            anciennes_unites = [tuple(item) for item in params.get("unites", [])]
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
            "unites": [tuple(item) for item in unites],
            AUTO_FLAG: True,
            AUTO_SITE: IDsite,
        }
        DB.ReqInsert("modeles_commandes_colonnes", [
            ("IDmodele", IDmodele),
            ("ordre", prochain_ordre),
            ("nom", site["nom"]),
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
