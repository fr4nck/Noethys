# Noe-042 — État de préparation de la Release Candidate

> État consolidé au 24 août 2026.

## Position actuelle

Les **portes techniques critiques du socle sont franchies**. Le dépôt peut produire un candidat Windows portable techniquement qualifié.

Une RC ne doit toutefois **pas** être publiée comme validée tant que la recette humaine n'a pas été effectuée sur une copie de base réellement utilisée avec **le SHA exact qui doit être publié**.

Cette précision est importante : le `master` a continué à recevoir des corrections et évolutions depuis la première préparation du sas RC. La qualification d'un ancien artefact ne valide pas automatiquement un nouveau candidat.

Le socle UI transverse Repens est maintenant consolidé sur `master`. La phase suivante n'est donc plus une refonte UI générale : elle consiste à qualifier le comportement réel sous Windows et à corriger uniquement les anomalies observées.

## Portes techniques franchies

- **SQL / bases** : chemins critiques règlements/exports sécurisés ; audit d'index disponible ; dette Noe-005 séparée ;
- **Python** : baseline Python 3.10 ; 3.11 qualifié ; 3.12 étudié ;
- **wxPython** : audit Phoenix, contrats UI et smoke tests de layout ;
- **UI commune** : socle Repens consolidé pour listes/ObjectListView, grilles, outils de liste, navigation et états vides ;
- **plateformes** : Windows, macOS, Linux GTK3 qualifiés au niveau du code source ;
- **non-régression métier** : `tests/test_*.py` exécutés globalement ;
- **bases existantes** : préflight lecture seule, empreinte de schéma et contrôles SQLite/MySQL ;
- **sauvegarde/restauration** : flux réparé et tests ajoutés ;
- **packaging Windows** : PyInstaller `onedir` plat qualifié par exécution réelle de l'archive extraite ;
- **mode portable** : `Portable/` livré et isolation testée ;
- **traçabilité** : `BUILD-INFO.txt` ;
- **sas RC** : workflow manuel protégé, release créée en brouillon uniquement ;
- **CI** : une porte d'entrée unique `ci.yml`, rapide sur PR/push et complète sur déclenchement manuel.

## Changements intégrés après la première préparation RC

Le candidat final doit également prendre en compte les changements déjà fusionnés dans `master`, notamment :

- commandes de repas par points de livraison ;
- échelle d'interface et modes Système / Clair / Sombre ;
- design system commun et préférences d'apparence/accessibilité ;
- consolidation transverse Repens des listes, grilles, navigation et outils communs ;
- instrumentation des freezes et lenteurs MySQL distantes ;
- corrections wxPython et AUI intégrées ;
- sauvegarde atomique des contrats PSU ;
- corrections de saisie ville/code postal ambiguë ;
- autres correctifs fusionnés depuis le premier sas.

Ces éléments ne changent pas le principe du sas : ils élargissent simplement ce qui doit être réellement testé si le SHA candidat les contient.

## Portes humaines obligatoires avant publication

### 1. Noe-030 — recette sur copie réelle

Utiliser exclusivement une **copie** d'une base Noethys réellement utilisée.

Minimum :

- préflight avant ouverture ;
- démarrage du portable Windows ;
- familles / individus ;
- activités / groupes / inscriptions ;
- consommations / réservations ;
- prestations / facturation ;
- règlements et ventilation ;
- comptabilité / export réellement utilisé ;
- PDF ;
- sauvegarde/restauration si pertinent ;
- fermeture/réouverture ;
- second contrôle de schéma.

### 2. Validation visuelle Windows

Le parcours manuel est décrit dans `CI-WINDOWS-AUDIT.md` et peut être préparé depuis les sources avec `DEV-Noethys.cmd`.

Vérifier au minimum :

- fenêtre principale ;
- dialogues courants ;
- absence de fenêtre vide/freeze/assertion sizer ;
- thèmes Système / Clair / Sombre ;
- échelles couramment utilisées, dont 120/125 % et 150 % ;
- titres longs, listes, grilles, toolbars et panneaux AUI ;
- recherche/filtrage/cochage des listes raccordées ;
- fermeture propre.

### 3. Fonctions nouvellement fusionnées réellement utilisées

Suivre `RC-CHECKLIST.md` pour les scénarios supplémentaires : commandes de repas, contrats PSU, MySQL distant/performance et autres fonctions présentes dans le SHA candidat.

## Ce qui reste hors exigence de la première RC

- installateur Windows système ;
- signature de code ;
- paquet macOS signé/notarisé ;
- paquet Linux utilisateur final ;
- migration baseline Python 3.11/3.12 ;
- migration obligatoire vers un MySQL/MariaDB récent ;
- clôture complète de Noe-005 ;
- achèvement de tous les chantiers Noe-060/061/062/063 encore ouverts.

Un chantier ouvert n'empêche pas la RC s'il ne constitue pas un défaut bloquant du code déjà intégré au SHA candidat.

## Procédure de décision RC

1. choisir le SHA candidat sur `master` ;
2. confirmer CI + packaging verts pour ce SHA ;
3. vérifier `BUILD-INFO.txt` ;
4. lancer `scripts/rc_db_preflight.py` sur la copie réelle ;
5. effectuer la recette métier et visuelle ;
6. appliquer les scénarios spécifiques aux fonctions fusionnées ;
7. si un défaut bloquant est corrigé, recommencer la qualification sur le nouveau SHA ;
8. déclencher le workflow `Release Candidate` ;
9. relire la release brouillon ;
10. publier uniquement après décision explicite.

## Conclusion

Le projet dispose d'un **socle techniquement prêt pour fabriquer une RC**, mais pas encore d'une **RC validée en exploitation** tant que la recette réelle du SHA final n'a pas été menée.
