# NOETHYS VANILLA — READINESS

## Statut

**Qualification automatisée Vanilla : VALIDÉE.**

**Recette finale Windows + copie réelle de BDD : VALIDATION MANUELLE REQUISE.**

Le candidat runtime/package est figé. La branche documentaire `docs/vanilla-readiness` part exactement de ce candidat afin de ne pas déplacer le SHA qualifié avant la recette humaine.

## Candidat figé

- Branche runtime : `master`
- SHA candidat complet : `74d25fdd8431eb7a167ab35cab8e1e8aa4e3bdc9`
- PR #354 : `ci/reuse-windows-package-rc`, fusionnée après CI verte.
- PR #357 : `ci/package-windows-master`, fusionnée en squash ; son commit de fusion est le SHA candidat ci-dessus.
- Branche de documentation : `docs/vanilla-readiness`, basée directement sur `74d25fdd8431eb7a167ab35cab8e1e8aa4e3bdc9`.

Aucune modification runtime, SQL, de schéma, de format de données ou de protocole Connecthys n'est introduite par la branche documentaire.

## CI terminale du candidat

Workflow `CI Noethys`, run #2389, run ID `34114566920`, sur le SHA exact `74d25fdd8431eb7a167ab35cab8e1e8aa4e3bdc9`.

| Job | Statut final |
| --- | --- |
| `Validation rapide Python / métier / UI / schéma` | `success` |
| `Package Windows portable` | `skipped` |
| `Recette synthétique et inventaires complets` | `skipped` |
| `Smoke test Windows` | `skipped` |
| `Smoke test Linux GTK3` | `skipped` |
| `Smoke test macOS` | `skipped` |

Les jobs lourds sont volontairement ignorés sur un push normal ; le packaging Windows du même SHA a été exécuté séparément par le workflow dédié décrit ci-dessous. Aucune relance n'est nécessaire.

### Preuves du job rapide

- compilation des sources : `success` ;
- compilation des outils de qualification : `success` ;
- audit runtime bloquant : `success` ;
- chemins SQLite Unicode : `success` ;
- `ReqInsert` / `newID` : `success` ;
- imports métier critiques : `success` ;
- tests de non-régression métier et contrats UI : `success` ;
- imports dynamiques PyInstaller : `success` ;
- garde AUI : `success` ;
- layout wxPython : `success` ;
- lifecycle wxPython : `success` ;
- contrôle de schéma sur push : `success` ;
- bilan : `success`.

**Tests : 761 exécutés, 761 passés, `OK`.**

Le contrôle de schéma sur push conclut qu'aucune modification du schéma applicatif SQL n'a été ajoutée dans ce lot de finalisation.

## Packaging Windows du SHA exact

Workflow `Package Windows master`, run ID `34114567033`, sur le SHA exact `74d25fdd8431eb7a167ab35cab8e1e8aa4e3bdc9`.

Job : `Qualifier le packaging Windows du master exact / Construire et tester Noethys portable + installateur` — **`success`**.

Validations acquises :

- dépendances de fabrication Windows : `success` ;
- hooks runtime/compatibilité : `success` ;
- corrections Python 3 validées avant PyInstaller : `success` ;
- compilation : `success` ;
- piles fonctionnelles optionnelles : `success` ;
- PDF Unicode : `success` ;
- ressources PyInstaller essentielles : `success` ;
- construction PyInstaller : `success` ;
- présence de `Noethys.exe` et layout historique sans `_internal` : `success` ;
- `BUILD-INFO.txt` : généré ;
- Inno Setup : `success` ;
- construction `Noethys-Upgrade-Setup.exe` : `success` ;
- smoke installable : `success` ;
- conservation de la configuration existante : `success` ;
- absence de migration d'un `Config.json` placé dans un répertoire courant étranger : `success` ;
- archive portable : `success` ;
- smoke portable extrait avec environnement Python externe neutralisé : `success` ;
- publication des deux artefacts : `success`.

### Artefacts

**Installable**

