# Noe-042 — État de préparation de la Release Candidate

## Position actuelle

Les **portes techniques critiques sont franchies**. Le dépôt peut désormais produire un candidat Windows portable techniquement qualifié.

Une RC ne doit toutefois **pas** être publiée comme validée tant que la recette humaine sur une copie de base réellement utilisée n'a pas été effectuée.

## Portes techniques franchies

- **SQL / bases** : audit SQL strict, `OL_Reglements`, export comptable et audit d'index traités ;
- **Python** : baseline Python 3.10 qualifiée, études 3.11 et 3.12 vertes et conservées en requalification à la demande ;
- **wxPython** : audit Phoenix intégré à la CI, incompatibilité réelle `SystemSettings_GetFont` corrigée ;
- **plateformes** : smoke tests Windows, macOS et Linux GTK3 ;
- **non-régression métier** : découverte complète `tests/test_*.py` intégrée à la CI ;
- **bases existantes** : préflight Noe-030 en lecture seule, empreinte de schéma et contrôle SHA-256 SQLite ;
- **sauvegarde/restauration** : contrôle de flux réparé et tests de restauration ajoutés ;
- **packaging Windows** : PyInstaller `onedir` qualifié par exécution réelle de l'archive extraite sans Python externe ;
- **layout PyInstaller 6** : disposition `_internal` refusée, layout plat historique restauré afin de rester compatible avec `Chemins.py` ;
- **mode portable** : dossier historique `Portable/` livré dans l'archive, isolation config/données testée et marqueur vérifié après extraction ;
- **traçabilité** : `BUILD-INFO.txt` identifie commit, Python, run, date de fabrication et activation du mode portable.

## Portes humaines obligatoires avant publication d'une RC

### 1. Noe-030 — recette sur une copie de base réelle

Utiliser exclusivement une **copie** d'une base Noethys réellement utilisée.

Minimum attendu :

- préflight lecture seule avant ouverture ;
- démarrage du portable Windows ;
- familles / individus ;
- activités / groupes / inscriptions ;
- consommations / réservations ;
- prestations / facturation ;
- règlements et ventilation ;
- comptabilité / export réellement utilisé ;
- génération d'un PDF ;
- sauvegarde et restauration sur la copie si le contexte le permet ;
- fermeture et réouverture ;
- second préflight et confirmation que le `schema_digest` n'a pas changé de façon inattendue.

### 2. Validation visuelle Windows

La CI lance le véritable EXE en mode smoke mais s'arrête volontairement avant `Noethys.py`. Un humain doit donc encore confirmer :

- ouverture réelle de la fenêtre principale ;
- absence de dialogue ou ressource manquante ;
- comportement normal des écrans critiques utilisés pendant la recette ;
- fermeture propre de l'application.

## Ce qui n'est pas bloquant pour cette première RC

- installateur Windows système ;
- signature de code ;
- paquet macOS signé/notarisé ;
- paquet Linux ;
- migration Python 3.11 ou 3.12 comme baseline ;
- migration de la base vers une version MySQL/MariaDB plus récente.

Ces sujets peuvent être traités après stabilisation sans retarder une RC Windows portable compatible avec l'existant.

## Décision RC

La partie **technique automatisée est prête**. Pour figer puis publier une RC validée :

1. sélectionner le SHA candidat sur `master` ;
2. confirmer CI + `Package Windows` verts sur ce SHA ;
3. vérifier `BUILD-INFO.txt` dans l'artefact ;
4. exécuter Noe-030 sur une copie de base réelle ;
5. effectuer la recette Windows manuelle ;
6. corriger tout défaut bloquant éventuel et relancer les contrôles concernés.

Tant que les points 4 et 5 ne sont pas réalisés, le projet dispose d'un **candidat technique RC**, mais la validation finale reste volontairement en attente.
