#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Expose la file de revue des candidats ``branch_assignment_gap``.

Le scanner de base réduit déjà les faux positifs qui peuvent être prouvés par le
contrôle de flot : branches exhaustives, chemins terminants, ``try/finally``,
``with`` et portées de compréhension Python 3.

Cette seconde étape ne baisse volontairement aucune priorité par heuristique.
Une occurrence ne peut sortir de ``high/review`` que via une qualification
explicite, étroite et documentée dans ``EXPLICIT_SAFE``. La clé ne contient pas
de numéro de ligne afin de résister aux déplacements de code, mais elle doit
correspondre à exactement un candidat brut et à l’empreinte AST complète de
la fonction qui porte son invariant ; une entrée absente, modifiée ou ambiguë est
signalée et couverte par les tests du dépôt.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import tokenize
from collections import Counter
from pathlib import Path

try:
    from scripts import audit_branch_assignment_gaps as base
except ModuleNotFoundError:
    import audit_branch_assignment_gaps as base

ROOT = base.NOETHYS


# Qualifications humaines explicites. Elles ne constituent pas une heuristique :
# chaque entrée doit être justifiée par un invariant de contrôle de flot précis
# et rester unique dans l'inventaire brut.
EXPLICIT_SAFE = {
    ('Dlg/DLG_Saisie_portail_demande.py', 'MAJ_informations', 'dict_periodes', 'body_only', '4779e9182f1002ee9ab536bdb9303391e030d4d4c723a43ff3b9c4ed973090f9'): (
        "la lecture n'est atteinte qu'en itérant des paiements de type période ; ce même ensemble non vide initialise dict_periodes juste avant"
    ),
    ('Dlg/DLG_Saisie_portail_demande.py', 'MAJ_informations', 'dict_factures', 'body_only', '914b011143627234ee14abea5738586b025fa49093f2b5f01cf45ace88ab46fc'): (
        "la lecture n'est atteinte qu'en itérant des paiements de type facture ; ce même ensemble non vide initialise dict_factures juste avant"
    ),
    ('Dlg/DLG_Saisie_portail_demande.py', 'Traitement_recus', 'reponse', 'body_only', '1a357b505a94693ac30e93cca69189fae6a478a1adc9b1139b6e46a5f2ba2ab0'): (
        "les chemins continuants sont couverts par methode_envoi != 'email' ou methode_envoi == 'email' ; chacun définit reponse avant le retour"
    ),
    ('Dlg/DLG_Saisie_portail_demande.py', 'Traitement_factures', 'reponse', 'body_only', '4d35390aa5af82e149c8e869939032d3ffefaf86b1598f61f7a3d743bdc983e0'): (
        "les chemins continuants sont couverts par methode_envoi != 'email' ou methode_envoi == 'email' ; chacun définit reponse avant le retour"
    ),
    ('Dlg/DLG_Ouvertures.py', 'Sauvegarde', 'prochainIDligne', 'body_only', 'be2a517abf7c8b4245b285e27a22a3a5d5022c13421bd3d4ff842cffd8bc5ae2'): (
        "prochainIDligne est initialisé lorsque DB.isNetwork est faux et sa lecture pour attribuer un IDligne est protégée par le même garde ; en mode réseau cette lecture n'est jamais atteinte"
    ),
    ('Dlg/DLG_Ouvertures.py', 'TraitementLot', 'etat', 'partial_branches', 'c0d13e7cc9b6a33b2c3404ce03b99235d6b8e8b2dbc577b51e653dcddc1551f9'): (
        "le bloc extérieur limite action à date, schema ou reinit ; date/schema affectent etat ou passent par l'except qui le replie à False, tandis que reinit passe par le else qui l'affecte aussi"
    ),
    ('Dlg/DLG_Ouvertures.py', 'TraitementLot', 'liste_temp', 'body_only', 'c0913bd34f86edcdd512abb5180f11a4d5277f0efe0c600d39cd3eba485fa64c'): (
        "la boucle sur liste_temp n'est atteinte que sous action date/schema ; chacun de ces deux chemins l'affecte dans le try et toute erreur quitte directement ce try vers l'except sans exécuter la boucle"
    ),
    ('Dlg/DLG_Ouvertures.py', 'TraitementLot', 'nbrePlaces', 'partial_branches', 'c3c4355421b4b54d0daa627449f414c23ad2d33240c8ae5e1c2c7957976a2fe9'): (
        "le bloc extérieur limite action à date, schema ou reinit ; date/schema affectent nbrePlaces ou passent par l'except qui le replie à 0, tandis que reinit passe par le else qui l'affecte à 0"
    ),
    ('Utils/UTILS_Cotisations_manquantes.py', 'GetListeCotisationsManquantes', 'date_fin', 'body_only', '52833ac4673ab36cac3451e073e6f972df167f8e77634102bb530990f98fa4d0'): (
        'la lecture de date_fin est dans le bloc gardé par A or B ; chacun des deux termes vrais affecte date_fin avant son utilisation'
    ),
    ('Utils/UTILS_Cryptage_fichier.py', 'DecrypterFichier', 'dec', 'partial_branches', 'c4ec08d2c16ced4dc3e072a66f32cdd872014748db4af9851753658dd310fe3e'): (
        'le format SV2 affecte dec dans la première branche et tout autre contenu passe par le else qui affecte dec après le chargement compatible Python 2/3'
    ),
    ('Utils/UTILS_Export_nomade.py', 'Run', 'dlgAttente', 'body_only', '0c366c92222727bc372dfac57ab219a3967d2725a9dac613a0366037bfdf1803'): (
        "dlgAttente n'est créé que si afficherDlgAttente est vrai et ses deux suppressions, en succès comme en exception, sont protégées par exactement le même garde"
    ),
    ('Utils/UTILS_Icalendar.py', '__init__', 'fichier', 'body_only', '4b3769dbe504b542a423a645cca1c8f940c592643482fcfee26964d061102c06'): (
        "fichier est lu uniquement dans le try englobant ; toute absence d'affectation ou erreur d'ouverture est capturée par l'except qui replie explicitement self.cal à None"
    ),
    ('Utils/UTILS_Impression_inscription.py', '__init__', 'paraStyleIntro', 'body_only', '3ed758b70f477a71a17f646ccb62f5f44c946ffba4702e5ca1a03a18ec89d6b5'): (
        'la lecture est sous le garde intro présent/non nul, qui implique nécessairement le premier terme du garde OR ayant créé paraStyleIntro juste avant'
    ),
    ('Utils/UTILS_Html2text.py', 'handle_tag', 'tag_style', 'body_only', '92dfcabc32019e8f2e8b08967afb57e88854c05f0a37329675fe74b201dcf8ce'): (
        "tag_style n'est lu que sous options.google_doc ; dans ce même bloc start l'affecte via element_style et le else l'affecte via le pop de tag_stack"
    ),
    ('Utils/UTILS_Html2text.py', 'handle_tag', 'parent_style', 'body_only', '9cbe4485113ef2f67dad45e6ecac66f2666c8a3a05e5e0622644ddc46fa523f3'): (
        "parent_style est initialisé à un dictionnaire vide dès l'entrée dans options.google_doc et toutes ses lectures ultérieures restent sous ce même garde"
    ),
    ('Utils/UTILS_Titulaires.py', 'GetTitulaires', 'nomsTitulaires', 'body_only', 'cd35c15e3510275978436eb40410f2403477fb4306c3dfd6db9330ae75be0084'): (
        "la lecture de nomsTitulaires est sous nbreTitulaires > 0 ; les cas 1, 2 et > 2, exhaustifs pour tout entier strictement positif, l'affectent auparavant"
    ),
    ('Dlg/DLG_Compte_internet.py', 'Importation', 'req', 'body_only', '8ef75e142a48792080feb6b65fe80cc44b1a56f5475a93eacf874b789364b419'): (
        'le retour initial exclut le seul cas où IDfamille et IDutilisateur sont tous deux nuls ; sur tout chemin continuant, au moins un des deux if suivants affecte req avant son exécution'
    ),
    ('Dlg/DLG_Saisie_lot_deductions.py', 'OnBoutonOk', 'montant', 'body_only', 'eab650102180c8b03a02c292191e12284307cf211ebcd4051d6c574c877444d6'): (
        "montant est affecté dans la branche qui fixe typeValeur à 'montant' et sa lecture ultérieure est gardée par exactement cette valeur de typeValeur"
    ),
    ('Dlg/DLG_Saisie_lot_deductions.py', 'OnBoutonOk', 'pourcent', 'else_only', '206f4f879ed45020225fe1bcbbcad100e089c7844b2e797aef70d31ef8810ea7'): (
        "pourcent est affecté dans le else qui fixe typeValeur à 'pourcent' et sa lecture ultérieure est gardée par exactement cette valeur de typeValeur"
    ),
    ('Dlg/DLG_Saisie_lot_deductions.py', 'OnBoutonOk', 'montantDeduction', 'body_only', '454c1378e63735132f7a506b88e0605cd7a59a6a87ed70267bf441d30bdbc7da'): (
        "l'if/else initial fixe toujours typeValeur à 'montant' ou 'pourcent' ; les deux gardes correspondants affectent donc montantDeduction avant sa première lecture"
    ),
    ('Dlg/DLG_Saisie_produit.py', 'OnBoutonOk', 'prochainIDligne', 'body_only', 'c5617cf6777451edb437c0626035e0717d96d3b98ff1ffc9ef8e4ef37a951dee'): (
        'prochainIDligne est initialisé lorsque DB.isNetwork est faux et toutes ses lectures/incréments restent sous le même garde DB.isNetwork == False'
    ),
    ('Utils/UTILS_Sauvegarde.py', 'Sauvegarde', 'fichierDest', 'body_only', '99d5dac98f4e3f5c63a3eecab3a5c6c64dbcaafb3b9101ad87323a3aba322044'): (
        "fichierDest est créé sous repertoire != None et sa seule lecture ultérieure reste protégée par exactement le même garde"
    ),
    ('Utils/UTILS_Sauvegarde.py', 'Sauvegarde', 'dictAdresse', 'body_only', '7bad752c10292daba9b617a1ee491bd3615f296533ef7fe9af66593ae8c830e5'): (
        "dictAdresse est créé sous listeEmails != None ; l'absence d'adresse quitte la fonction et sa lecture ultérieure reste sous exactement le même garde"
    ),
    ('Dlg/DLG_Conversion_etat.py', 'GetDonnees', 'option_lignes', 'body_only', '3f4e12d4bbddaa5622c402f57190e4b516d1a75dcdf1ec5cb0ade3262aa5fe98'): (
        "les deux contrôles appartiennent au même groupe wx.RadioButton (RB_GROUP sur le premier) ; le premier est sélectionné par défaut et l'initialisation restaure explicitement l'une des deux valeurs, donc GetDonnees rencontre toujours un choix actif avant de lire option_lignes"
    ),
    ('Dlg/DLG_Recopiage_conso.py', 'GetDonnees', 'option_lignes', 'body_only', '6a08b6aab02ca8987b4de02a7971e297230281a2399c42fb450f2e761140c71b'): (
        "les deux contrôles appartiennent au même groupe wx.RadioButton (RB_GROUP sur le premier) ; le premier est sélectionné par défaut et l'initialisation restaure explicitement l'une des deux valeurs, donc GetDonnees rencontre toujours un choix actif avant de lire option_lignes"
    ),
    ('Dlg/DLG_Saisie_portail_periode.py', 'OnBoutonOk', 'affichage', 'body_only', '52ac485d1f64da32d9e253f6179ae32909bd671beef50cca0b96db1ef9a7aa44'): (
        "radio_oui ouvre un groupe wx.RadioButton et radio_dates/radio_non appartiennent au même groupe ; wx conserve exactement un membre actif, le premier est sélectionné par défaut et Importation positionne explicitement l'un des trois états, donc OnBoutonOk affecte toujours affichage avant son enregistrement"
    ),
    ('Dlg/DLG_Activite_portail.py', 'Sauvegarde', 'portail_inscriptions_affichage', 'body_only', 'fa33b4b2ab34dbf9feaf6ca02f71bbef1ca54fb0e83d55a80d740314a8d17314'): (
        "radio_inscriptions_non ouvre un groupe wx.RadioButton et les variantes oui/dates appartiennent au même groupe ; un membre est actif par défaut et Importation restaure explicitement l'un des trois états, donc Sauvegarde affecte toujours portail_inscriptions_affichage avant son utilisation"
    ),
    ('Dlg/DLG_Activite_portail.py', 'Sauvegarde', 'portail_reservations_affichage', 'body_only', 'bd4a9365546bf46fa47623bbac514e590441890210824dd17c47d5fc1e3c2cac'): (
        "radio_reservations_non ouvre un groupe wx.RadioButton avec radio_reservations_oui ; un membre est actif par défaut et Importation restaure explicitement l'état, donc Sauvegarde affecte toujours portail_reservations_affichage avant son utilisation"
    ),
    ('Dlg/DLG_Liste_deductions.py', 'GetActivites', 'listeActivites', 'body_only', '649580e66da7f0c4c8018ae65fac9b7187ff41809897f65b3de07aa0e0d3d455'): (
        "les trois choix d'activité forment un unique groupe wx.RadioButton ouvert par wx.RB_GROUP ; un membre est donc actif avant le retour de listeActivites"
    ),
    ('Dlg/DLG_Synthese_modes_reglements.py', 'GetActivites', 'listeActivites', 'body_only', '649580e66da7f0c4c8018ae65fac9b7187ff41809897f65b3de07aa0e0d3d455'): (
        "les trois choix d'activité forment un unique groupe wx.RadioButton ouvert par wx.RB_GROUP ; un membre est donc actif avant le retour de listeActivites"
    ),
    ('Dlg/DLG_Badgeage_saisie_procedure.py', 'Sauvegarde', 'systeme', 'body_only', 'f2e917298b08945fd006a54fed261a38ee71ea28fbe69bc55b4280306e713727'): (
        "les trois systèmes d'identification appartiennent au même groupe wx.RadioButton ouvert par radio_barre avec wx.RB_GROUP ; un système est donc sélectionné avant la construction de listeDonnees"
    ),
    ('Dlg/DLG_Saisie_utilisateur.py', 'Sauvegarde', 'profil', 'body_only', 'bbc4d9d71862225ad4299bed30b3f5d2f00d67945b5632c7251f48e64c63a6e3'): (
        'les trois profils de droits appartiennent au même groupe wx.RadioButton ouvert par radio_droits_admin avec wx.RB_GROUP ; un profil est donc sélectionné avant la sauvegarde'
    ),
    ('Dlg/DLG_Saisie_utilisateur_reseau.py', 'RechercheAutorisation', 'hote', 'body_only', '499543fa04fb742efa9d4adbb83f777db921f37517e97a0b38fc4ffc74df82d4'): (
        "les trois hôtes appartiennent au même groupe wx.RadioButton ouvert par radio_1 avec wx.RB_GROUP et le constructeur restaure explicitement l'un d'eux ; hote est donc affecté avant la requête"
    ),
    ('Dlg/DLG_Saisie_utilisateur_reseau.py', 'Sauvegarde', 'hote', 'body_only', 'e45faa4b945b6cbfe393bf7a0bf3b00ea76a974cf550f6a327c8aa68c0e3ac97'): (
        "les trois hôtes appartiennent au même groupe wx.RadioButton ouvert par radio_1 avec wx.RB_GROUP et le constructeur restaure explicitement l'un d'eux ; hote est donc affecté avant la requête"
    ),
    ('Dlg/DLG_Releve_prestations_saisie.py', 'GetOptions', 'dictOptions', 'body_only', '09a437989cf92599132b8a6da6e969fb26da5982ddac935aae7d301d55564a50'): (
        "les deux types de relevé appartiennent au même groupe wx.RadioButton ouvert par radio_type_prestations avec wx.RB_GROUP ; GetType retourne donc prestations ou factures et l'une des deux branches affecte dictOptions"
    ),
    ('Dlg/DLG_Releve_prestations_saisie.py', 'GetPeriode', 'parametres', 'body_only', 'e4e498bf1ad21e688ae114bed74ab2c2938c18cceb08061764d1b6902c760e4c'): (
        'les sept périodes appartiennent au même groupe wx.RadioButton ouvert par radio_tout avec wx.RB_GROUP ; un membre est donc actif et la branche correspondante affecte parametres avant le retour'
    ),
    ('Dlg/DLG_Impression_don_oeuvres.py', 'SetListeDonnees', 'nomTitulaires', 'body_only', '00f3603e1115e49c00a56d85121d852ac88660246cc1e15af30c0d039ea58258'): (
        'nbreTitulaires vient de len(listeTitulaires) ; les cas 0, 1, 2 et > 2 sont exhaustifs et affectent nomTitulaires'
    ),
    ('Dlg/DLG_Saisie_cotisation.py', 'SetListeDonnees', 'nomTitulaires', 'body_only', '24c2be783944620320109b1f00badfa42aafd2509acc980ceb8999badbec69b9'): (
        'nbreTitulaires vient de len(listeTitulaires) ; les cas 0, 1, 2 et > 2 sont exhaustifs et affectent nomTitulaires'
    ),
    ('Dlg/DLG_Saisie_cotisation.py', 'MAJ', 'nomTitulaires', 'body_only', '9421712a7bb2f16c698f77752b49ea7bfc8512740a744c362579c2c610b3f710'): (
        'nbreTitulaires vient de len(listeTitulaires) ; les cas 0, 1, 2 et > 2 sont exhaustifs et affectent nomTitulaires'
    ),
    ('Dlg/DLG_Saisie_cotisation.py', 'MAJ', 'IDcompte_payeur', 'body_only', '0bae14cfb9ce3fd17ae7eef5f7d714a9825baaee6e07cb64eb344dd1c9e60f18'): (
        "si listeTitulaires est vide IDcompte_payeur est mis à None ; sinon la boucle qui a rempli la liste l'a déjà affecté"
    ),
    ('Ol/OL_Etat_nomin_resultats.py', '__init__', 'valeur', 'partial_branches', '9cd718823faa61de4c31850db7909ec0ace156e8e319475584f68ed3e2255601'): (
        'prefixe parcourt uniquement NBRE, TEMPS et TEMPS_FACTURE ; le cas NBRE et le couple TEMPS/TEMPS_FACTURE affectent valeur avant setattr'
    ),
    ('Utils/UTILS_Sauvegarde.py', 'Sauvegarde', 'err', 'body_only', 'a7768a2427dd2bbcc182784fbfaefe6f2908d5983a1a7b6a1ef8f3b5683d09da'): (
        "err est lié par le except Exception as err externe ; le try/except interne n'a pas de cible d'exception et ne supprime pas cette liaison"
    ),
    ('Dlg/DLG_Releve_prestations_saisie.py', 'GetOptions', 'regroupement', 'partial_branches', '076091d5da5f887d72e44ead6c19551a4f24a866ae3bc47508263d60a65f76b4'): (
        "le wx.Choice contient exactement Date, Mois, Année et démarre à l'index 0 ; les index 0, 1, 2 couvrent donc le domaine lorsque le regroupement est actif"
    ),
    ('Dlg/DLG_Saisie_texte_html.py', 'Importation', 'condition', 'body_only', '09773fc59fe8f6a53f5862d9c2eb465a40e74c0e20697ef31d1bdcfd461dafa5'): (
        "le constructeur n'appelle Importation que si IDelement ou categorie est non nul ; chacun de ces gardes affecte condition avant la requête"
    ),
    ('Dlg/DLG_Stats.py', 'Imprimer', 'html', 'body_only', '887c7c1ab10848c856b90de60e7518a933e3b6bad66a8c599a817d9ea34c5d74'): (
        "Imprimer n'est relié qu'aux commandes 10, 20 et 30 ; chacune affecte html avant son utilisation"
    ),
    ('Utils/UTILS_Stats_modeles.py', 'GetHTML', 'html', 'body_only', 'ab5adc57bb82b744f682a74ae2e913119a6c854d0e1807af3366f759b0cae858'): (
        'le garde initial rejette tout mode autre que affichage/impression ; chacun des deux modes autorisés affecte html avant le retour'
    ),
    ('Dlg/DLG_Badgeage_importation.py', 'Connexion', 'scanner', 'body_only', 'c961c43ad211675335a7a6c372aa26f76751b18a04c8477201c2a421cf7a67ae'): (
        'appareil provient du wx.Choice CTRL_Choix_appareil, dont le domaine est exactement cs1504/opn-2001 ; None est rejeté avant la branche et chacune des deux valeurs crée scanner avant le retour'
    ),
    ('Dlg/DLG_Saisie_contrat_periode_auto.py', 'Generation', 'listeDates', 'body_only', 'ecf9289c9c12f3152763f341c99b14a263093b8f8151e0b7814374cc735c8071'): (
        "ctrl_periodicite est un wx.Choice à trois valeurs initialisé sur l'index 1 ; son domaine 0/1/2 est exhaustivement traité et affecte listeDates avant lecture"
    ),
    ('Dlg/DLG_Saisie_contrat_periode_auto.py', 'Generation', 'nom_auto', 'body_only', '4ea0d677dcb071f557c305a7bcbcaf3548e8e4665757c544892cfab1b1fc50e2'): (
        "la même sélection de périodicité 0/1/2, issue d'un wx.Choice à trois valeurs initialisé, affecte exhaustivement nom_auto avant son utilisation"
    ),
    ('Dlg/DLG_Saisie_lot_ouvertures2.py', 'Validation', 'expression', 'body_only', '047d8f897bb49d93846132df9f41a70c3afb196375ed6df6ef6a8cf051df70a8'): (
        'radio_ajouter, radio_supprimer_expression et radio_supprimer_tout forment un seul groupe wx ; dans la branche de suppression, les deux états possibles affectent expression avant la recherche'
    ),
    ('Dlg/DLG_Liste_envoi_email.py', 'OnBoutonOk', 'tracks', 'body_only', '9ab82f3d7367f276e62350f1259aaf7b30a211359fc042b6ef76ed4975172f6d'): (
        'les trois radios de sélection de lignes forment un groupe wx unique initialisé par radio_lignes_affichees ; chacune des trois valeurs affecte tracks avant son parcours'
    ),
    ('Dlg/DLG_Individu_coords.py', 'EnvoyerEmail', 'ctrl', 'body_only', '01508690582815411acf4bc16442087272a30c3b6c5bdf3ad505dd71616e45e1'): (
        "EnvoyerEmail n'est lié par OnEnvoiEmail qu'aux quatre identifiants 801/802/901/902 ; 801/802 sélectionnent ctrl_travail_mail et 901/902 ctrl_mail avant toute lecture"
    ),
    ('Ol/OL_Prelevements_sepa.py', 'MemoriseReglementHistorique', 'IDcategorie', 'body_only', '42e119479de7d50c9e564fc20bb61b3bc5e5fc43b7678955f8b86cbb2d41c7fb'): (
        "la méthode interne est appelée avec les modes historiques saisie/modification/suppression, son défaut est saisie, et chacun de ces trois modes affecte IDcategorie avant construction de l'action"
    ),
    ('Ol/OL_Prelevements_sepa.py', 'MemoriseReglementHistorique', 'categorie', 'body_only', '8bbc415dfdabcba25908c5170bcde6c9500349e55b9bb4c153c46f6db839c184'): (
        "la méthode interne est appelée avec les modes historiques saisie/modification/suppression, son défaut est saisie, et chacun de ces trois modes affecte categorie avant construction de l'action"
    ),
    ('Ctrl/CTRL_Grille.py', 'SetModeIndividu', 'attente', 'body_only', '70f5456a75d70afc53914fbe8d33c87be6bda0a2e9c3f7dc4f3f9862ff909a0c'): (
        "attente est créée et supprimée sous exactement le même garde modeSilencieux == False ; si le mode est silencieux, aucune lecture de la variable n'est atteinte"
    ),
    ('Ctrl/CTRL_Grille.py', 'SetModeDate', 'attente', 'body_only', 'dcce2fc03cd1af61b13c16e44070fbaa8a427798d53735418043fddc8b8ff3dc'): (
        "attente est créée et supprimée sous exactement le même garde modeSilencieux == False ; si le mode est silencieux, aucune lecture de la variable n'est atteinte"
    ),
    ('Ctrl/CTRL_Grille.py', 'Sauvegarde', 'IDcategorie', 'body_only', '93d18d8877ff7608822da94438fe472aa6871233dccba623f756b1ed60185c51'): (
        "la boucle parcourt le domaine littéral suppr/modif/ajout et chacun de ces trois codes affecte IDcategorie avant son ajout à l'historique"
    ),
    ('Ctrl/CTRL_Locations_tableau.py', 'Draw', 'hauteurTrait', 'partial_branches', 'd8a2510a4cd8d0e38467865a16a60521ba4b24af7c00ffbfc4cc2aa89dab0f14'): (
        'listeGraduations est produite par rrule avec byminute=(0, 15, 30, 45) ; les branches 0, 15/45 et 30 couvrent donc chaque valeur de minute avant le tracé'
    ),
    ('Ctrl/CTRL_Synthese_impayes.py', 'MAJ', 'niveau2', 'body_only', '1d28288079518cfbc6d43b82de7a62a3c311b9d1b9702eebad61dae403ddd913'): (
        'dans chaque itération, niveau2 est créé sous affichage_details == True et toutes ses lectures ultérieures sont protégées par ce même garde'
    ),
    ('Ctrl/CTRL_Synthese_prestations.py', 'MAJ', 'niveau2', 'body_only', 'cd37c1069d3b103f3b89dcbf3d565583c4e6765d75f3d16f3f65d3aa82f1b50b'): (
        "dans chaque itération, niveau2 est créé sous key_ligne2 != '' et toutes ses lectures ultérieures sont protégées par ce même garde"
    ),
    ('Ctrl/CTRL_Synthese_ventilation.py', 'MAJ', 'niveauPrestation', 'body_only', 'cf657a4d335fa481d47247e788a545469e352e64db8e605bbbd7af2e0ac07aad'): (
        'dans chaque itération, niveauPrestation est créé sous affichage_details == True et toutes ses lectures ultérieures sont protégées par ce même garde'
    ),

    ('Ctrl/CTRL_Informations.py', 'GetRenseignements', 'dictDonneesFamille', 'body_only', '553a2da43f84d88750fa5cb2f80464a15ef3ba297a7840808cc1c1ec880695e1'): (
        'dictDonneesFamille est créé dès que self.IDfamille est renseigné ; toutes les lectures famille signalées sont elles-mêmes gardées par self.IDfamille != None'
    ),
    ('Ctrl/CTRL_Tarification_calcul.py', 'Sauvegarde', 'DB', 'body_only', '64b232151781a42f76e5ebbb62132ce5462d24ea671a58ba1a1d6690135805c2'): (
        "DB n'existe qu'en mode sans track_tarif et chaque accès base de la méthode est protégé par ce même test self.track_tarif == None"
    ),
    ('Ctrl/CTRL_Tarification_forfait.py', 'Sauvegarde', 'options', 'body_only', '5c43f37bd39a724ca1e53df08e464bd741babaaf1d5ec0309b045b336d58f19c'): (
        'les trois boutons radio forment un groupe wx exhaustif ; chacun des trois états affecte options avant la sauvegarde'
    ),
    ('Dlg/DLG_Appliquer_forfait.py', 'Applique_forfait', 'IDgroupe', 'body_only', 'f277d576ab915af8a7ae2f65be13da20afaa2188ff62e865c7452ce0791bf34b'): (
        "IDgroupe est affecté en même temps que IDcategorie_tarif_temp ; le flot aval ne l'utilise que sous le garde IDcategorie_tarif_temp != None"
    ),
    ('Dlg/DLG_Appliquer_forfait.py', 'Applique_forfait', 'IDinscription', 'body_only', '721fdff3ed814dddb85acdb5de0dd73261b4a31c4e78610cc56c927c9f69e0ca'): (
        'IDinscription est affecté en même temps que IDcategorie_tarif_temp ; les consommations ne sont créées que dans le flot gardé par IDcategorie_tarif_temp != None'
    ),
    ('Dlg/DLG_Nbre_inscrits_2.py', 'MAJ', 'dictGroupeParActivite', 'body_only', '8b5c81c2346031249d856905667d48be2f7cd54b01752cec2beeb419b0d58c84'): (
        "dictGroupeParActivite est créé lorsque regroupement_groupe_activites == 1 et sa lecture est dans le second opérande d'un and portant exactement le même test"
    ),
    ('Ol/OL_PES_pieces.py', 'GetTracks', 'criteres', 'body_only', 'e4d0949a679a053f1a5caf53ae039116b8e72df5f022726f0c0d6c3747da065c'): (
        'si IDlot et IDmandat sont tous deux None la fonction retourne immédiatement ; sinon au moins une des deux branches affecte criteres avant la requête'
    ),
    ('Utils/UTILS_Portail_synchro.py', 'Upload_data', 'IDfamille', 'body_only', '507611e7116da5de8ffffe3e27c3b3f24bc49331d084a640056b7eeeeb7e5a84'): (
        'profil parcourt littéralement famille/utilisateur ; les deux branches affectent IDfamille avant toute lecture'
    ),
    ('Utils/UTILS_Portail_synchro.py', 'Upload_data', 'IDutilisateur', 'body_only', 'ea2ef62443e863b14b71ade08b1529287e5bc2d560f41127a0681fd7276f8386'): (
        'profil parcourt littéralement famille/utilisateur ; les deux branches affectent IDutilisateur avant la création du compte'
    ),
    ('Utils/UTILS_Portail_synchro.py', 'Upload_data', 'nomDossier', 'body_only', '6da45fa1c42a7ca448ba000d773ab5d6cb9fdd5742a4c133d63986519cde66ab'): (
        'profil parcourt littéralement famille/utilisateur et chacune des deux valeurs affecte nomDossier avant anonymisation ou création du compte'
    ),
    ('Utils/UTILS_Portail_synchro.py', 'Download_data', 'listeRefExistantes', 'body_only', '95cfbe85369db500f839937ef8cd70a610fe0c509ddf536aceed728850cce8eb'): (
        'listeRefExistantes est construite sous full_synchro == True et sa seule lecture signalée est protégée par le même garde'
    ),

    ('Ctrl/CTRL_Synthese_conso.py', 'Importation', 'regroupement', 'body_only', 'c4030bbe4160747afa4dcbbc5b40573de7db9ec3930fdb04b9280f8b47bc5039'): (
        'affichage_lignes provient du choix UI fini de DLG_Synthese_conso ; chaque code déclaré, y compris les questionnaires famille/individu, affecte regroupement et le bloc try fournit en plus un repli None'
    ),
    ('Ctrl/CTRL_Synthese_conso.py', 'Importation', 'valeur', 'body_only', 'e34ccdd2cceaa6f4acb3774495e23d5f116d851f4d8966a7959b42ddc28e82af'): (
        "affichage_valeurs provient d'un choix UI à trois valeurs quantite/temps_presence/temps_facture, toutes trois affectant valeur avant son utilisation"
    ),
    ('Ctrl/CTRL_Synthese_deductions.py', 'Importation', 'regroupement', 'body_only', '3641952e2069fbf86fb142decf6aa0843a1fed6835a2f6f259964010f4e50eb6'): (
        'affichage_regroupement provient du choix UI fini de DLG_Synthese_deductions ; chaque code déclaré et les questionnaires famille affectent regroupement, avec repli None dans le try/except'
    ),
    ('Ctrl/CTRL_Synthese_locations.py', 'Importation', 'regroupement', 'body_only', '4b46ed148e1373aba5c70629cbae2fd44f113c1c4d96f6ae3273a56574a8b7d3'): (
        'affichage_regroupement provient du choix UI fini de DLG_Synthese_locations ; chaque code déclaré et les questionnaires famille affectent regroupement, avec repli None dans le try/except'
    ),
    ('Ctrl/CTRL_Synthese_modes_reglements.py', 'Importation', 'condition', 'body_only', '4b035aa113b05943472c47c01fae9ac2ed809392622106cd5a81e0b3f3bb6ec3'): (
        'mode provient de Parametres.GetMode, lui-même adossé à un groupe radio wx exhaustif saisie/depose/nondepose ; les trois valeurs affectent condition'
    ),
    ('Ol/OL_Liste_factures_detail.py', '__init__', 'label_key', 'body_only', '844bfd458f15972c32467b0877ee092cffd3bf824e52129c2b7be00e4592f6d1'): (
        "ListView.detail est initialisé à label et l'unique sélecteur de DLG_Liste_factures_detail le borne à label ou IDactivite ; les deux branches affectent label_key"
    ),
    ('Ol/OL_Liste_factures_detail.py', 'InitObjectListView', 'label_colonne', 'body_only', 'be48c350db30c96e78cf921ec8f631013cb9f36b7bb4796eb062cc6841a97ecf'): (
        'le même domaine fini label/IDactivite gouverne le détail de facture et les deux branches affectent label_colonne avant la création de colonne'
    ),
    ('Dlg/DLG_Saisie_tarification.py', 'Sauvegarde', 'DB', 'body_only', '2b4755c2feeaa043e4ca12c5a7422c19c54b306778a931ab76471ee67f38fe48'): (
        'après la correction #347, DB est créé uniquement sous self.track_tarif == None et chaque opération base restante, suppression de filtres et fermeture comprises, est protégée par ce même mode non-track'
    ),

}

