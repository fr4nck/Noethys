# Architecture cible — Tiers, programmes, séances, planning, conventions et facturation

## Principe directeur

Noethys devient la source métier de référence pour les tiers, activités/programmes, relations contractuelles, séances, lieux, facturation et encaissements.

Teamworks reste la source RH : salariés, contrats, temps de travail, compétences, disponibilités et contrôles CCNS.

PMSL-Équipe reste le cockpit opérationnel de planification et de validation terrain : affectations, planning des éducateurs, remplacements et validation du réalisé.

Dolibarr / Oxygène reçoit les données comptables validées et ne devient pas une seconde logique de facturation parallèle.

## Priorité de mise en œuvre — rentrée 2026

La création du référentiel des **tiers et contacts** est prioritaire avant la refonte graphique complète et avant la migration du moteur de base de données.

Ordre retenu :
1. référentiel des tiers et contacts (Noe-062A) ;
2. rôles, groupes libres et sections ;
3. relations contractuelles ;
4. conventions / avenants ;
5. programmation et occurrences ;
6. facturation, reporting et synchronisations.

L'interface du premier lot reste volontairement simple et s'appuie sur le socle UI actuel. La refonte graphique générale ne doit pas bloquer la livraison métier.

## Modèle métier canonique

Le modèle de référence est :

`structure / personne morale → contacts → section / classe / cycle / service / groupe libre → programme ou activité contractuelle → séances prévues → séance réellement effectuée`

La séance réelle conserve notamment :

- le lieu réellement utilisé ;
- l'éducateur réellement présent ;
- les horaires et la durée réels ;
- son statut et sa validation.

Le modèle est générique. Les libellés d'interface varient selon le contexte sans créer des moteurs séparés : section sportive, classe, cycle scolaire, service, groupe, programme annuel, cycle EPS, mise à disposition, etc.

## Structures et tiers

Le modèle doit accepter sans identifiant administratif obligatoire :

- associations ;
- clubs / sections ;
- écoles ;
- mairies / collectivités ;
- hôpitaux, EHPAD et autres établissements de santé ;
- ALSH gérés par une mairie ou par une association ;
- Département / ASE ;
- autres partenaires et financeurs.

RNA, SIREN, SIRET, APE/NAF restent facultatifs.

Une structure peut cumuler plusieurs rôles selon la relation : organisateur, gestionnaire, bénéficiaire, payeur, financeur/subventionneur, partenaire, donneur d'ordre, propriétaire ou gestionnaire d'un lieu, structure d'accueil.

Une structure comptable ne doit pas être dupliquée parce qu'elle exerce plusieurs rôles.

## Contacts

Les contacts appartiennent à une structure et peuvent avoir plusieurs rôles :

- président / bureau ;
- direction ;
- enseignant / référent pédagogique ;
- APEL ou association de parents d'élèves ;
- responsable de section ;
- trésorerie / facturation ;
- planning ;
- convention ;
- administratif ;
- technique / accès ;
- urgence ;
- autre.

Le contact qui commande ou suit la prestation n'est pas nécessairement celui qui gère le lieu physique.

## Groupes libres, sections, classes et cycles

Le niveau situé sous la structure est volontairement libre afin de ne pas figer une hiérarchie annuelle.

Exemples :

- école : Cycle 1, Cycle 2, Cycle 3, PS, MS, GS, CP, CE1, CE2, CM1, CM2, `Classe Mme Dupont` ;
- association : section tennis, section football, gymnastique adultes ;
- hôpital / EHPAD : service, unité, groupe ;
- collectivité : service, équipement ou groupe.

Une section ou un groupe peut être renommé, activé ou archivé sans casser l'historique. Une nouvelle sous-structure n'est créée que lorsqu'il existe une vraie différence d'activité ou d'organisation.

## Programme / activité contractuelle

Le programme représente la prestation organisée sur une période.

Exemples :

- `EPS Cycle 2 — athlétisme — septembre/octobre 2026` ;
- `Section gymnastique adultes — saison 2026-2027 — 34 séances` ;
- `Sport-santé EHPAD — 2026-2027`.

Il peut porter :

- saison / période ;
- pratique ou discipline ;
- groupe / section ;
- nombre de séances prévu ;
- jours et horaires habituels ;
- tarif et mode de facturation ;
- relation contractuelle / convention ;
- lieu habituel ;
- éducateur habituel ou référent lorsque l'affectation est connue.

