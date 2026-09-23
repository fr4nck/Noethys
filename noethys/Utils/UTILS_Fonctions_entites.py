#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fonctions et usages des individus dans les entités.

Le modèle historique `rattachements` (Représentant/Enfant/Contact) reste
inchangé. Noethys SL ajoute une table additive 1:1 qui porte uniquement
les informations métier de la relation individu <-> famille/entité :
fonction et usages documentaires/administratifs.

Cette séparation est volontaire :
- une même personne peut être Présidente d'une association et Trésorière
  d'une autre ;
- les ID locaux restent des ID de la base courante, ce qui permettra à
  un futur outil de fusion ALSH/MAD/Mairies de conserver une table de
  correspondance source -> cible sans supposer qu'un ID est global ;
- une ancienne version de Noethys peut ignorer entièrement cette table.
"""

from __future__ import annotations

from Data import DATA_Civilites
from Data import DATA_Fonctions_entites
from Data import DATA_Tables


NOM_TABLE = "rattachements_fonctions"
USAGES = ("representant", "signataire", "facturation", "planning")


def _bool_int(valeur):
    return 1 if valeur in (True, 1, "1") else 0


def _fermer_si_besoin(DB, fermer):
    if fermer:
        DB.Close()


def AssurerTable(DB=None):
    """Crée la table additive si elle n'existe pas encore.

    Cette fonction n'est appelée que lors d'une écriture explicite de la
    fonctionnalité (édition d'une fonction dans l'entité), jamais par les
    simples lectures. Elle évite de modifier la table historique
    `rattachements` et ne nécessite aucun changement d'ID existant.
    """
    fermer = DB is None
    if DB is None:
        import GestionDB
        DB = GestionDB.DB()
    creee = False
    try:
        if not DB.IsTableExists(NOM_TABLE):
            DB.CreationTable(NOM_TABLE, DATA_Tables.DB_DATA)
            DB.Commit()
            creee = True
    finally:
        _fermer_si_besoin(DB, fermer)
    return creee


def TableDisponible(DB=None):
    fermer = DB is None
    if DB is None:
        import GestionDB
        DB = GestionDB.DB()
    try:
        return DB.IsTableExists(NOM_TABLE)
    finally:
        _fermer_si_besoin(DB, fermer)


def GetTypeEntiteFamille(IDfamille, DB=None):
    """Déduit le type d'entité depuis la civilité institutionnelle
    rattachée à la famille. Renvoie None pour une famille classique."""
    fermer = DB is None
    if DB is None:
        import GestionDB
        DB = GestionDB.DB()
    try:
        DB.ExecuterReq(
            """SELECT individus.IDcivilite, rattachements.titulaire,
            rattachements.IDcategorie, rattachements.IDrattachement
            FROM rattachements
            LEFT JOIN individus ON individus.IDindividu = rattachements.IDindividu
            WHERE rattachements.IDfamille=%d
            ORDER BY rattachements.titulaire DESC,
                     rattachements.IDcategorie ASC,
                     rattachements.IDrattachement ASC;""" % int(IDfamille)
        )
        for IDcivilite, _titulaire, _categorie, _IDrattachement in DB.ResultatReq():
            type_entite = DATA_Fonctions_entites.GetTypeDepuisCivilite(IDcivilite)
            if type_entite:
                return type_entite
        return None
    finally:
        _fermer_si_besoin(DB, fermer)


def GetSuggestionsFonctions(IDfamille, sexe=None, DB=None):
    return DATA_Fonctions_entites.GetFonctions(
        type_entite=GetTypeEntiteFamille(IDfamille, DB=DB),
        sexe=sexe,
    )


def GetFonctionRattachement(IDrattachement, DB=None):
    """Retourne le paramétrage d'un rattachement, sans créer de table."""
    valeur_vide = {
        "IDfonction_rattachement": None,
        "IDrattachement": IDrattachement,
        "fonction": u"",
        "representant": 0,
        "signataire": 0,
        "facturation": 0,
        "planning": 0,
        "defaut": 0,
    }
    fermer = DB is None
    if DB is None:
        import GestionDB
        DB = GestionDB.DB()
    try:
        if not DB.IsTableExists(NOM_TABLE):
            return valeur_vide
        DB.ExecuterReq(
            """SELECT IDfonction_rattachement, IDrattachement, fonction,
            representant, signataire, facturation, planning, defaut
            FROM rattachements_fonctions
            WHERE IDrattachement=%d
            ORDER BY IDfonction_rattachement;""" % int(IDrattachement)
        )
        lignes = DB.ResultatReq()
        if not lignes:
            return valeur_vide
        ligne = lignes[0]
        return {
            "IDfonction_rattachement": ligne[0],
            "IDrattachement": ligne[1],
            "fonction": ligne[2] or u"",
            "representant": _bool_int(ligne[3]),
            "signataire": _bool_int(ligne[4]),
            "facturation": _bool_int(ligne[5]),
            "planning": _bool_int(ligne[6]),
            "defaut": _bool_int(ligne[7]),
        }
    finally:
        _fermer_si_besoin(DB, fermer)


