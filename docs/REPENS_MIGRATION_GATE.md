# Porte de sortie — migration Repens

La modernisation UI de Noethys doit avoir une fin mesurable. L'objectif n'est pas de retoucher chaque pixel avant de pouvoir utiliser le logiciel, mais de supprimer l'ancien système graphique comme architecture parallèle.

## 1. Point de bascule architectural

La migration Repens est considérée comme suffisamment complète pour entrer en stabilisation lorsque :

- les contrôles communs et les principaux écrans métier consomment `UTILS_StyleRepens` pour les couleurs, typographies, espacements, métriques et états ;
- la **couverture Repens exclusive** mesurée par `scripts/audit_ui_layout.py` atteint au moins **95 %** des fichiers UI déclarant une dépendance de style ;
- aucun contrôle commun ne dépend encore directement de `UTILS_Interface` ou `UTILS_UIMetrics`, hors exception explicitement documentée ;
- les fichiers encore mixtes Repens/ancien socle sont des renderers ou comportements réellement particuliers et non des restes de migration ;
- les boutons bitmap historiques ne servent plus de commandes génériques lorsqu'une action Repens équivalente existe ;
- les principaux layouts ne reposent plus sur des dimensions fixes qui rognent le contenu avec le DPI, l'échelle de texte ou le redimensionnement ;
- aucune nouvelle dépendance visuelle locale n'est ajoutée dans les écrans déjà migrés.

Le seuil de 95 % n'est pas un score esthétique. Il mesure la disparition de l'architecture visuelle parallèle. Les exceptions restantes doivent pouvoir être nommées et justifiées.

## 2. Stabilisation

Une fois ce point atteint, le gros chantier UI est gelé. Les travaux deviennent uniquement :

- corrections de régression ;
- défauts de lisibilité, DPI, thème sombre ou redimensionnement réellement observés ;
- correction des exceptions Repens restantes si elles bloquent un parcours métier ;
- validation des parcours critiques et du packaging Windows.

Les améliorations purement cosmétiques non bloquantes retournent dans la roadmap après la RC.

## 3. Porte RC

La RC utilisable est ouverte après :

- compilation et tests automatisés au vert ;
- build Windows installable ;
- ouverture d'une copie d'une base existante ;
- smoke tests familles/individus, inscriptions, consommations/réservations, facturation, impressions/exports, sauvegarde/restauration ;
- vérification rapide des échelles 100/120/150 %, clair/sombre et redimensionnement ;
- absence de régression métier ou de corruption de données bloquante.

## 4. Cadence de travail

La migration doit pouvoir avancer sans présence permanente de l'utilisateur :

- travailler par lots cohérents et autonomes ;
- ne demander une décision que pour un comportement métier ambigu ou une incompatibilité réelle ;
- regrouper les demandes de recette manuelle en checkpoints plutôt que solliciter un test après chaque composant ;
- conserver les anciennes configurations et les comportements métier tant qu'une modification n'est pas explicitement nécessaire ;
- utiliser l'audit comme liste de travail pour traiter d'abord les hotspots transversaux.

Commande de référence :

```bash
python scripts/audit_ui_layout.py --json tmp/ui-layout-audit.json
```

Lorsque le chantier approche de la porte de sortie, le seuil peut être vérifié explicitement :

```bash
python scripts/audit_ui_layout.py --min-repens-clean 95
```
