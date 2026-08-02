# Audit CI Windows

Cette branche prépare un audit frugal de la compatibilité Windows de Noethys.

Objectifs :
- inventorier les workflows, versions Python et dépendances existants ;
- ajouter, uniquement si nécessaire, une validation Windows ciblée dans un workflow unique ;
- éviter toute duplication de contrôles Linux ;
- compiler le code Python, vérifier wxPython et exécuter les tests disponibles ;
- documenter les limites qui nécessitent encore une recette sur base réelle.

Aucune modification fonctionnelle de Noethys n'est prévue dans ce lot.