def EnregistrerFonctionRattachement(
    IDrattachement, fonction=u"", representant=False, signataire=False,
    facturation=False, planning=False, defaut=False, DB=None,
):
    """Insère ou met à jour la métadonnée métier d'un rattachement.

    Une ligne entièrement vide est supprimée. Si une ancienne anomalie a
    créé plusieurs lignes pour le même rattachement, la première est
    conservée et les doublons sont nettoyés lors de cette écriture.
    """
    fermer = DB is None
    if DB is None:
        import GestionDB
        DB = GestionDB.DB()
    try:
        if not DB.IsTableExists(NOM_TABLE):
            DB.CreationTable(NOM_TABLE, DATA_Tables.DB_DATA)
            DB.Commit()

        fonction = (fonction or u"").strip()
        valeurs = [
            ("fonction", fonction),
            ("representant", _bool_int(representant)),
            ("signataire", _bool_int(signataire)),
            ("facturation", _bool_int(facturation)),
            ("planning", _bool_int(planning)),
            ("defaut", _bool_int(defaut)),
        ]

        DB.ExecuterReq(
            """SELECT IDfonction_rattachement
            FROM rattachements_fonctions
            WHERE IDrattachement=%d
            ORDER BY IDfonction_rattachement;""" % int(IDrattachement)
        )
        ids = [ligne[0] for ligne in DB.ResultatReq()]

        vide = not fonction and not any(v for _k, v in valeurs[1:])
        if vide:
            for IDligne in ids:
                DB.ReqDEL(NOM_TABLE, "IDfonction_rattachement", IDligne, commit=False)
            DB.Commit()
            return None

        if ids:
            IDligne = ids[0]
            DB.ReqMAJ(NOM_TABLE, valeurs, "IDfonction_rattachement", IDligne, commit=False)
            for doublon in ids[1:]:
                DB.ReqDEL(NOM_TABLE, "IDfonction_rattachement", doublon, commit=False)
            DB.Commit()
            return IDligne

        return DB.ReqInsert(
            NOM_TABLE,
            [("IDrattachement", int(IDrattachement))] + valeurs,
            commit=True,
        )
    finally:
        _fermer_si_besoin(DB, fermer)


def _nom_complet(IDcivilite, nom, prenom):
    nom = (nom or u"").strip()
    prenom = (prenom or u"").strip()
    if not prenom:
        return nom
    abrege = u""
    try:
        abrege = DATA_Civilites.GetDictCivilites()[IDcivilite]["civiliteAbrege"] or u""
    except Exception:
        pass
    return u" ".join(x for x in (abrege, nom, prenom) if x).strip()


