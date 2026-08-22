# Guide utilisateur — Noethys Upgrade

> Guide maintenu au 22 août 2026.

## À qui s'adresse ce guide ?

Ce document concerne les utilisateurs qui souhaitent tester ou utiliser le fork modernisé de Noethys Desktop tout en conservant une installation et des données historiques.

La règle essentielle reste : **une nouvelle version se teste d'abord sur une copie de la base**.

## Distribution Windows portable

La distribution prioritaire est l'artefact GitHub Actions Windows.

Après extraction, le dossier contient notamment :

```text
Noethys.exe
BUILD-INFO.txt
Static/
Portable/
```

Le dossier `Portable/` active le mode portable historique. Configuration et bases locales peuvent alors rester dans le dossier extrait plutôt que dans le profil Windows.

## Première installation de test

1. créer un nouveau dossier, par exemple `Noethys-RC-Test` ;
2. extraire intégralement l'archive ;
3. ouvrir `BUILD-INFO.txt` et noter le SHA ;
4. ne pas déplacer immédiatement la base de production ;
5. lancer `Noethys.exe` ;
6. vérifier que l'accueil s'affiche sans erreur de DLL, module ou ressource ;
7. vérifier rapidement l'apparence et l'échelle avant d'ouvrir la copie de base.

## Apparence et accessibilité

Le fork propose désormais :

- **Apparence** : Système / Clair / Sombre ;
- conservation de l'accent historique Vert / Bleu / Noir ;
- échelle générale de l'interface ;
- réglages d'apparence/accessibilité selon la version du candidat.

Pour une recette sérieuse :

- tester d'abord à 100 % ;
- vérifier ensuite l'échelle réellement utilisée sur le poste, notamment 120/125 % ou 150 % ;
- contrôler les titres longs, listes, grilles, dialogues et boutons ;
- si le thème sombre est utilisé, vérifier qu'aucune zone blanche ou texte illisible ne subsiste ;
- signaler toute fenêtre vide, freeze ou dialogue incomplet : ces symptômes doivent être corrigés à la source, pas contournés par un réglage caché.

## Tester avec une base existante

### Base locale SQLite

1. fermer complètement l'ancien Noethys ;
2. faire une copie indépendante du fichier de base ;
3. conserver l'original intact ;
4. placer uniquement la **copie** dans l'environnement de test ;
5. lancer le préflight prévu ;
6. ouvrir la copie avec le Noethys modernisé.

Le préflight RC unifié est documenté dans `NOE-030-RECETTE-BASE-EXISTANTE.md`.

### Base MySQL/MariaDB

Pour une première qualification :

- préférer une copie de la base ou une instance de recette ;
- ne pas tester un nouveau candidat directement sur l'unique base distante de production ;
- conserver les paramètres historiques tant qu'aucune migration n'est explicitement décidée ;
- si l'interface semble geler, distinguer latence réseau et vrai freeze avant de conclure.

Le fork n'impose pas une migration vers un serveur MySQL/MariaDB plus récent.

## Recette métier minimale

Sur la copie, contrôler au minimum :

- ouverture d'une famille ;
- ouverture d'un individu ;
- consultation/modification d'une inscription de test ;
- consommations/réservations ;
- prestation/facturation ;
- saisie/ventilation d'un règlement ;
- liste des règlements/dépôts ;
- export comptable réellement utilisé ;
- génération d'un PDF ;
- fermeture puis réouverture de Noethys.

La checklist complète et à jour est `RC-CHECKLIST.md`.

## Fonctions récentes à vérifier si vous les utilisez

### Commandes de repas

Le module peut maintenant raisonner par **points de livraison** :

- plusieurs groupes/unités peuvent être regroupés dans une même livraison ;
- les journées peuvent être retrouvées depuis les consommations réellement réservées/présentes ;
- les repas animateurs peuvent être saisis séparément ;
- les totaux sont calculés par point de livraison.

Vérifier que les journées affichées correspondent bien au site/point de livraison choisi et qu'aucune journée étrangère n'apparaît.

### Contrats PSU

La sauvegarde contrat + prestations + consommations a été rendue atomique. Sur une copie de recette, rouvrir un contrat modifié afin de vérifier que toutes les données liées sont cohérentes.

### MySQL distant

Le fork peut produire un journal de diagnostic de performance lors des investigations. En cas de lenteur, conserver ce journal plutôt que déduire qu'une fenêtre est bloquée uniquement à partir du ressenti.

## Sauvegarde

Avant toute mise à jour ou recette :

- conserver une sauvegarde extérieure au dossier de test ;
- pour SQLite, conserver une copie intacte du fichier ;
- pour MySQL/MariaDB, disposer d'un export ou d'une copie serveur indépendante ;
- ne pas considérer le seul dossier portable comme une stratégie de sauvegarde.

Le format de sauvegarde historique Noethys reste utilisé.

## Restauration

La restauration a été auditée et plusieurs erreurs historiques de contrôle de flux ont été corrigées dans le fork.

Malgré cela, une restauration doit d'abord être testée sur une copie ou un environnement de recette.

Après restauration :

1. ouvrir la base restaurée ;
2. vérifier les données essentielles ;
3. réaliser quelques parcours métier représentatifs ;
4. ne remplacer une base de travail qu'après validation.

## Mise à jour d'un portable existant

Le dossier `Portable/` peut contenir configuration et bases locales. **Ne le supprimez jamais sans sauvegarde.**

Méthode recommandée :

1. conserver l'ancien dossier complet ;
2. extraire la nouvelle version dans un dossier neuf ;
3. sauvegarder l'ancien `Portable/` ;
4. tester la nouvelle version avec une copie ;
5. seulement après validation, transférer les éléments nécessaires.

Cette méthode facilite le retour arrière.

## Retour arrière

Tant qu'aucune migration incompatible n'a été introduite :

- fermer la version modernisée ;
- conserver la base de recette pour analyse ;
- reprendre l'ancien dossier/application avec la sauvegarde intacte.

Le projet comporte des garde-fous contre les migrations implicites, mais cela ne remplace pas la recette sur copie.

## Windows, macOS et Linux

### Windows

Windows est la plateforme de distribution la plus avancée. L'archive portable est construite, ré-extraite et exécutée en CI sans environnement Python externe.

### macOS

Le code source est testé automatiquement sur macOS. Il n'existe pas encore de paquet utilisateur signé/notarisé équivalent au portable Windows.

### Linux

Le code source est testé sous Ubuntu/GTK3 avec environnement graphique virtuel. Il n'existe pas encore de paquet Linux final équivalent au portable Windows.

## Ce que signifie une CI verte

Une CI verte confirme de nombreuses frontières techniques et non-régressions, mais ne peut pas inspecter chaque écran ni connaître les particularités de votre base.

Avant d'adopter une RC :

- vérifier le SHA ;
- tester le démarrage réel ;
- ouvrir une copie de votre base ;
- exécuter la recette minimale et les fonctions spécifiques que vous utilisez ;
- contrôler thème/échelle ;
- conserver une sauvegarde de retour arrière.

## Documentation

Pour l'état courant du fork :

- `docs/README.md` — index ;
- `PROJECT_STATE.md` — état transversal ;
- `ROADMAP.md` — trajectoire ;
- `RC-CHECKLIST.md` — validation ;
- `COMMANDES_REPAS_POINTS_LIVRAISON.md` — repas ;
- `DESIGN_SYSTEM_UI_UX.md` — interface.
