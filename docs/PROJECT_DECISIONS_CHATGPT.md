# Décisions de projet consolidées

> Consolidation au 14 septembre 2026.
>
> Objectif : aucune décision durable de Noethys ne doit dépendre de la conservation d'une conversation ChatGPT. GitHub est la mémoire du projet ; les conversations sont des espaces de travail temporaires.

## Source de vérité

Ordre de confiance :

1. code et tests sur `master` pour le comportement réellement livré ;
2. issues et PR GitHub pour le travail en cours et l'historique ;
3. `docs/` pour les décisions durables, l'architecture et les procédures ;
4. conversations uniquement avant consolidation.

Toute décision durable prise en conversation doit finir dans GitHub avant fermeture du sujet.

## Noethys Vanilla

Vanilla doit rester conservateur.

- Conserver la base de données actuelle et sa structure historique.
- Ne pas introduire de migration implicite ou destructive pour finaliser Vanilla.
- Conserver la compatibilité avec le Connecthys existant actuellement utilisé ; Vanilla ne doit ni casser ni remplacer cette intégration.
- Conserver les configurations et formats historiques autant que possible.
- Les corrections Python 3, wxPython, runtime, packaging, stabilité et compatibilité restent dans le périmètre.
- Les gros changements de schéma, d'indexation persistante, de cache persistant, de threading/async global ou de moteur de données ne doivent pas être introduits uniquement pour moderniser Vanilla.
- Les optimisations non indispensables sont à étudier après gel/tag de Vanilla, sur mesures réelles.

### Interface de Vanilla

- Une interface claire, directe et proche du fonctionnement historique est la cible.
- La visibilité directe des listes et informations métier est prioritaire.
- Le thème sombre et les transformations visuelles lourdes ne sont pas nécessaires à la finalisation de Vanilla.
- Les améliorations techniques ou fonctionnelles déjà validées doivent être conservées.

## Modernisation graphique : branche Qt séparée

La réflexion Qt est distincte de Vanilla.

Intention : conserver Noethys, ses données, ses tableaux, ses comportements métier et ses habitudes d'usage tout en testant un moteur graphique plus moderne.

Garde-fous :

- prototype isolé dans une branche dédiée ;
- aucun changement de base ou de logique métier uniquement pour démontrer l'interface ;
- réutiliser les contrôleurs et comportements existants autant que possible ;
- préserver la densité desktop, les tableaux, raccourcis et interactions utiles ;
- ne pas reproduire le découpage lourd vécu sur Teamworks ;
- si Qt impose une duplication importante de logique métier ou une réarchitecture générale avant même de valider un premier écran, revoir la stratégie.

Le design visuel de référence reste `DESIGN_SYSTEM_UI_UX.md`. Il décrit la direction visuelle sans rendre obligatoire une migration Qt du produit principal.

## Base de données

À court terme, la règle est la stabilité.

- Noethys continue à fonctionner avec la base actuelle.
- MySQL/MariaDB historique et SQLite restent des compatibilités à préserver autant que raisonnablement possible.
- Pas de migration de moteur de base dans le cadre de Vanilla.
- Toute évolution future du moteur SQL doit être étudiée séparément avec stratégie de migration, compatibilité Connecthys et recette sur copie réelle.
- Mesurer d'abord requêtes, latence réseau et blocages UI avant toute optimisation.

## Connecthys et comptes multi-rôles

Décision d'architecture : un même individu doit pouvoir cumuler plusieurs rôles dans les portails, par exemple parent ou représentant familial, salarié, représentant d'association, école, mairie ou autre tiers autorisé.

Ordre de livraison :

- première cible : portail famille, principalement alimenté par Noethys ;
- portail salarié développé progressivement en parallèle, principalement alimenté par Teamworks ;
- le portail salarié ne doit pas bloquer la mise en production du portail famille ;
- les rôles supplémentaires doivent pouvoir être ajoutés sans recréer un second système d'identité incompatible.

Principes d'échange :

- ne pas exposer directement la base Noethys locale au web ;
- utiliser des interfaces contrôlées et des identifiants stables ;
- Noethys reste la source de vérité pour les tarifs et données métier qu'il porte déjà ;
- ne pas dupliquer inutilement tarifs, familles ou inscriptions dans un moteur simplifié du portail ;
- les premières évolutions restent compatibles avec le Connecthys hébergé existant tant que son remplacement n'a pas fait l'objet d'une décision explicite.

## Frontières entre projets

- **Noethys** : familles, individus, inscriptions, consommations, prestations, facturation et données liées aux activités.
- **Teamworks-CCNS** : RH, temps de travail, CCNS et organisation des salariés.
- **Portails / Connecthys** : interfaces web familles/salariés et vues contrôlées des données.
- **PMSL-Arch** : référence d'architecture d'exploitation PMSL lorsqu'une décision de déploiement ou d'intégration doit être alignée avec l'environnement réel.

Règle d'arbitrage : aligner les dépôts `fr4nck` sur l'architecture d'exploitation validée, puis laisser la CI vérifier ce qui est versionné. Ne pas modifier la production pour s'adapter à une expérimentation locale non validée.

## Questionnaires Noethys et Noé-Doc

Cette partie reste une exploration fonctionnelle.

Constats des essais :

- une catégorie de questionnaire « Convention sportive » a servi à tester le stockage d'informations liées à une association ou à une convention ;
- widgets natifs observés : liste déroulante, cases à cocher, date, montant, porte-documents et RFID ;
- priorité à la réutilisation des mécanismes natifs de Noethys avant de créer une nouvelle mécanique ;
- objectif : pouvoir produire ou alimenter une convention à partir des données d'un club, tiers ou activité sans double saisie lorsque l'information existe déjà.

Points non résolus :

- le mécanisme exact des mots-clés ou variables utilisables dans Noé-Doc n'est pas établi de manière fiable ;
- la page ou le mécanisme historique de téléchargement de nouveaux modèles Noé-Doc n'était plus disponible lors des essais ;
- l'initialisation de Noé-Doc a présenté un comportement bloquant pendant les tests.

Conclusion : ne pas bâtir une nouvelle architecture documentaire sur des hypothèses concernant Noé-Doc. Qualifier d'abord le fonctionnement natif actuel.

## Portail salarié et pointage

Les besoins de pointage des éducateurs et animateurs relèvent du portail salarié/Teamworks, pas d'une réécriture du cœur Noethys Desktop.

Lorsque Noethys fournit des données utiles — activités, séances, participants, contacts — elles doivent être exposées par une interface stable, pas par un accès direct du portail aux tables internes.

## Ce qui n'a plus besoin d'être conservé dans les chats

Peuvent être supprimés sans valeur d'archive : discussions préparatoires d'une PR déjà fusionnée ou fermée, prompts temporaires envoyés à d'autres assistants, détails de CI visibles dans GitHub Actions, audits ponctuels dont le résultat utile est intégré au code ou aux tests, hésitations intermédiaires remplacées par une décision documentée, captures et diagnostics devenus sans objet après correction.

L'historique Git et les PR conservent la provenance technique ; le chat n'a pas à devenir une seconde archive.

## Règle pour les prochaines conversations

Avant de considérer un fil terminé :

1. si du code a changé, la décision doit être visible dans le code, les tests ou la PR ;
2. si du travail reste, il doit exister dans une issue ou un backlog GitHub ;
3. si une règle transversale a été décidée, mettre à jour le document canonique correspondant ;
4. ensuite, la conversation peut être supprimée.

La conservation d'un chat ne doit plus être un prérequis pour reprendre le projet.