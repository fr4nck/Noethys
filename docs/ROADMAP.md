# Roadmap de modernisation de Noethys

Cette feuille de route décrit la trajectoire de modernisation du fork `fr4nck/Noethys`.

L'objectif n'est pas de réécrire Noethys ni de forcer les utilisateurs à migrer leurs données. La priorité est de prolonger durablement le logiciel en conservant son fonctionnement métier, ses bases existantes et, autant que possible, sa compatibilité historique.

## Principes directeurs

- préserver les bases et configurations existantes ;
- ne jamais introduire de migration implicite de schéma ;
- conserver la compatibilité MySQL/MariaDB historique, notamment avec les serveurs 5.5 encore utilisés ;
- rendre progressivement les requêtes compatibles avec les modes SQL modernes et stricts ;
- préférer des corrections ciblées aux refactorisations massives ;
- maintenir Windows, Linux et macOS comme cibles du code source ;
- ne pas mettre à jour les dépendances uniquement pour disposer de versions plus récentes ;
- tester les changements affectant les données sur une copie de base réelle ;
- considérer la recette métier comme complément indispensable à la CI.

## Phase 1 — Compatibilité SQL et bases existantes

**Priorité : critique**

- auditer les requêtes utilisant `GROUP BY` ;
- identifier les requêtes dépendant du comportement permissif de MySQL/MariaDB historique ;
- supprimer les `GROUP BY` artificiels lorsqu'aucune agrégation n'est nécessaire ;
- isoler les relations 1:N par sous-requêtes ou lectures séparées lorsque cela permet d'éviter des doublons ;
- conserver les agrégations réellement nécessaires en les rendant compatibles avec `ONLY_FULL_GROUP_BY` ;
- vérifier les exports comptables, règlements, ventilations, dépôts et statistiques concernés ;
- préserver la compatibilité MySQL/MariaDB 5.5 ;
- ne modifier ni le schéma ni les données pendant cette phase ;
- valider les résultats sur une copie de base réelle.

**Critère de sortie :** les parcours concernés produisent les mêmes résultats métier avec une base historique et ne reposent plus sur des extensions SQL permissives évitables.

## Phase 2 — Stabilisation wxPython multi-plateforme

**Priorité : haute**

- terminer l'audit des API wxPython historiques ;
- identifier les différences Phoenix/Classic encore présentes ;
- vérifier les contrôles, dialogues, sizers et calculs de dimensions sensibles ;
- remplacer les tailles fixes ou contournements GTK3 uniquement lorsqu'une solution portable plus robuste est disponible ;
- conserver les correctifs spécifiques à une plateforme seulement lorsqu'ils sont réellement nécessaires ;
- maintenir les contrôles CI Windows, Linux et macOS.

**Critère de sortie :** aucun correctif restant ne repose inutilement sur une hypothèse d'ancienne API wxPython ou sur une taille arbitraire qui casse sur une plateforme moderne.

## Phase 3 — Runtime Python moderne

**Priorité : haute**

- poursuivre l'élimination des patterns Python anciens réellement problématiques ;
- maintenir Python 3.10 comme environnement de référence tant qu'il reste le socle le mieux qualifié ;
- qualifier Python 3.11 progressivement ;
- envisager Python 3.12 uniquement lorsque wxPython et les autres dépendances sont suffisamment stables ;
- éviter les hausses de versions minimales sans bénéfice démontré ;
- conserver les frontières texte/binaire, chemins, encodages et imports dynamiques sous surveillance.

**Critère de sortie :** le runtime retenu est reproductible, documenté et ne dépend plus d'API Python obsolètes bloquantes.

## Phase 4 — Tests métier et non-régression

**Priorité : critique avant RC**

Sanctuariser au minimum les scénarios suivants :

- ouverture d'une base existante ;
- consultation et modification d'une famille ;
- création et modification d'un individu ;
- inscription à une activité ;
- gestion des consommations ;
- calcul de tarification ;
- génération de factures ;
- saisie et ventilation d'un règlement ;
- création et consultation d'un dépôt ;
- exports comptables ;
- attestations et impressions ;
- sauvegarde et restauration ;
- contrôles spécifiques PMSL lorsqu'ils touchent le socle partagé.