Le nombre de 34 séances est un cas PMSL fréquent, pas une règle codée en dur.

## Prestations, activités et inscriptions Noethys

Le moteur historique des activités, inscriptions, consommations, prestations et tarifs est conservé autant que possible.

L'objectif n'est pas de créer un moteur `sport` séparé mais d'utiliser le caractère flexible de Noethys pour faire cohabiter :

- familles et ALSH ;
- écoles ;
- associations et sections ;
- collectivités ;
- établissements de santé ;
- autres partenaires.

Les différences sont portées par le tiers, la relation contractuelle, le groupe/section, le programme, les vues métier et le vocabulaire d'interface.

Le vocabulaire peut donc dépendre du contexte :

- familles : inscriptions, consommations, réservations ;
- écoles / associations / institutions : programmes, interventions, séances, prestations.

Aucune duplication de logique de facturation ne doit être introduite.

## Éducateurs et séances

L'éducateur sportif est le dernier maillon opérationnel de la chaîne et non un attribut permanent de l'école ou de la structure.

### Écoles

`établissement → contacts → classe/cycle/groupe → pratique ou cycle sportif → séances → éducateur de la séance`

### Associations / institutions

`personne morale → contacts → section/service → programme annuel → séances → éducateur de la séance`

Un programme peut avoir un éducateur habituel afin de préremplir les occurrences. Chaque séance conserve néanmoins son propre éducateur réellement affecté.

Cette distinction permet de gérer les remplacements sans réécrire le programme ou la convention. Le workflow automatisé de remplacement peut être développé plus tard, mais le modèle doit l'autoriser dès maintenant.

## Lieux

Un **lieu** est une donnée métier autonome, distincte de l'adresse administrative ou de facturation d'une structure.

Il peut porter :

- nom ;
- rue, complément, code postal, ville ;
- coordonnées géographiques lorsque disponibles ;
- type : gymnase, terrain, école, salle, piscine, siège, autre ;
- informations d'accès et notes pratiques ;
- structure propriétaire / gestionnaire ;
- contacts référents : technique, réservation, accès/clés, urgence, administratif.

La structure cliente peut être différente de celle qui gère le lieu. Une association peut par exemple commander une prestation organisée dans un gymnase municipal dont le référent technique appartient à la mairie.

Le programme peut définir un lieu habituel. Chaque séance conserve cependant le lieu réellement utilisé pour préserver l'historique et alimenter les calculs de déplacement.

## Chaîne métier

Demande du partenaire
→ arbitrage / validation
→ programme ou cycle
→ programmation des créneaux
→ génération des occurrences
→ affectation de l'intervenant
→ convention + annexe
→ réalisation / annulation / remplacement
→ validation du réalisé
→ facturation
→ encaissement
→ synchronisation comptable.

## Demande annuelle et renouvellement

Une fiche `Demande / programmation annuelle` enregistre : structure, saison, contacts, renouvellement ou nouveaux créneaux, groupe libre, jours/horaires, période souhaitée, observations et statut de traitement.

Le renouvellement d'une saison doit permettre de recopier la programmation précédente puis de marquer chaque ligne : inchangée, modifiée, supprimée ou ajoutée.

## Cas EPS écoles — du vœu au réalisé

Le processus observé dans les écoles ne doit pas être reproduit dans plusieurs documents indépendants.

Chaîne cible :

**vœux de l'école → validation/arbitrage → cycles EPS → programmation réelle → affectation RH → séances réalisées → heures validées → facturation → rapport d'activité.**

Le document opérationnel construit aujourd'hui après les vœux doit devenir une **vue/export de la programmation acceptée**, pas une seconde source de saisie.

Pour une programmation EPS, le modèle doit pouvoir porter au minimum :

- établissement ;
- contacts utiles : direction, enseignant, APEL, administratif ;
- année scolaire / saison ;
- classe, niveau, cycle ou groupe libre ;
- période ou cycle sportif ;
- activité / discipline ;
- jour ;
- heure de début et heure de fin ;
- lieu habituel ;
- nombre de séances prévu ;
- dates / occurrences calculées ;
- volume d'heures prévisionnel ;
- tarif applicable et relation contractuelle ;
- budget prévisionnel ;
- statut de validation.

L'éducateur réel appartient à la séance. Une affectation habituelle peut préremplir les occurrences.

## PMSL-Équipe

Noethys fournit :

