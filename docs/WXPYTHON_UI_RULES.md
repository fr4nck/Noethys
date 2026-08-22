# Règles wxPython et harmonisation d’interface

Ce document conserve les règles de mise en œuvre et de débogage issues du chantier Upgrade Noethys. Elles complètent `DESIGN_SYSTEM_UI_UX.md` avec les contraintes propres à wxPython et à l’architecture historique de Noethys.

## 1. Principe directeur

Moderniser proprement, sans surcouche destinée à masquer les défauts historiques.

Une correction doit traiter la cause : ownership wxPython, sizer, métrique figée, ordre d’initialisation, thème ou logique de contrôle. Ne pas empiler des contournements visuels ou des exceptions locales qui déplacent le problème.

## 2. Parent visuel et contrôleur métier

Un objet passé comme `parent` à un contrôle wxPython doit être un parent visuel valide (`wx.Window` ou dérivé).

Ne pas confondre :

- le **parent visuel**, propriétaire du contrôle dans l’arbre wxWidgets ;
- le **contrôleur métier**, objet Python utilisé pour les callbacks ou la logique applicative.

Lorsqu’un composant a besoin des deux, les conserver séparément. Ne jamais utiliser un contrôleur non visuel comme parent wxPython uniquement parce qu’il porte les méthodes métier attendues.

## 3. Initialisation et fermeture des dialogues

Éviter les objets partiellement initialisés.

Règles :

- ne pas appeler `EndModal()` pendant `__init__` avant que le dialogue ne soit complètement construit ;
- ne pas fermer ou détruire le mauvais parent ;
- construire les contrôles, bindings et sizers avant les opérations différées qui les utilisent ;
- lorsqu’une fermeture anticipée est nécessaire, la différer proprement après initialisation complète ;
- conserver des tests ciblés pour les dialogues ayant déjà produit des fenêtres vides ou des freezes.

## 4. Sizers : corriger, ne pas supprimer les garde-fous

Les assertions wxWidgets sur les sizers signalent généralement une incohérence réelle.

Interdictions :

- ne pas utiliser `WXSUPPRESS_SIZER_FLAGS_CHECK` pour faire disparaître les assertions ;
- ne pas modifier le package wxPython système ou protégé pour contourner un défaut applicatif ;
- ne pas ajouter une couche de compatibilité globale destinée seulement à ignorer les erreurs de layout.

À faire :

- supprimer les flags invalides ou contradictoires ;
- utiliser le bon sizer pour la responsabilité de layout ;
- vérifier les parents, proportions, `EXPAND`, alignements, bordures et tailles minimales ;
- supprimer les structures historiques rigides lorsqu’elles sont précisément la cause du défaut ;
- préférer une structure claire et flexible à un empilement de `SetSize`, `SetPosition`, `SetMinSize` et corrections différées.

Pour un problème dépendant de wxPython lui-même, reproduire dans un environnement modifiable ou isolé plutôt que patcher une installation système protégée.

## 5. Échelle d’interface et métriques

Le réglage d’échelle doit fonctionner avec les vrais contenus, notamment à 120 % et 150 %, sans titres rongés ni panneaux surdimensionnés.

Règles :

- pas de hauteur historique figée lorsqu’un contenu peut dimensionner son conteneur ;
- l’ancien bandeau de hauteur fixe de 76 px ne doit pas redevenir un contrat d’interface ;
- ne pas tronquer artificiellement les titres par une coupe de chaîne du type `label[:25]` ;
- laisser le sizer calculer la place nécessaire aux textes et titres longs ;
- les métriques doivent provenir des tokens/métriques communes lorsque possible ;
- une police redimensionnée doit servir de base au calcul des dimensions associées : ne pas redimensionner le conteneur à partir de la police historique ;
- les textes de pied de fenêtre et autres textes secondaires doivent suivre la même logique d’échelle ;
- une régression vers les anciennes métriques rigides doit pouvoir être détectée par des tests de contrat ciblés.

## 6. Thème sombre et contrôles natifs

Le moteur de thème doit respecter les exceptions métier et les particularités des contrôles natifs.

Règles conservées :

