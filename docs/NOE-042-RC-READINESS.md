# Noe-042 — État de préparation de la Release Candidate

## Position actuelle

La modernisation technique critique est désormais largement qualifiée. Une RC ne doit toutefois **pas** être publiée tant que la recette humaine sur une copie de base réellement utilisée n'a pas été effectuée.

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
- **traçabilité** : `BUILD-INFO.txt` identifie commit, Python, run et date de fabrication.

## Porte technique encore en cours

- **Noe-041 — mode portable** : activation explicite du dossier historique `Portable/`, isolation de la configuration et des données, tests de chemins et validation du marqueur dans l'archive finale.

Cette porte doit être fusionnée avant de figer le commit candidat RC.

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

La RC est **prête à être figée** lorsque :

1. Noe-041 est fusionné ;
2. la CI du SHA candidat est verte ;
3. `Package Windows` est vert sur ce même SHA ;
4. l'artefact est identifié par `BUILD-INFO.txt` ;
5. Noe-030 a été exécuté sur une copie de base réelle ;
6. la recette Windows manuelle ne révèle aucun blocage ;
7. les anomalies éventuelles sont corrigées puis les contrôles concernés relancés.

Tant que les points 5 et 6 ne sont pas réalisés, le projet peut produire un **candidat technique**, mais il ne doit pas être présenté comme une RC validée.