- artifact GitHub : `Noethys-Windows-installer`
- artifact ID : `10015844325`
- digest GitHub : `sha256:2a3d58c16b7381f0694d02dcc3beb9a2a6df9bd7901651cb11925ed994920f94`
- contenu à exécuter après extraction : `Noethys-Upgrade-Setup.exe`

**Portable**

- artifact GitHub : `Noethys-Windows-portable`
- artifact ID : `10015847439`
- digest GitHub : `sha256:6175ada64c72a454ed54bcf8b38eb6422d667cf6e1c999a1b67ef3335f3f308c`
- contient l'archive `Noethys-Windows-portable.zip`
- le build contient `Noethys.exe`, `Portable/README.txt` et `BUILD-INFO.txt`

`BUILD-INFO.txt` du portable qualifié indique :

- `Commit: 74d25fdd8431eb7a167ab35cab8e1e8aa4e3bdc9`
- `Python: Python 3.10.11`
- `Workflow run: 34114567033`
- correctifs sources Python 3 appliqués avant PyInstaller ;
- mode Portable activé.

## Sauvegarde / restauration

**Statut : VALIDÉE AUTOMATIQUEMENT, recette réelle finale encore requise.**

Le durcissement sauvegarde/restauration de la PR #352 est intégré au candidat. Les suites `test_noe_032_backup_integrity` et `test_noe_032_restore_flow` font partie des 761 tests verts de #2389.

Les contrats couverts incluent notamment : refus des faux succès, nettoyage après échec, manifeste/intégrité, détection des dumps tronqués ou incomplets, restauration locale, restauration réseau/MySQL et vérification des postconditions.

La dernière preuve indispensable reste une sauvegarde puis une restauration dans **une seconde copie jetable de la BDD réelle**, sous Windows.

## Compatibilité BDD actuelle et Connecthys d'Ivan

### Garde bloquante Vanilla

Noethys doit conserver la base de données actuelle et continuer à fonctionner avec le Connecthys d'Ivan actuellement utilisé.

Pour le candidat `74d25fdd8431eb7a167ab35cab8e1e8aa4e3bdc9` :

- aucune modification de schéma n'est introduite par le lot final #354/#357 ;
- aucune modification de format de données n'est introduite par ce lot ;
- aucune modification de protocole Connecthys n'est introduite par ce lot ;
- aucun changement de comportement Connecthys n'est introduit par ce lot ;
- le contrôle de schéma #2389 est vert ;
- la compatibilité avec la BDD actuelle et le Connecthys d'Ivan est conservée par non-modification des contrats concernés dans cette finalisation.

**Toute future modification susceptible d'altérer schéma, format, protocole ou comportement Connecthys est BLOQUANTE tant que la compatibilité n'est pas démontrée avant implémentation.**

La recette humaine finale doit confirmer ce garde-fou sur une copie réelle de BDD et le scénario Connecthys habituellement utilisé, sans opération destructive sur les systèmes réels.

## P0 / P1

**Aucun P0/P1 bloquant connu sur le candidat figé.**

Preuves notamment acquises :

- 761/761 tests ;
- contrôles SQL ciblés contre les mises à jour globales involontaires ;
- sauvegarde/restauration durcie ;
- 0 risque PyInstaller dynamique non qualifié ;
- catégories wx à haut risque `constructor_parent_callback` et `use_after_destroy` à 0 dans le gate qualifié ;
- aucun piège sémantique de haute priorité connu dans les tests de garde ;
- aucun gestionnaire d'exception silencieux de haute priorité connu dans les tests de garde ;
- packaging installable et portable du SHA exact validé sur Windows.

## P2 / P3 explicitement reportés

Aucun nouvel audit de dette n'est ouvert pour la sortie Vanilla. Les éléments déjà inventoriés mais non démontrés comme P0/P1 restent **NON BLOQUANT REPORTÉ**, notamment :

- avertissements statiques `RESULT_UNGUARDED` / `RESULT_ASSIGN` qui ne sont pas des défauts dangereux confirmés ;
- dette UI/layout et couplages wx historiques hors catégories à haut risque ;
- autres inventaires statiques de maintenance qui n'affectent pas les critères de sortie Vanilla.