- préserver les couleurs historiques qui portent réellement un état métier, notamment certaines lignes de statut ;
- lorsqu’un contrôle conserve explicitement un fond clair en mode sombre, adapter le texte pour qu’il reste lisible au lieu d’imposer mécaniquement une couleur de texte sombre/thème ;
- traiter les contrôles spécialisés avant les règles génériques lorsqu’ils pourraient être capturés par celles-ci ; en particulier, appliquer les règles `Choicebook` avant les règles génériques de type `Choice` ;
- éviter les grandes zones blanches résiduelles, mais ne pas casser un contrôle natif uniquement pour obtenir une uniformité décorative.

## 7. Menus et identifiants

Les libellés affichés et les identifiants réels doivent rester cohérents avec la traduction et la plateforme.

Lorsqu’une action de menu est résolue par libellé, utiliser le libellé traduit correspondant à l’ID réellement créé. Ne pas rechercher un texte historique codé en dur qui peut diverger de la traduction ou de l’ID du menu courant.

## 8. Composants communs avant retouches locales

Le chantier Repens/UI a confirmé que les corrections centrales sont préférables aux retouches écran par écran.

Priorités :

1. tokens et métriques communes ;
2. contrôles de listes/tableaux ;
3. champs et boutons ;
4. navigation et barres d’outils ;
5. dialogues et composants métier partagés ;
6. écrans particuliers.

Les composants déjà migrés doivent hériter des sections, espacements, tailles et actions communes plutôt que recréer une variante locale.

## 9. Anti-patterns constatés dans les anciens écrans

Plusieurs dialogues historiques, notamment la liste des familles, ont présenté la même famille de défauts :

- couleurs codées en dur (`#ECE9D8`, `#FFFFFF`, `#000000`, `#C0C0C0`, etc.) ;
- tailles de police répétées en dur ;
- contrôles proches visuellement mais configurés différemment ;
- `FlexGridSizer` imbriqués de façon rigide ;
- mélange de `SetSize`, `SetMinSize`, `SetPosition` et sizers ;
- `wx.CallAfter` utilisé pour corriger a posteriori des problèmes de sélection/layout ;
- logique métier et logique d’interface regroupées dans les mêmes handlers ;
- boutons et icônes sans métriques communes.

La modernisation consiste à retirer ces décisions locales, pas à les recouvrir.

## 10. Performance : distinguer technique et perceptif

Une interface qui paraît instantanée n’est pas nécessairement la plus ergonomique. À l’inverse, une animation ou transition agréable ne doit jamais masquer un traitement bloquant.

Règles :

- distinguer la rapidité technique du confort perceptif ;
- une transition visuelle peut être légèrement retardée ou amortie si elle améliore la compréhension ;
- aucune transition ne doit ralentir un traitement réseau ou métier ;
- pour diagnostiquer un freeze, instrumenter l’événement avant dispatch et mesurer le temps réellement passé ;
- conserver/loguer les actions dépassant 15 secondes pendant les investigations de performance ;
- distinguer explicitement délai d’affichage/widget, blocage de la boucle UI et latence MySQL distante.

## 11. Tests wxPython ciblés

Pour toute correction de layout ou de parentage importante :

- compiler/importer le module concerné ;
- créer et détruire un `wx.App(False)` dans le smoke test approprié ;
- lorsque possible, créer puis détruire le contrôle ou dialogue fautif ;
- exécuter le test sur Windows dès qu’un comportement wxWidgets/GUI est concerné ;
- conserver Linux/macOS comme garde-fous de portabilité lorsque le composant est multiplateforme ;
- ne pas considérer une CI verte comme une validation visuelle complète.

## 12. Règle de validation d’une correction UI

Une correction est considérée propre lorsque :

- la cause historique a été supprimée ou isolée ;
- aucun garde-fou wxWidgets n’a été désactivé ;
- le comportement métier est inchangé ;
- le rendu reste lisible en clair et sombre ;
- l’échelle 100/120/150 % ne réintroduit pas de troncature ou d’espace artificiel ;
- le composant réutilise les métriques/tokens communs lorsqu’ils existent ;
- les configurations historiques restent exploitables.