- identifiant stable de séance ;
- structure ;
- groupe / section ;
- programme / activité ;
- période et créneau ;
- lieu prévu ;
- besoin métier ;
- éventuel éducateur habituel ;
- relation contractuelle.

PMSL-Équipe rapproche ces besoins des ressources et contraintes RH issues de Teamworks.

L'éducateur doit pouvoir y consulter son planning puis valider les séances réellement effectuées.

La validation peut faire remonter vers Noethys :

- réalisée / annulée ;
- éducateur réellement présent ;
- horaires et durée réels ;
- lieu réellement utilisé ;
- commentaire utile.

Les échanges utilisent des identifiants stables, au minimum pour :

- la séance ;
- l'éducateur ;
- le lieu.

Un remplacement dans PMSL-Équipe modifie l'éducateur réel de la séance sans recréer celle-ci.

Avant validation d'une programmation, un écran `Impact planning` doit pouvoir signaler les indisponibilités, conflits, temps de trajet et surcharges.

## Déplacements et frais kilométriques

Les kilomètres ne sont pas une constante attachée à une activité.

Ils doivent pouvoir être calculés depuis les lieux réellement validés et, lorsque nécessaire, depuis l'enchaînement réel des déplacements d'une journée.

Deux sections d'une même association peuvent donc produire des distances différentes si elles utilisent des équipements distincts.

Le réalisé validé dans PMSL-Équipe peut alimenter les données RH et frais utiles à Teamworks, sans déplacer la responsabilité de la paie vers Noethys.

## Convention et annexe

La convention n'est pas une seconde source de données : elle est générée depuis la relation contractuelle et la programmation déjà saisies.

Elle peut reprendre :

- structure et représentant ;
- contacts ;
- section / groupe ;
- pratique ;
- période ;
- volume de séances ;
- horaires ;
- lieux ;
- éducateur prévu lorsque contractuellement pertinent ;
- tarif ;
- modalités de facturation ;
- clauses standard et annexes.

L'annexe détaille les interventions prévisionnelles date par date.

Une modification contractuelle peut produire un avenant sans écraser la convention initiale.

Les mêmes données canoniques doivent produire : convention, annexe, planning, facturation, statistiques, rapport annuel, exports et synchronisations. Les tableurs Excel et documents Word parallèles ne sont pas des sources de vérité.

## Formulaire web futur de demande annuelle

Le formulaire papier de demande de créneaux doit pouvoir être remplacé par un formulaire web public ou semi-public sécurisé par un lien ou jeton propre à la structure.

Objectifs :

- préremplir la structure et ses contacts connus ;
- présenter les créneaux de la saison précédente ;
- permettre, ligne par ligne : inchangé, modifier, supprimer ou ajouter ;
- permettre la correction des coordonnées et contacts ;
- enregistrer directement la demande dans Noethys sans ressaisie ;
- historiser les demandes par saison ;
- soumettre la programmation à PMSL-Équipe avant validation ;
- produire ensuite convention et annexe depuis la programmation acceptée.

## Reporting et statistiques

Parce que tiers, programmes, lieux et réalisé utilisent les mêmes données canoniques, Noethys doit pouvoir produire notamment :

- séances prévues, réalisées et annulées ;
- heures prévues et réalisées ;
- activité par structure, section, pratique, lieu, éducateur et période ;
- volumes facturables ;
- conventions et montants ;
- rapports annuels ;
- indicateurs partenaires et financeurs.

Aucune statistique de référence ne doit dépendre d'une ressaisie dans un fichier externe.

## Historique de résidence et financements communaux

Les participations communales liées à la fréquentation des ALSH sont calculées depuis les enfants et consommations déjà présents dans Noethys, sans double saisie.

La résidence doit être historisée avec date de début et date de fin. La commune attribuée à une présence est celle de l'enfant à la date de cette présence.

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

## Dolibarr / Oxygène

Le connecteur utilise les identifiants stables Noethys pour synchroniser de manière idempotente les tiers, factures, règlements et données comptables utiles.

Une même mairie ou association reste un seul tiers comptable même si elle cumule plusieurs rôles ou activités.

## Compatibilité

Cette architecture doit être introduite de manière additive.

Les familles, individus, consommations, prestations, tarifs et bases existantes restent exploitables.

Aucune migration destructive ou remplacement massif des tables historiques n'est autorisé sans nécessité démontrée et procédure de migration testée.

Référence transverse : `PMSL-Arch/docs/ADR/ADR-007-modele-tiers-programmes-seances-lieux.md`.