Ils ne doivent pas être corrigés opportunément avant la recette humaine finale.

## Recette humaine finale Windows

**Règle absolue : ne jamais utiliser la BDD de production. Utiliser une copie réelle et jetable.**

1. Télécharger l'artifact `Noethys-Windows-installer` du run `34114567033`, artifact ID `10015844325`, l'extraire puis lancer `Noethys-Upgrade-Setup.exe`.
   - Attendu : installation sans erreur.
   - Échec : installateur en erreur, fichier absent, antivirus/Windows bloque définitivement l'exécution.

2. Dans le dossier installé, ouvrir `BUILD-INFO.txt`.
   - Attendu : `Commit: 74d25fdd8431eb7a167ab35cab8e1e8aa4e3bdc9`.
   - Échec : SHA différent ou `BUILD-INFO.txt` absent.

3. Lancer Noethys.
   - Attendu : fenêtre principale visible, pas de crash ni boucle de démarrage, configuration existante conservée.
   - Échec : crash, écran bloqué, paramètres usuels perdus ou configuration existante écrasée.

4. Connecter Noethys à une **copie réelle** de la BDD actuellement utilisée.
   - Attendu : connexion normale, données existantes lisibles, aucune migration inattendue.
   - Échec bloquant : demande ou exécution d'une modification de schéma non prévue, incompatibilité SQL, données illisibles.

5. Ouvrir les écrans principaux puis une famille et un individu réels de la copie.
   - Attendu : listes et fiches se chargent sans exception ; navigation normale.
   - Échec : exception, fiche impossible à ouvrir, données incohérentes par rapport à la copie.

6. Créer ou modifier une donnée **de test** dans la copie, enregistrer, fermer la fiche puis la rouvrir.
   - Attendu : enregistrement réussi et valeur relue identique.
   - Échec : sauvegarde silencieusement perdue, erreur SQL, écriture sur une autre fiche/ligne.

7. Tester une liste/table métier : recherche, filtre, sélection, ouverture d'une ligne ; puis lancer un export et un aperçu/impression ou PDF.
   - Attendu : contenu cohérent, aucune exception, export/PDF produit ou aperçu imprimable.
   - Échec : crash, filtre faux, données corrompues, export/impression impossible.

8. Vérifier le scénario Connecthys actuellement utilisé, en lecture ou sur un périmètre de test non destructif.
   - Attendu : configuration reconnue et comportement/protocole habituel inchangé.
   - Échec bloquant : incompatibilité de protocole, erreur liée au schéma/format, comportement différent qui empêcherait l'usage actuel avec le Connecthys d'Ivan.

9. Depuis Noethys, faire une sauvegarde de la copie réelle.
   - Attendu : succès explicite et archive exploitable ; aucun faux succès.
   - Échec : erreur masquée, archive manquante/incomplète, message de succès malgré une erreur.

10. Restaurer cette sauvegarde dans une **seconde copie jetable**, jamais par-dessus la copie de départ ni la production.
    - Attendu : restauration déclarée réussie, ouverture de la seconde copie, présence des données existantes et de la modification de test de l'étape 6.
    - Échec bloquant : checksum/manifeste invalide, dump tronqué, restauration partielle, objets/données manquants, faux succès.

11. Fermer Noethys proprement puis le relancer une dernière fois sur la copie de test.
    - Attendu : fermeture sans blocage, redémarrage normal, configuration conservée.
    - Échec : crash/hang à la fermeture, configuration perdue, redémarrage impossible.

## Verdict avant recette humaine

- Qualification automatisée : **VALIDÉE**.
- Packaging Windows : **VALIDÉ**.
- P0/P1 connus : **AUCUN**.
- BDD actuelle : **CONTRAT CONSERVÉ**.
- Connecthys d'Ivan : **CONTRAT CONSERVÉ DANS LE LOT FINAL ; validation fonctionnelle finale à confirmer sur copie réelle**.
- Recette humaine : **VALIDATION MANUELLE REQUISE**.