def _candidate_fingerprint(root, item):
    """Empreinte la structure AST qui justifie une qualification explicite.

    Les numéros de ligne servent uniquement à retrouver la fonction signalée par
    le scanner. Ils ne participent pas à l'empreinte. En revanche, toute évolution
    AST de cette fonction invalide la qualification, y compris un garde ou une
    boucle environnante dont dépend l'invariant humain.
    """
    path = Path(root) / item["file"]
    try:
        with tokenize.open(path) as stream:
            tree = ast.parse(stream.read(), filename=str(path))
    except (OSError, SyntaxError, UnicodeError):
        return None

    functions = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == item["function"]
    ]
    for function in functions:
        if_node = next((
            node for node in ast.walk(function)
            if isinstance(node, ast.If)
            and getattr(node, "lineno", None) == item["if_line"]
        ), None)
        if if_node is None:
            continue

        candidates = []
        for node in ast.walk(function):
            if not isinstance(node, ast.stmt):
                continue
            found = any(
                isinstance(child, ast.Name)
                and child.id == item["name"]
                and getattr(child, "lineno", None) == item["line"]
                and isinstance(child.ctx, (ast.Load, ast.Del))
                for child in ast.walk(node)
            )
            if found:
                start = getattr(node, "lineno", item["line"])
                end = getattr(node, "end_lineno", start)
                candidates.append((end - start, len(list(ast.walk(node))), node))
        if not candidates:
            continue

        event_node = min(candidates, key=lambda entry: (entry[0], entry[1]))[2]
        # Une qualification humaine peut dépendre d'un garde ou d'une boucle
        # située avant/après le ``if`` directement signalé. On empreinte donc la
        # fonction entière plutôt qu'un voisinage local : toute évolution du flot
        # qui établit l'invariant rend l'entrée explicite obsolète et la remet en
        # ``high/review`` jusqu'à nouvelle validation humaine.
        payload = "|".join((
            item["function"],
            item["name"],
            item["detail"],
            ast.dump(function, include_attributes=False),
        ))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return None


