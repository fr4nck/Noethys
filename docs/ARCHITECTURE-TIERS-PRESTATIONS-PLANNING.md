# Architecture cible — Tiers, prestations, planning, facturation

## Principe directeur

Noethys devient la source métier unique pour les tiers, les prestations, la facturation et les encaissements.
PMSL-Équipe reste la source RH/planning des intervenants.
Dolibarr Oxygène reçoit les données comptables validées et ne devient pas une seconde logique de facturation parallèle.

## Chaîne métier

Demande du partenaire
→ arbitrage / validation
→ programmation des créneaux
→ affectation de l'intervenant
→ génération des interventions prévisionnelles
→ convention + annexe
→ réalisation / annulation / remplacement
→ validation du réalisé
→ facturation
→ encaissement
→ synchronisation comptable vers Dolibarr Oxygène.

## Structures et tiers

Le modèle doit accepter sans identifiant administratif obligatoire :
- associations ;
- clubs / sections ;
- écoles ;
- mairies / collectivités ;
- ALSH gérés par une mairie ou par une association ;
- Département / ASE ;
- autres partenaires et financeurs.

RNA, SIREN, SIRET, APE/NAF restent facultatifs et peuvent être saisis manuellement ou proposés par une recherche publique assistée.

Une structure peut cumuler plusieurs rôles selon la relation : organisateur, gestionnaire, bénéficiaire, payeur, financeur/subventionneur, partenaire, donneur d'ordre, structure d'accueil.

## Contacts

Les contacts appartiennent à une structure et peuvent avoir plusieurs rôles : président, trésorier, direction, APEL, responsable de section, planning, facturation, convention, administratif, urgence, etc.

## Groupes libres

Les écoles, associations et autres structures utilisent un libellé libre « section / classe / groupe » afin de ne pas figer une hiérarchie annuelle.

## Prestations et consommations

Le moteur historique des consommations et prestations de Noethys est conservé autant que possible.
Le vocabulaire d'interface dépend du contexte :
- familles : consommations / réservations ;
- clubs, écoles, collectivités : interventions / séances / prestations.

Une intervention porte au minimum : date, créneau, structure bénéficiaire, activité, intervenant prévu, intervenant réalisé, état, durée prévue, durée réalisée, durée validée, tarif et statut de facturation.

## Demande annuelle et renouvellement

Une fiche « Demande / programmation annuelle » enregistre : structure, saison, contacts, renouvellement ou nouveaux créneaux, groupe libre, jours/horaires, période souhaitée, observations et statut de traitement.

Le renouvellement d'une saison doit permettre de recopier la programmation précédente puis de marquer chaque ligne : inchangée, modifiée, supprimée ou ajoutée.

## Formulaire web futur de demande annuelle

Le formulaire papier de demande de créneaux doit pouvoir être remplacé par un formulaire web public ou semi-public sécurisé par un lien ou jeton propre à la structure.

Objectifs :
- préremplir la structure et ses contacts connus ;
- présenter les créneaux de la saison précédente ;
- permettre, ligne par ligne : inchangé, modifier, supprimer ou ajouter ;
- permettre la correction des coordonnées et des contacts de planning/facturation ;
- enregistrer directement la demande dans Noethys sans ressaisie ;
- historiser les demandes par saison ;
- soumettre la programmation à l'écran « Impact planning » de PMSL-Équipe avant validation ;
- produire ensuite convention et annexe prévisionnelle depuis la programmation acceptée.

Ce formulaire peut constituer un premier module web dédié avant l'existence d'un portail structures complet.

## Convention et annexe

La convention et la facturation ne sont pas saisies séparément : elles sont produites depuis la même relation contractuelle et la même programmation.

La convention reprend le modèle documentaire existant sans en modifier arbitrairement la structure.
L'annexe détaille les interventions prévisionnelles date par date, comme l'édition actuelle des réservations.
Un changement en cours de saison peut produire un avenant sans écraser la convention initiale.

## PMSL-Équipe

Chaque créneau / relation contractuelle possède un identifiant stable partagé avec PMSL-Équipe.

Noethys fournit :
- structure ;
- activité ;
- période ;
- créneau ;
- besoin métier ;
- tarif et relation contractuelle.

PMSL-Équipe fournit :
- intervenant affecté ;
- disponibilités ;
- conflits ;
- temps de travail ;
- trajets ;
- absences ;
- remplacements ;
- validation RH du réalisé.

Une affectation validée doit répercuter automatiquement le planning éducateur sans seconde saisie.
Un remplacement dans PMSL-Équipe doit mettre à jour l'intervenant réalisé sans recréer la séance.

Avant validation d'une programmation, un écran « Impact planning » doit pouvoir signaler les indisponibilités, conflits, temps de trajet et surcharges.

## Historique de résidence et financements communaux

Les participations communales liées à la fréquentation des ALSH sont calculées depuis les enfants et consommations déjà présents dans Noethys, sans double saisie.

La résidence doit être historisée avec date de début et date de fin.
La commune attribuée à une présence est celle de l'enfant à la date de cette présence.

Les états financiers validés sont figés afin qu'une correction ultérieure d'adresse ne modifie pas silencieusement une demande déjà envoyée.

## Facturation et encaissements

Noethys est la source unique de vérité pour :
- prestations ;
- factures ;
- avoirs ;
- règlements / encaissements ;
- soldes ;
- remboursements.

Les modalités de facturation appartiennent à la relation contractuelle, pas au type de structure : mensuelle, trimestrielle, après validation du réalisé, manuelle, etc.

## Dolibarr Oxygène

Le connecteur utilise les identifiants stables Noethys pour synchroniser de manière idempotente les tiers, factures, règlements et données comptables utiles.
Une même mairie ou association reste un seul tiers comptable même si elle cumule plusieurs rôles ou activités.

## Compatibilité

Cette architecture doit être introduite de manière additive.
Les familles, individus, consommations, prestations, tarifs et bases existantes restent exploitables.
Aucune migration destructive ou remplacement massif des tables historiques n'est autorisé sans nécessité démontrée et procédure de migration testée.
