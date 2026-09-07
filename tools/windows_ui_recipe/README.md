# Noethys Vanilla — prototype de pilote de recette Windows interactif

Prototype isolé du code métier, destiné à piloter le vrai `Noethys.exe` sous Windows comme un utilisateur.

## Choix technique

- `pywinauto==0.6.9`.
- backend UI Automation (`uia`) en priorité ; backend Win32 en repli.
- toutes les actions du scénario passent par `click_input()` ou par de vraies frappes clavier ; aucun handler Noethys n'est appelé directement.
- aucun clic à coordonnées fixes.
- attentes explicites et timeouts bornés.

Ce choix est particulièrement adapté à l'interface wx historique : Noethys combine des fenêtres/dialogues et boutons wx natifs avec des contrôles plus complexes AGW/AUI et un `FastObjectListView`. UIA apporte les rôles accessibles lorsqu'ils existent ; Win32 permet de retrouver une partie des contrôles natifs que UIA décrit mal.

## Dépendances

```text
pywinauto==0.6.9
comtypes==1.4.16
pywin32==312
psutil==7.2.2
Pillow==12.3.0
```

Installer une fois dans la session Windows de recette :

```powershell
python -m pip install -r tools\windows_ui_recipe\requirements.txt
```

## Garde-fous BDD

Le pilote refuse de lancer Noethys si :

- Windows n'est pas utilisé ;
- l'exécutable ne s'appelle pas `Noethys.exe` ;
- le profil n'a pas le marqueur `NOETHYS_UI_RECIPE_PROFILE=1` ;
- `Roaming\noethys\Config.json` est absent ;
- `nomFichier` ne désigne pas une base réseau/MySQL ;
- le host ne correspond pas à `--expected-db-host` ;
- le nom de base ne correspond pas à `--expected-db-name` ;
- le host ne résout pas vers la boucle locale (`localhost`, `127.0.0.1`, `::1`, etc.).

`APPDATA` et `LOCALAPPDATA` sont redirigés vers le profil jetable. Les actions génériques dont le libellé évoque suppression, envoi, facturation ou publication sont refusées.

Le helper `prepare_profile.ps1` copie uniquement un `Config.json` de recette déjà préparé. Il ne crée, ne migre et ne modifie aucune base.

## Préparation

```powershell
.\tools\windows_ui_recipe\prepare_profile.ps1 `
  -ProfileRoot "C:\Noethys-Recipe-Profile" `
  -RecipeConfig "C:\recette\Config.json"
```

## Exécution du prototype

```powershell
.\tools\windows_ui_recipe\run.ps1 `
  -Exe "C:\Noethys-Vanilla\Noethys.exe" `
  -ProfileRoot "C:\Noethys-Recipe-Profile" `
  -ExpectedDbHost "127.0.0.1" `
  -ExpectedDbName "NOETHYS_RECETTE" `
  -Repeat 5
```

La sortie standard du scénario contient uniquement un statut par étape exécutée :

- `PASS`
- `FAIL`
- `TIMEOUT`
- `CRASH`

Le détail est écrit dans `artifacts\noethys-ui\scenario.jsonl`.

## Scénario minimal

1. lancer `Noethys.exe` ;
2. attendre la fenêtre principale et vérifier sa réactivité ;
3. ouvrir `Affichage` ;
4. le fermer par `Echap` ;
5. ouvrir `Consommations > Liste d'attente` ;
6. fermer avec le bouton `Fermer` ;
7. ouvrir `Consommations > Liste détaillée des consommations` ;
8. fermer au premier instant où le dialogue devient réellement visible ;
9. rouvrir immédiatement ;
10. répéter fermeture/réouverture plusieurs fois ;
11. fermer par la vraie croix Windows ;
12. vérifier que `Noethys.exe` reste vivant et responsive.

### Limite de l'étape 8

`DLG_Liste_consommations.Dialog` effectue une partie de son chargement synchrone dans le constructeur, avant `ShowModal()`. Un vrai utilisateur ne peut donc pas cliquer pendant cette phase cachée. Le pilote ferme au premier instant où la fenêtre devient user-visible. Instrumenter avant cela ne serait plus une recette UI « comme un utilisateur ».

## Détection d'échec

Sur `FAIL`, `TIMEOUT` ou `CRASH`, le pilote enregistre autant que possible :

- scénario, étape, action, attendu, obtenu ;
- durée et horodatage ;
- titre de la fenêtre active ;
- état du processus ;
- screenshot multi-écrans ;
- traceback ;
- dumps UIA et Win32 ;
- corrélation best-effort du journal `Application` pour Event ID 1000, `Noethys.exe` et `0xc0000005`.

L'absence d'événement Windows n'est jamais interprétée comme preuve d'absence de bug.

La réactivité est contrôlée avec `IsHungAppWindow` et `SendMessageTimeout(WM_NULL)`.

## Contrôles et limites wxPython

Statistiquement favorables, mais à confirmer sur le vrai binaire Windows :

- fenêtre principale `wx.Frame` ;
- menus `wx.Menu` ;
- dialogues `wx.Dialog` ;
- boutons `CTRL_Bouton_image.CTRL`, car ils héritent de `wx.Button` ;
- `wx.Choice` ;
- certaines listes natives.

À qualifier en priorité car potentiellement moins bien exposés :

- `wx.lib.agw.aui.AuiNotebook` ;
- AUI/AGW toolbars et panes ;
- contrôles owner-drawn ;
- `FastObjectListView`/`wx.ListCtrl` virtuel ;
- `wx.BitmapButton` sans libellé textuel exploitable.

Le scénario produit des dumps d'accessibilité même sur certaines étapes réussies afin de documenter précisément les rôles UIA, `AutomationId`, classes Win32 et contrôles réellement exposés. Un dump n'est jamais converti automatiquement en preuve fonctionnelle.

## Croix Windows

L'étape de fermeture par croix cherche et clique le vrai bouton de `TitleBar` via UI Automation. Il n'existe volontairement **aucun fallback `WM_CLOSE`** pour cette étape : si la croix n'est pas accessible, le résultat doit être `FAIL`, pas un faux `PASS`.

## Session Windows / CI

Une vraie session Windows utilisateur, active et déverrouillée, est nécessaire pour rendre `click_input()` et les frappes clavier fiables. Éviter un bureau RDP déconnecté et aligner les niveaux d'élévation entre Noethys et le pilote.

Les runners GitHub Actions hébergés restent utiles pour construire le portable et les smokes processus, mais ne doivent pas servir de preuve de recette souris/clavier tant que l'environnement de bureau interactif n'est pas explicitement maîtrisé. Pour une CI UI fiable, utiliser de préférence un runner Windows self-hosted lancé dans une session utilisateur interactive, et non uniquement comme service en Session 0.