def qualification_key(item, root=ROOT):
    return (
        item["file"],
        item["function"],
        item["name"],
        item["detail"],
        _candidate_fingerprint(root, item),
    )


def build_report(root=ROOT):
    raw = base.build_report(root)
    key_counts = Counter(qualification_key(item, root) for item in raw["findings"])
    matched = set()
    findings = []

    for item in raw["findings"]:
        result = dict(item)
        key = qualification_key(item, root)
        reason = EXPLICIT_SAFE.get(key)
        if reason is not None and key_counts[key] == 1:
            result["classification"] = "explicit_safe"
            result["priority"] = "low"
            result["reason"] = reason
            matched.add(key)
        else:
            result["classification"] = "review"
            result["priority"] = "high"
            result["reason"] = (
                "candidat conservé : aucune heuristique ne masque automatiquement "
                "un risque de variable locale absente"
            )
        findings.append(result)

    unmatched = sorted(key for key in EXPLICIT_SAFE if key_counts[key] == 0)
    ambiguous = sorted(key for key in EXPLICIT_SAFE if key_counts[key] > 1)

    findings.sort(key=lambda item: (item["file"], item["line"], item["name"]))
    return {
        "count": len(findings),
        "priorities": dict(Counter(item["priority"] for item in findings)),
        "classifications": dict(Counter(item["classification"] for item in findings)),
        "explicit_safe_registry": {
            "configured": len(EXPLICIT_SAFE),
            "matched": len(matched),
            "unmatched": [list(key) for key in unmatched],
            "ambiguous": [list(key) for key in ambiguous],
        },
        "findings": findings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", default="", metavar="FILE")
    args = parser.parse_args(argv)

    report = build_report()
    print(f"BRANCH_ASSIGNMENT_QUALIFIED={report['count']} {report['priorities']} {report['classifications']}")
    for item in report["findings"]:
        label = "SAFE" if item["classification"] == "explicit_safe" else "REVIEW"
        print(f"- {label} {item['file']}:{item['line']} {item['function']} — {item['name']} ({item['detail']})")

    registry = report["explicit_safe_registry"]
    if registry["unmatched"] or registry["ambiguous"]:
        print(
            "QUALIFICATION_REGISTRY_ERROR="
            f"unmatched={len(registry['unmatched'])} ambiguous={len(registry['ambiguous'])}"
        )

    if args.json:
        output = Path(args.json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return 2 if registry["unmatched"] or registry["ambiguous"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
