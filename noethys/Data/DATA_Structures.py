#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Schéma cible pour les structures et relations métier de Noethys 1.3.5.x.

Ce module reste volontairement séparé de ``DATA_Tables.py`` tant que la
migration additive n'est pas activée sur les bases existantes. Il sert de
contrat de données testable pour Noe-062.

Principes :
- aucun champ famille/individu existant n'est modifié ;
- les identifiants administratifs restent optionnels ;
- une structure possède un identifiant interne numérique et un UID stable
  destiné aux échanges avec PMSL-Equipe / Dolibarr ;
- une structure peut avoir plusieurs contacts, catégories et groupes libres ;
- bénéficiaire et payeur sont dissociés ;
- les règles de facturation sont portées par la relation/prestation, pas par
  le type de structure.
"""

DB_STRUCTURES = {
    "structures": [
        ("IDstructure", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID local de la structure"),
        ("uid", "VARCHAR(64)", u"Identifiant stable inter-applications"),
        ("type_structure", "VARCHAR(50)", u"association, club_section, ecole, mairie_collectivite, alsh, departement_ase, financeur, autre"),
        ("nom", "VARCHAR(300)", u"Nom usuel de la structure"),
        ("nom_court", "VARCHAR(150)", u"Nom court optionnel"),
        ("nom_officiel", "VARCHAR(300)", u"Dénomination officielle optionnelle"),
        ("IDstructure_parent", "INTEGER", u"Structure parente éventuelle"),
        ("rue", "VARCHAR(255)", u"Adresse"),
        ("cp", "VARCHAR(10)", u"Code postal"),
        ("ville", "VARCHAR(100)", u"Ville"),
        ("tel", "VARCHAR(50)", u"Téléphone principal"),
        ("mail", "VARCHAR(200)", u"Adresse mail principale"),
        ("site_web", "VARCHAR(300)", u"Site internet"),
        ("rna", "VARCHAR(30)", u"RNA optionnel"),
        ("siren", "VARCHAR(20)", u"SIREN optionnel"),
        ("siret", "VARCHAR(20)", u"SIRET optionnel"),
        ("ape", "VARCHAR(20)", u"Code APE/NAF optionnel"),
        ("memo", "VARCHAR(2000)", u"Mémo"),
        ("actif", "INTEGER", u"Structure active 0/1"),
        ("date_creation", "DATE", u"Date de création de la fiche"),
        ("date_modification", "DATE", u"Date de dernière modification"),
    ],

    "structures_contacts": [
        ("IDcontact", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID du contact"),
        ("IDstructure", "INTEGER", u"Structure liée"),
        ("IDindividu", "INTEGER", u"Lien optionnel vers une fiche individu Noethys"),
        ("nom", "VARCHAR(100)", u"Nom"),
        ("prenom", "VARCHAR(100)", u"Prénom"),
        ("fonction", "VARCHAR(150)", u"Fonction libre : président, trésorier, directeur, etc."),
        ("tel", "VARCHAR(50)", u"Téléphone"),
        ("mobile", "VARCHAR(50)", u"Téléphone mobile"),
        ("mail", "VARCHAR(200)", u"Adresse mail"),
        ("contact_principal", "INTEGER", u"Contact principal 0/1"),
        ("actif", "INTEGER", u"Contact actif 0/1"),
        ("memo", "VARCHAR(1000)", u"Mémo"),
    ],

    "structures_roles_contacts": [
        ("IDrole_contact", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID du rôle"),
        ("IDcontact", "INTEGER", u"Contact concerné"),
        ("role", "VARCHAR(100)", u"administratif, facturation, convention, planning, communication, urgence, autre"),
    ],

    "structures_categories": [
        ("IDcategorie_structure", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID catégorie"),
        ("nom", "VARCHAR(150)", u"ALSH, EMS, sport-santé, couture, atelier multimédia, association sportive, école, mairie, etc."),
        ("actif", "INTEGER", u"Catégorie active 0/1"),
    ],

    "structures_categories_liens": [
        ("IDlien_categorie", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID lien"),
        ("IDstructure", "INTEGER", u"Structure concernée"),
        ("IDcategorie_structure", "INTEGER", u"Catégorie"),
    ],

    "structures_tags": [
        ("IDtag_structure", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID tag"),
        ("nom", "VARCHAR(150)", u"Tag libre : olympiades, ponctuel, mise à disposition, etc."),
        ("actif", "INTEGER", u"Tag actif 0/1"),
    ],

    "structures_tags_liens": [
        ("IDlien_tag", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID lien"),
        ("IDstructure", "INTEGER", u"Structure concernée"),
        ("IDtag_structure", "INTEGER", u"Tag"),
    ],

    "structures_groupes": [
        ("IDgroupe_structure", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID groupe libre"),
        ("IDstructure", "INTEGER", u"Structure concernée"),
        ("nom", "VARCHAR(200)", u"Section / classe / groupe libre"),
        ("actif", "INTEGER", u"Groupe actif 0/1"),
        ("memo", "VARCHAR(1000)", u"Mémo"),
    ],

    "interventions": [
        ("IDintervention", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID local de l'intervention"),
        ("uid", "VARCHAR(64)", u"Identifiant stable inter-applications"),
        ("IDstructure", "INTEGER", u"Structure bénéficiaire"),
        ("IDgroupe_structure", "INTEGER", u"Classe / groupe optionnel"),
        ("IDrelation_structure", "INTEGER", u"Relation / convention optionnelle"),
        ("nature", "VARCHAR(50)", u"Nature : sport, animation, autre"),
        ("date", "DATE", u"Date de l'intervention"),
        ("heure_debut", "VARCHAR(5)", u"Heure de début HH:MM"),
        ("heure_fin", "VARCHAR(5)", u"Heure de fin HH:MM"),
        ("duree_minutes", "INTEGER", u"Durée calculée en minutes"),
        ("libelle", "VARCHAR(300)", u"Libellé de la séance"),
        ("statut", "VARCHAR(50)", u"planifiee, realisee, annulee"),
        ("notes", "VARCHAR(2000)", u"Notes libres"),
        ("actif", "INTEGER", u"Intervention active 0/1"),
        ("date_creation", "DATE", u"Date de création"),
        ("date_modification", "DATE", u"Date de dernière modification"),
    ],

    "lieux": [
        ("IDlieu", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID local du lieu"),
        ("uid", "VARCHAR(64)", u"Identifiant stable inter-applications du lieu"),
        ("nom", "VARCHAR(300)", u"Nom usuel du lieu"),
        ("type_lieu", "VARCHAR(50)", u"gymnase, terrain, ecole, salle, piscine, siege, autre"),
        ("rue", "VARCHAR(255)", u"Adresse"),
        ("complement", "VARCHAR(255)", u"Complément d'adresse"),
        ("cp", "VARCHAR(10)", u"Code postal"),
        ("ville", "VARCHAR(100)", u"Ville"),
        ("latitude", "FLOAT", u"Latitude optionnelle"),
        ("longitude", "FLOAT", u"Longitude optionnelle"),
        ("IDstructure_gestionnaire", "INTEGER", u"Structure gestionnaire éventuelle"),
        ("informations_acces", "VARCHAR(1000)", u"Accès, clés, portail, consignes"),
        ("notes", "VARCHAR(2000)", u"Notes libres"),
        ("actif", "INTEGER", u"Lieu actif 0/1"),
        ("date_creation", "DATE", u"Date de création"),
        ("date_modification", "DATE", u"Date de dernière modification"),
    ],

    "interventions_execution": [
        ("IDexecution_intervention", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID de l'extension opérationnelle"),
        ("IDintervention", "INTEGER UNIQUE", u"Séance canonique concernée ; une seule extension par séance"),
        ("UIDintervenant_habituel", "VARCHAR(100)", u"UID RH stable de l'intervenant habituel"),
        ("UIDintervenant_prevu", "VARCHAR(100)", u"UID RH stable de l'intervenant prévu"),
        ("UIDintervenant_reel", "VARCHAR(100)", u"UID RH stable de l'intervenant ayant réellement assuré la séance"),
        ("IDlieu_prevu", "INTEGER", u"Lieu prévu"),
        ("IDlieu_reel", "INTEGER", u"Lieu réellement utilisé"),
        ("heure_debut_reelle", "VARCHAR(5)", u"Heure de début réellement constatée HH:MM"),
        ("heure_fin_reelle", "VARCHAR(5)", u"Heure de fin réellement constatée HH:MM"),
        ("duree_reelle_minutes", "INTEGER", u"Durée réelle calculée"),
        ("commentaire_realise", "VARCHAR(2000)", u"Commentaire terrain sur le réalisé"),
        ("date_modification", "DATE", u"Date de dernière modification de l'exécution"),
    ],

    "structures_relations": [
        ("IDrelation_structure", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID relation/prestation"),
        ("IDstructure", "INTEGER", u"Structure contractante ou bénéficiaire"),
        ("IDgroupe_structure", "INTEGER", u"Section/classe/groupe optionnel"),
        ("IDactivite", "INTEGER", u"Activité Noethys optionnelle"),
        ("type_relation", "VARCHAR(100)", u"mise_disposition, prestation, adhesion, eps, autre"),
        ("fonction_intervenant", "VARCHAR(100)", u"animateur, directeur, educateur_sportif, autre"),
        ("IDintervenant_externe", "VARCHAR(100)", u"Identifiant PMSL-Equipe ou autre source"),
        ("nom_intervenant", "VARCHAR(200)", u"Nom d'affichage de l'intervenant"),
        ("date_debut", "DATE", u"Début de la relation"),
        ("date_fin", "DATE", u"Fin de la relation"),
        ("tarif", "FLOAT", u"Tarif de référence"),
        ("unite_tarif", "VARCHAR(50)", u"heure, jour, forfait, séance, autre"),
        ("mode_facturation", "VARCHAR(100)", u"mensuel, trimestriel, apres_validation, manuel, autre"),
        ("jour_facturation", "INTEGER", u"Jour indicatif du mois si applicable"),
        ("actif", "INTEGER", u"Relation active 0/1"),
        ("memo", "VARCHAR(2000)", u"Mémo"),
    ],

    "structures_payeurs": [
        ("IDpayeur_structure", "INTEGER PRIMARY KEY AUTOINCREMENT", u"ID payeur"),
        ("IDrelation_structure", "INTEGER", u"Relation concernée"),
        ("type_payeur", "VARCHAR(50)", u"famille, structure, departement_ase, autre"),
        ("IDfamille", "INTEGER", u"Famille payeuse optionnelle"),
        ("IDstructure_payeur", "INTEGER", u"Structure payeuse optionnelle"),
        ("libelle_payeur", "VARCHAR(300)", u"Libellé libre si nécessaire"),
        ("taux_prise_en_charge", "FLOAT", u"Taux de prise en charge optionnel"),
        ("montant_plafond", "FLOAT", u"Plafond optionnel"),
        ("date_debut", "DATE", u"Début de prise en charge"),
        ("date_fin", "DATE", u"Fin de prise en charge"),
        ("reference", "VARCHAR(200)", u"Référence de prise en charge / convention"),
    ],
}


def GetNomsTables():
    """Retourne les tables du module dans un ordre stable pour les tests/migrations."""
    return tuple(DB_STRUCTURES.keys())


def GetChamps(nom_table):
    """Retourne les noms de champs déclarés pour une table du module."""
    return tuple(champ[0] for champ in DB_STRUCTURES[nom_table])