def GetContactsFamille(IDfamille, usage=None, DB=None):
    """Retourne les personnes dont le rattachement porte une fonction.

    usage peut valoir representant/signataire/facturation/planning. Le
    filtre est appliqué en Python, donc aucun nom de colonne issu de
    l'appelant n'est injecté dans la requête SQL.
    """
    if usage is not None and usage not in USAGES:
        raise ValueError("Usage inconnu : %s" % usage)

    fermer = DB is None
    if DB is None:
        import GestionDB
        DB = GestionDB.DB()
    try:
        if not DB.IsTableExists(NOM_TABLE):
            return []
        DB.ExecuterReq(
            """SELECT
                rattachements_fonctions.IDfonction_rattachement,
                rattachements.IDrattachement,
                rattachements.IDindividu,
                rattachements.IDcategorie,
                rattachements.titulaire,
                individus.IDcivilite,
                individus.nom,
                individus.prenom,
                individus.mail,
                individus.travail_mail,
                individus.tel_domicile,
                individus.tel_mobile,
                individus.travail_tel,
                rattachements_fonctions.fonction,
                rattachements_fonctions.representant,
                rattachements_fonctions.signataire,
                rattachements_fonctions.facturation,
                rattachements_fonctions.planning,
                rattachements_fonctions.defaut
            FROM rattachements_fonctions
            INNER JOIN rattachements
                ON rattachements.IDrattachement = rattachements_fonctions.IDrattachement
            LEFT JOIN individus
                ON individus.IDindividu = rattachements.IDindividu
            WHERE rattachements.IDfamille=%d
            ORDER BY rattachements_fonctions.defaut DESC,
                     rattachements.IDrattachement ASC,
                     rattachements_fonctions.IDfonction_rattachement ASC;""" % int(IDfamille)
        )
        resultat = []
        vus = set()
        for ligne in DB.ResultatReq():
            (
                IDfonction, IDrattachement, IDindividu, IDcategorie, titulaire,
                IDcivilite, nom, prenom, mail, travail_mail, tel_domicile,
                tel_mobile, travail_tel, fonction, representant, signataire,
                facturation, planning, defaut,
            ) = ligne
            if IDrattachement in vus:
                continue
            vus.add(IDrattachement)
            item = {
                "IDfonction_rattachement": IDfonction,
                "IDrattachement": IDrattachement,
                "IDindividu": IDindividu,
                "IDcategorie": IDcategorie,
                "titulaire": _bool_int(titulaire),
                "IDcivilite": IDcivilite,
                "nom": (nom or u"").strip(),
                "prenom": (prenom or u"").strip(),
                "nom_complet": _nom_complet(IDcivilite, nom, prenom),
                "fonction": (fonction or u"").strip(),
                "representant": _bool_int(representant),
                "signataire": _bool_int(signataire),
                "facturation": _bool_int(facturation),
                "planning": _bool_int(planning),
                "defaut": _bool_int(defaut),
                "mail": (travail_mail or mail or u"").strip(),
                "telephone": (travail_tel or tel_mobile or tel_domicile or u"").strip(),
            }
            if usage is None or item[usage]:
                resultat.append(item)
        return resultat
    finally:
        _fermer_si_besoin(DB, fermer)


def ChoisirContact(IDfamille, usage, DB=None, fallback_usage=None):
    """Choisit un contact déterministe : contact marqué par défaut puis
    premier rattachement. Un fallback peut être demandé explicitement."""
    candidats = GetContactsFamille(IDfamille, usage=usage, DB=DB)
    if not candidats and fallback_usage:
        candidats = GetContactsFamille(IDfamille, usage=fallback_usage, DB=DB)
    if not candidats:
        return None
    return candidats[0]


def GetRepresentantConvention(IDfamille, DB=None):
    # Un signataire explicite est prioritaire. À défaut, un représentant
    # explicite est utilisable pour le préremplissage de la convention.
    return ChoisirContact(
        IDfamille, usage="signataire", DB=DB, fallback_usage="representant"
    )


def GetReferentFacturation(IDfamille, DB=None):
    return ChoisirContact(IDfamille, usage="facturation", DB=DB)