Les tests automatisés doivent couvrir les régressions techniques reproductibles. Les parcours GUI et métier qui ne peuvent pas être automatisés de manière fiable doivent rester dans une checklist de recette explicite.

**Critère de sortie :** les parcours critiques sont soit automatisés, soit documentés et reproductibles sur une copie de base réelle.

## Phase 5 — Packaging Windows

**Priorité : haute**

- fiabiliser la chaîne PyInstaller ;
- conserver un packaging `onedir` lisible et diagnostiquable ;
- produire automatiquement l'artefact `Noethys-Windows-portable` ;
- conserver un `BUILD-INFO.txt` permettant d'identifier précisément le build ;
- vérifier l'exécution sur une machine Windows sans environnement Python de développement ;
- contrôler les ressources, DLL et dépendances embarquées ;
- documenter le passage depuis une installation historique vers le build modernisé sans toucher directement à la base de production.

**Critère de sortie :** téléchargement, extraction et démarrage réussis sur une machine Windows de recette avec une copie de base existante.

## Phase 6 — Linux et macOS

**Priorité : moyenne**

- consolider les contrôles Linux ;
- maintenir la CI Linux ;
- maintenir la CI macOS ;
- corriger les régressions multi-plateformes révélées par wxPython ;
- documenter clairement ce qui est validé automatiquement et ce qui a été testé manuellement ;
- ne pas annoncer une compatibilité utilisateur complète sans recette fonctionnelle suffisante.

**Critère de sortie :** le code source reste portable et les limites de qualification de chaque plateforme sont explicites.

## Phase 7 — Documentation et gouvernance technique

**Priorité : moyenne**

- maintenir le README à jour ;
- documenter la matrice de compatibilité ;
- conserver la procédure de recette sur base existante ;
- maintenir la documentation du packaging ;
- documenter les décisions qui préservent la compatibilité historique ;
- conserver l'audit des forks comme source de régressions historiques, sans importer leurs commits en bloc ;
- distinguer clairement les corrections du socle Noethys des évolutions spécifiques PMSL ;
- conserver un backlog upstream séparé.

**Critère de sortie :** un développeur extérieur peut comprendre l'état du projet, les contraintes de compatibilité et la stratégie de modernisation sans devoir reconstituer l'historique des décisions.

## Phase 8 — Release Candidate modernisée

Une RC ne doit être produite qu'après validation des phases critiques.

- générer un build Windows identifié ;
- exécuter la recette sur une copie d'une base réelle ;
- tester les parcours métier critiques ;
- corriger uniquement les anomalies bloquantes ou les régressions constatées ;
- vérifier la documentation ;
- vérifier que les workflows nécessaires sont verts.

**Critère de sortie :** une RC peut remplacer temporairement l'installation de recette sans migration irréversible et sans anomalie critique connue.

## Phase 9 — Première version stable modernisée

La première version stable doit privilégier la fiabilité plutôt que l'ajout de fonctionnalités.

Elle devra notamment garantir :

- la continuité avec les bases existantes qualifiées ;
- un packaging Windows reproductible ;
- une CI multi-plateforme cohérente ;
- l'absence de migration implicite ;
- une documentation de recette et de retour arrière ;
- une liste claire des plateformes et environnements effectivement qualifiés.

## Après la première stable

Les sujets suivants pourront être envisagés sans bloquer la stabilisation actuelle :

- adoption éventuelle de `pyproject.toml` ;
- usage éventuel de `uv` pour la reproductibilité des environnements ;
- qualification Python 3.12 et versions ultérieures ;
- optimisation des requêtes réellement lentes ;
- amélioration progressive de l'interface ;
- approfondissement de l'intégration NoethysWeb ;
- outils de diagnostic et de réparation explicitement déclenchés par l'utilisateur ;
- évolutions métier spécifiques, traitées séparément de la modernisation du socle.

## Ordre de marche synthétique

`SQL strict → wxPython → runtime Python → tests métier → packaging → RC → stable`

La règle reste simple : **moderniser sans casser ce qui fonctionne déjà**.
