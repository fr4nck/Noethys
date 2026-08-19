# Guide utilisateur — Noethys Upgrade

## À qui s'adresse ce guide ?

Ce document concerne les utilisateurs qui souhaitent tester ou utiliser le fork modernisé de Noethys Desktop tout en conservant une installation et des données historiques.

La règle essentielle est simple : **une nouvelle version se teste d'abord sur une copie de la base**.

## Distribution Windows portable

La distribution prioritaire est l'artefact GitHub Actions :

```text
Noethys-Windows-portable
```

Après extraction, le dossier contient notamment :

```text
Noethys.exe
BUILD-INFO.txt
Static/
Portable/
```

Le dossier `Portable/` active le mode portable historique. La configuration et les bases locales restent alors dans le dossier extrait plutôt que dans le profil Windows.

## Première installation de test

1. créer un nouveau dossier, par exemple `Noethys-RC-Test` ;
2. extraire intégralement l'archive dans ce dossier ;
3. ouvrir `BUILD-INFO.txt` pour identifier précisément la version testée ;
4. ne pas déplacer immédiatement votre base de production ;
5. lancer `Noethys.exe` une première fois ;
6. vérifier que l'accueil s'affiche sans erreur de DLL, module ou ressource.

## Tester avec une base existante

### Base locale SQLite

1. fermer complètement l'ancien Noethys ;
2. faire une copie indépendante du fichier de base ;
3. conserver l'original dans son emplacement habituel ;
4. placer uniquement la **copie** dans `Portable/Data/` du dossier de test ;
5. ouvrir cette copie avec le Noethys modernisé.

Avant la recette, le préflight Noe-030 peut produire une empreinte de référence :

```bash
python scripts/recette_existing_db_readonly.py --sqlite copie.dat --json avant.json
```

Après la recette, un second passage permet de vérifier l'absence de changement de schéma inattendu.

### Base MySQL/MariaDB

Pour une première qualification :

- préférer une copie de la base sur une instance ou une base de recette ;
- ne pas tester une nouvelle RC directement sur l'unique base distante en production ;
- conserver les paramètres de connexion historiques tant qu'aucune migration n'est explicitement décidée.

Le chantier Upgrade Noethys n'impose pas une migration vers un serveur MySQL/MariaDB plus récent pour cette RC.

## Recette minimale

Sur la copie, contrôler au minimum :

- ouverture d'une famille ;
- ouverture d'un individu ;
- consultation et modification d'une inscription de test ;
- consommations/réservations ;
- prestation et facturation ;
- saisie et ventilation d'un règlement ;
- liste des règlements/dépôts ;
- export comptable réellement utilisé ;
- génération d'un PDF ;
- fermeture puis réouverture de Noethys.

Si votre installation utilise des fonctions particulières, ajouter leurs vérifications : portail, MySQL distant, SFTP/FTPS, impression, périphériques, extensions, etc.

## Sauvegarde

Avant toute mise à jour ou recette :

- conserver une sauvegarde extérieure au dossier de test ;
- pour SQLite, conserver une copie intacte du fichier de base ;
- pour MySQL/MariaDB, disposer d'un export ou d'une copie serveur indépendante ;
- ne pas considérer le seul dossier portable comme une stratégie de sauvegarde.

Le format de sauvegarde Noethys historique reste utilisé (`.nod` non chiffré, `.noc` chiffré lorsque ce mode est choisi).

## Restauration

La restauration a été auditée et plusieurs erreurs historiques de contrôle de flux ont été corrigées dans le fork. Malgré cela, une restauration doit d'abord être testée sur une copie ou un environnement de recette.

Après restauration :

1. ouvrir la base restaurée ;
2. vérifier les données essentielles ;
3. réaliser quelques parcours métier représentatifs ;
4. ne remplacer la base de travail qu'après validation.

## Mise à jour d'un portable existant

Le dossier `Portable/` peut contenir votre configuration et vos bases locales. **Ne le supprimez pas sans sauvegarde.**

Méthode recommandée :

1. conserver l'ancien dossier Noethys complet ;
2. extraire la nouvelle version dans un dossier neuf ;
3. sauvegarder le contenu de l'ancien `Portable/` ;
4. tester la nouvelle version avec une copie des données ;
5. seulement après validation, décider du transfert de la configuration/données nécessaires.

Cette méthode permet un retour arrière immédiat.

## Retour arrière

Tant que la base n'a subi aucune migration incompatible, le retour arrière consiste à :

- fermer la version modernisée ;
- conserver la base utilisée pour analyse ;
- reprendre l'ancien dossier/application avec votre sauvegarde intacte.

Le projet comporte des garde-fous contre les migrations implicites, mais la recette sur copie reste obligatoire avant une RC.

## Windows, macOS et Linux

### Windows

Windows est la plateforme de distribution la plus avancée. L'archive portable est construite puis réellement extraite et exécutée en CI sans environnement Python externe.

### macOS

Le code source est testé automatiquement avec Python/wxPython sur macOS. Il n'existe pas encore, au même niveau de qualification, de paquet utilisateur signé/notarisé équivalent au portable Windows.

### Linux

Le code source est testé sous Ubuntu avec wxPython GTK3 et un environnement graphique virtuel. Il n'existe pas encore de paquet Linux final équivalent au portable Windows.

## Ce que signifie une CI verte

Une CI verte confirme de nombreuses frontières techniques et non-régressions, mais ne peut pas inspecter chaque écran ni connaître les particularités de votre base historique.

Avant d'adopter une RC :

- vérifier le SHA du build ;
- tester le démarrage réel ;
- ouvrir une copie de votre base ;
- exécuter la recette minimale ;
- conserver une sauvegarde de retour arrière.
