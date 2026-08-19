# Noe-022 — Qualification macOS

## État

Le code source Noethys est qualifié automatiquement sur un runner macOS moderne avec Python 3.10 et wxPython Phoenix.

La CI vérifie désormais :

- la compilation des sources ;
- les imports non-GUI critiques ;
- la configuration UTF-8 et sa récupération ;
- la compatibilité `pyttsx3` ;
- la création/destruction de `wx.App` ;
- les API wxPython historiques réellement utilisées par le code first-party ;
- un layout wx représentatif avec fenêtre, sizers, contrôles texte, bouton et `UltimateListCtrl`.

Les études Python 3.11 et 3.12 ont également validé les smoke tests wxPython sur macOS.

## Ce que cette qualification permet d'affirmer

Le **code source** reste compatible avec wxPython Phoenix sur macOS pour les frontières techniques couvertes par la CI. Les changements de modernisation doivent conserver ce niveau de compatibilité.

## Limites

Cette qualification automatisée n'est **pas** une recette fonctionnelle complète de Noethys sur un Mac réel :

- aucun parcours métier complet n'est exécuté avec une base de production ;
- les périphériques et intégrations spécifiques ne sont pas tous testés ;
- aucun paquet applicatif macOS signé/notarisé n'est produit ;
- l'ergonomie de chaque dialogue n'est pas inspectée visuellement.

En conséquence, la documentation ne doit pas présenter macOS comme une distribution officiellement packagée au même niveau que le portable Windows. La formulation correcte est : **compatibilité du code source maintenue et testée automatiquement sur macOS**, sous réserve d'une recette fonctionnelle sur machine réelle avant toute promesse de support complet.
